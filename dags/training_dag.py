"""
training_dag.py

Weekly pipeline that compiles and submits the Kubeflow Pipelines v2
finsight_pipeline to a KFP backend, then waits for completion.

Learning goals (Phase 2):
- How Airflow orchestrates external ML systems (KFP) via its Python client
- XCom: run_id flows from trigger task to wait task to log task
- Polling pattern for long-running external jobs
- Why orchestration (Airflow) and ML execution (Kubeflow) are kept separate
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from google.cloud import bigquery

log = logging.getLogger(__name__)

DATASET = "finsight"
TABLE = "stock_prices"
SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN"]

# WHY 20 rows minimum: Isolation Forest needs enough samples to learn a normal
# baseline. With daily data and weekends/holidays removed, 20 rows ≈ one month.
MIN_ROWS_PER_SYMBOL = 20

POLL_INTERVAL_SECONDS = 30

# WHY 30 min timeout: Isolation Forest on 90 days × 4 symbols is fast (< 5 min),
# but Kubernetes pod scheduling and GCS artifact uploads add overhead.
PIPELINE_TIMEOUT_SECONDS = 30 * 60


@dag(
    dag_id="training_dag",
    schedule="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    },
    tags=["phase2", "training", "kubeflow"],
)
def training_dag():
    """
    Weekly ML training pipeline.

    check_data_freshness → trigger_kubeflow_pipeline → wait_for_pipeline → log_results
    """

    @task()
    def check_data_freshness() -> dict:
        """
        Verify BigQuery has enough rows per symbol before spending compute on training.

        WHY this guard exists: if ingest_dag failed for several days the training
        pipeline would run on sparse data and produce a low-quality model. Failing
        fast here is cheaper than discovering the problem inside evaluate.py after
        20 minutes of preprocessing.

        Returns:
            Dict mapping symbol → row_count (stored in XCom for UI visibility).
        """
        gcp_project = Variable.get("gcp_project")
        client = bigquery.Client(project=gcp_project)

        query = f"""
            SELECT symbol, COUNT(*) AS row_count
            FROM `{gcp_project}.{DATASET}.{TABLE}`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY symbol
        """

        result = client.query(query).result()
        counts = {row.symbol: row.row_count for row in result}
        log.info("Row counts (last 90 days): %s", counts)

        missing = [s for s in SYMBOLS if s not in counts]
        insufficient = [s for s, n in counts.items() if n < MIN_ROWS_PER_SYMBOL]

        if missing:
            raise AirflowException(
                f"Symbols missing from BigQuery: {missing}. Run ingest_dag first."
            )
        if insufficient:
            raise AirflowException(
                f"Insufficient rows for {insufficient}. "
                f"Need >= {MIN_ROWS_PER_SYMBOL} rows per symbol."
            )

        log.info("Data freshness check passed.")
        return counts

    @task()
    def trigger_kubeflow_pipeline(row_counts: dict) -> str:
        """
        Compile the finsight KFP pipeline and submit a run to the KFP backend.

        WHY compile inside the task: the pipeline definition lives in
        kubeflow/pipeline.py which is mounted into the Airflow container.
        Compiling at trigger time means code changes to the pipeline are picked
        up on the next DAG run without restarting Airflow.

        WHY enable_caching=False: we always want a fresh training run with the
        latest BigQuery data, not a cached result from a previous week's run.

        Args:
            row_counts: passed from check_data_freshness to make the dependency
                        explicit in the Airflow task graph.

        Returns:
            KFP run ID (str) — passed downstream via XCom.
        """
        import sys
        import tempfile

        # WHY: /opt/airflow is where docker-compose mounts the project root inside
        # the Airflow container, so kubeflow/pipeline.py is importable from there.
        sys.path.insert(0, "/opt/airflow")

        from kfp import compiler
        from kfp.client import Client
        from kubeflow.pipeline import finsight_pipeline

        gcp_project = Variable.get("gcp_project")

        # WHY kfp_host as an Airflow Variable: the host changes between local k3d
        # (port-forward on 8888) and GKE Autopilot (internal service URL).
        # Storing it in Variables means no code change is needed to switch envs.
        kfp_host = Variable.get("kfp_host", default_var="http://localhost:8888")
        mlflow_uri = Variable.get("mlflow_tracking_uri", default_var="http://mlflow:5000")

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            pipeline_yaml = f.name

        log.info("Compiling pipeline to %s", pipeline_yaml)
        compiler.Compiler().compile(
            pipeline_func=finsight_pipeline,
            package_path=pipeline_yaml,
        )

        log.info("Connecting to KFP backend at %s", kfp_host)
        kfp_client = Client(host=kfp_host)

        run = kfp_client.create_run_from_pipeline_package(
            pipeline_file=pipeline_yaml,
            arguments={
                "gcp_project": gcp_project,
                "mlflow_tracking_uri": mlflow_uri,
            },
            run_name=f"finsight-training-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            enable_caching=False,
        )

        log.info("Pipeline submitted — run_id: %s", run.run_id)
        return run.run_id

    @task()
    def wait_for_pipeline(run_id: str) -> str:
        """
        Poll the KFP backend until the pipeline run finishes or times out.

        WHY polling instead of a Sensor: a KFP sensor would require a custom
        Airflow provider. Simple polling in a task is sufficient for a weekly
        batch job where a 30-second check interval has no meaningful cost.

        Args:
            run_id: KFP run ID from trigger_kubeflow_pipeline (via XCom).

        Returns:
            Final run status string (e.g. "SUCCEEDED", "FAILED").
        """
        from kfp.client import Client

        kfp_host = Variable.get("kfp_host", default_var="http://localhost:8888")
        kfp_client = Client(host=kfp_host)

        terminal_states = {"SUCCEEDED", "FAILED", "CANCELLED", "SKIPPED"}
        elapsed = 0

        while elapsed < PIPELINE_TIMEOUT_SECONDS:
            run_response = kfp_client.get_run(run_id=run_id)
            status = run_response.state

            log.info("Run %s → %s (elapsed: %ds)", run_id, status, elapsed)

            if status in terminal_states:
                return status

            time.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS

        raise AirflowException(
            f"Pipeline run {run_id} did not complete within "
            f"{PIPELINE_TIMEOUT_SECONDS}s. Check the KFP UI."
        )

    @task()
    def log_results(status: str, run_id: str) -> None:
        """
        Raise an Airflow failure if the pipeline did not succeed.

        WHY a separate task: separating result handling from polling means the
        Airflow UI shows a distinct red cell for "log_results" vs "wait_for_pipeline",
        making it easy to tell whether the failure was a KFP job failure or a
        polling/connectivity issue.
        """
        kfp_host = Variable.get("kfp_host", default_var="http://localhost:8888")
        pipeline_url = f"{kfp_host}/#/runs/details/{run_id}"

        if status == "SUCCEEDED":
            log.info("Training pipeline completed successfully. Details: %s", pipeline_url)
        else:
            raise AirflowException(
                f"Pipeline run {run_id} finished with status '{status}'. "
                f"Inspect in KFP UI: {pipeline_url}"
            )

    # WHY: TaskFlow API infers the dependency graph from how return values are passed.
    # row_counts → trigger: freshness check must pass before wasting compute.
    # run_id → wait → log: poll the exact run we submitted, then report its outcome.
    row_counts = check_data_freshness()
    run_id = trigger_kubeflow_pipeline(row_counts)
    status = wait_for_pipeline(run_id)
    log_results(status, run_id)


training_dag()
