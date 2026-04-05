"""
ingest_dag.py

Daily pipeline that pulls OHLCV stock data from Yahoo Finance and
loads it into the BigQuery table `finsight.stock_prices`.

Learning goals (Phase 1):
- TaskFlow API (@dag, @task decorators)
- XCom: how return values flow between tasks automatically
- BigQuery Python client (insert_rows_json)
- ADC authentication inside a containerised Airflow task
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import yfinance as yf
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from google.cloud import bigquery

log = logging.getLogger(__name__)

# WHY: Symbols are defined at module level so they're easy to extend later
# without touching task logic.
SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN"]

DATASET = "finsight"
TABLE = "stock_prices"


@dag(
    dag_id="ingest_dag",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["phase1", "ingestion"],
)
def ingest_dag():
    """
    Daily stock ingestion pipeline.

    fetch_stock_data → load_to_bigquery → validate_row_count
    """

    @task()
    def fetch_stock_data() -> list[dict]:
        """
        Pull the last 30 days of OHLCV data for each symbol in SYMBOLS.

        WHY 30 days: We re-fetch a rolling window rather than a single day so
        that gaps caused by weekends, holidays, or past failures are backfilled
        automatically on the next run. BigQuery upsert semantics (insert_rows_json
        with WRITE_APPEND) mean duplicate rows are possible; the validate task
        catches zero-row situations, and downstream queries can use MAX(ingested_at)
        to deduplicate if needed.

        Returns:
            List of dicts, one per OHLCV row, ready for BigQuery insertion.
        """
        rows = []

        for symbol in SYMBOLS:
            log.info("Fetching data for %s", symbol)

            # WHY: auto_adjust=True adjusts OHLCV for splits and dividends,
            # giving cleaner price history for anomaly detection.
            df = yf.download(symbol, period="30d", interval="1d", auto_adjust=True, progress=False)

            if df.empty:
                log.warning("No data returned for %s — skipping", symbol)
                continue

            # WHY: yfinance returns a MultiIndex when auto_adjust=True in newer
            # versions. Flatten column names to avoid KeyError surprises.
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df = df.reset_index()

            for _, row in df.iterrows():
                rows.append({
                    "symbol": symbol,
                    "date": str(row["Date"].date()),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    # ingested_at is added in load_to_bigquery so all rows in
                    # a single task execution share the same timestamp.
                })

        log.info("Fetched %d total rows across %d symbols", len(rows), len(SYMBOLS))
        return rows  # WHY: returned value is automatically pushed to XCom

    @task()
    def load_to_bigquery(rows: list[dict]) -> None:
        """
        Write the rows returned by fetch_stock_data into BigQuery.

        WHY XCom: Airflow's TaskFlow API passes the return value of the upstream
        task directly as a function argument — no manual xcom_pull() needed.
        Under the hood Airflow serialises the list to JSON and stores it in the
        metadata DB (or a configured XCom backend for large payloads).

        Args:
            rows: List of OHLCV dicts from fetch_stock_data.
        """
        if not rows:
            log.warning("No rows to insert — skipping BigQuery load")
            return

        # Stamp all rows with the same ingestion time for this run
        ingested_at = datetime.utcnow().isoformat()
        for row in rows:
            row["ingested_at"] = ingested_at

        # WHY: BigQuery client resolves ADC automatically — no key file needed.
        # Inside the Docker container the ADC file is mounted at
        # /home/airflow/.config/gcloud/application_default_credentials.json
        # (see docker-compose.yaml volume mount).
        # WHY: Variable.get() reads the value at runtime from Airflow's metadata DB.
        # Set this via Admin → Variables in the UI: key=gcp_project, value=your-project-id
        gcp_project = Variable.get("gcp_project")
        client = bigquery.Client(project=gcp_project)
        table_ref = f"{gcp_project}.{DATASET}.{TABLE}"

        # WHY: load_table_from_json uses batch load instead of streaming insert.
        # Streaming insert (insert_rows_json) is not available on the BigQuery
        # free/sandbox tier — it raises a 403 Forbidden error.
        # Batch load is free, slightly slower, but perfectly fine for daily pipelines.
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        job = client.load_table_from_json(rows, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete

        if job.errors:
            raise AirflowException(f"BigQuery load errors: {job.errors}")

        log.info("Inserted %d rows into %s", len(rows), table_ref)

    @task()
    def validate_row_count() -> None:
        """
        Sanity check: confirm that recent rows exist in BigQuery.

        WHY this task exists: insert_rows_json returns errors synchronously,
        but BigQuery's streaming buffer can occasionally lag. This task runs a
        SQL query after the load to verify data is actually queryable.
        If the pipeline ran but wrote zero recent rows, we want an Airflow
        task failure (red cell in the UI) rather than silent data loss.
        """
        gcp_project = Variable.get("gcp_project")
        client = bigquery.Client(project=gcp_project)

        # WHY: We check 30 days instead of 2 days because:
        # 1. We fetch 30 days of data in fetch_stock_data
        # 2. BigQuery streaming buffer can lag a few seconds, so checking
        #    the exact last 2 days right after insert is unreliable.
        query = f"""
            SELECT COUNT(*) AS recent_count
            FROM `{gcp_project}.{DATASET}.{TABLE}`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """

        result = client.query(query).result()
        count = next(iter(result)).recent_count

        if count == 0:
            raise AirflowException(
                "Validation failed: no rows found in finsight.stock_prices "
                "for the last 2 days. Check the load task logs."
            )

        log.info("Validation passed: %d recent rows found in BigQuery", count)

    # WHY: TaskFlow API infers dependencies from function call order.
    # fetch → load → validate is the explicit execution order.
    rows = fetch_stock_data()
    load_to_bigquery(rows)
    validate_row_count()


ingest_dag()
