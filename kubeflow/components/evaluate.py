"""
evaluate.py

Kubeflow Pipeline component — Phase 2.

Loads the trained model, scores all data points, and writes the
anomaly results back to BigQuery for downstream dashboarding.

Learning goals:
- KFP v2 Input[Model] artifact consumption
- Writing evaluation results back to BigQuery (batch load, free tier)
- Why evaluation is a separate component (can be re-run independently)
"""

from kfp import dsl
from kfp.dsl import Input, Output, Dataset, Model


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "scikit-learn>=1.4,<2.0",
        "pandas>=2.0,<3.0",
        "google-cloud-bigquery>=3.0,<4.0",
        "pyarrow>=14.0",
    ],
)
def evaluate(
    input_features: Input[Dataset],
    input_model: Input[Model],
    gcp_project: str,
    output_anomalies: Output[Dataset],
) -> None:
    """
    Score each trading day with the trained Isolation Forest and surface anomalies.

    WHY a separate evaluate component:
    - Decouples scoring from training — we can rescore historical data with a
      new model without re-running the full pipeline
    - KFP caches component outputs: if features didn't change, preprocess and
      train are skipped and evaluate runs against the cached model

    Output schema written to BigQuery (finsight.anomalies):
        symbol       STRING
        date         DATE
        score        FLOAT64   (higher = more normal, lower = more anomalous)
        is_anomaly   BOOL
        daily_return FLOAT64
    """
    import pickle
    import pandas as pd
    from google.cloud import bigquery

    # Load features
    df = pd.read_csv(input_features.path)

    # Load model + scaler bundle saved by the train component
    with open(input_model.path, "rb") as f:
        artifact = pickle.load(f)

    model = artifact["model"]
    scaler = artifact["scaler"]
    feature_cols = artifact["feature_cols"]

    X = df[feature_cols].values
    X_scaled = scaler.transform(X)  # WHY: transform (not fit_transform) — use training scaler params

    df["score"] = model.decision_function(X_scaled)
    df["is_anomaly"] = model.predict(X_scaled) == -1

    anomaly_count = df["is_anomaly"].sum()
    print(f"Scored {len(df)} rows — {anomaly_count} anomalies detected")
    print(df[df["is_anomaly"]][["symbol", "date", "score", "daily_return"]].to_string())

    # Write anomaly results to KFP output artifact
    df.to_csv(output_anomalies.path, index=False)

    # WHY: Also write to BigQuery so Grafana can query anomalies directly.
    # We use load_table_from_json (batch) — free tier compatible.
    client = bigquery.Client(project=gcp_project)
    table_ref = f"{gcp_project}.finsight.anomalies"

    rows = df[["symbol", "date", "score", "is_anomaly", "daily_return"]].copy()
    rows["date"] = rows["date"].astype(str)
    rows["score"] = rows["score"].astype(float)
    rows["is_anomaly"] = rows["is_anomaly"].astype(bool)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        # WHY: WRITE_TRUNCATE replaces the anomalies table on each run.
        # Anomaly labels are model outputs, not raw data — recomputing them
        # from scratch each time is safer than appending stale results.
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
    )

    job = client.load_table_from_json(rows.to_dict("records"), table_ref, job_config=job_config)
    job.result()

    print(f"Anomaly results written to {table_ref}")
