"""
pipeline.py

Kubeflow Pipeline v2 — FinSight anomaly detection pipeline.

Compiles the three components (preprocess → train → evaluate) into a
single KFP pipeline YAML that can be submitted to any KFP-compatible
backend (local runner, GKE Autopilot, Vertex AI Pipelines).

Learning goals:
- How @dsl.pipeline connects components via artifact references
- Pipeline compilation: Python → YAML (the spec KFP submits to Kubernetes)
- How to run the pipeline locally for testing without a cluster

Usage:
    # Run locally (no Kubernetes needed)
    python kubeflow/pipeline.py --local --gcp-project YOUR_PROJECT_ID

    # Compile to YAML only
    python kubeflow/pipeline.py --compile
"""

import argparse
import sys
import os
import kfp
from kfp import dsl
from kfp import compiler
from kfp import local

# WHY: Add kubeflow/ to sys.path so relative imports work when running
# pipeline.py directly from the project root.
sys.path.insert(0, os.path.dirname(__file__))

from components.preprocess import preprocess
from components.train import train
from components.evaluate import evaluate

# WHY: Pipeline-level defaults are defined here so they can be overridden
# at submission time without editing the pipeline code.
DEFAULT_GCP_PROJECT = "finsight-492407"
DEFAULT_MLFLOW_URI = "http://mlflow:5000"
DEFAULT_CONTAMINATION = 0.05
OUTPUT_YAML = "kubeflow/finsight_pipeline.yaml"


@dsl.pipeline(
    name="finsight-anomaly-detection",
    description="Daily stock price anomaly detection using Isolation Forest",
)
def finsight_pipeline(
    gcp_project: str = DEFAULT_GCP_PROJECT,
    bq_dataset: str = "finsight",
    bq_table: str = "stock_prices",
    mlflow_tracking_uri: str = DEFAULT_MLFLOW_URI,
    contamination: float = DEFAULT_CONTAMINATION,
):
    """
    End-to-end anomaly detection pipeline.

    WHY this order:
    1. preprocess: raw data → clean feature matrix (CPU-only, fast)
    2. train: features → fitted model (CPU-only for Isolation Forest)
    3. evaluate: model + features → scored anomalies + BigQuery write

    KFP infers the dependency graph from artifact connections:
    - train receives preprocess's output_features → train runs after preprocess
    - evaluate receives train's output_model → evaluate runs after train
    No explicit ordering code needed.
    """

    preprocess_task = preprocess(
        gcp_project=gcp_project,
        dataset=bq_dataset,
        table=bq_table,
    )

    train_task = train(
        input_features=preprocess_task.outputs["output_features"],
        mlflow_tracking_uri=mlflow_tracking_uri,
        contamination=contamination,
    )

    evaluate_task = evaluate(  # noqa: F841
        input_features=preprocess_task.outputs["output_features"],
        input_model=train_task.outputs["output_model"],
        gcp_project=gcp_project,
    )


def main():
    parser = argparse.ArgumentParser(description="Run or compile the FinSight KFP pipeline")
    parser.add_argument("--local", action="store_true", help="Run locally without Kubernetes")
    parser.add_argument("--compile", action="store_true", help="Compile pipeline to YAML only")
    parser.add_argument("--gcp-project", default=DEFAULT_GCP_PROJECT)
    parser.add_argument("--contamination", type=float, default=DEFAULT_CONTAMINATION)
    args = parser.parse_args()

    if args.local:
        # WHY: local.init() tells KFP to run each component as a subprocess
        # on your machine instead of a Kubernetes pod. Same component code,
        # same artifact passing — just no cluster needed. Perfect for development.
        local.init(runner=local.SubprocessRunner())

        print("Running pipeline locally...")
        finsight_pipeline(
            gcp_project=args.gcp_project,
            contamination=args.contamination,
        )
        print("Local pipeline run complete.")

    elif args.compile:
        # WHY: Compiling validates the pipeline graph and produces a YAML
        # spec that can be submitted to any KFP-compatible backend later.
        print(f"Compiling pipeline to {OUTPUT_YAML}...")
        compiler.Compiler().compile(
            pipeline_func=finsight_pipeline,
            package_path=OUTPUT_YAML,
        )
        print(f"Compiled successfully → {OUTPUT_YAML}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
