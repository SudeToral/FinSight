"""
init_bigquery.py

Bootstrap script — creates the BigQuery dataset and table for FinSight.
Run this once before starting the Airflow pipeline.

Usage:
    python scripts/init_bigquery.py --project YOUR_GCP_PROJECT_ID
"""

import argparse
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

# WHY: We use Application Default Credentials (ADC) instead of a service account
# key file. ADC automatically picks up credentials from:
#   1. GOOGLE_APPLICATION_CREDENTIALS env var (if set)
#   2. gcloud auth application-default login (local dev)
#   3. Attached service account (when running on GCE/GKE/Cloud Run)
# This means zero secrets in the repo and zero key rotation headaches.


DATASET_ID = "finsight"
TABLE_ID = "stock_prices"

# Schema mirrors the financial OHLCV (Open/High/Low/Close/Volume) format.
# ingested_at lets us track data freshness and debug late-arriving rows.
SCHEMA = [
    bigquery.SchemaField("symbol",      "STRING",    description="Ticker symbol e.g. AAPL"),
    bigquery.SchemaField("date",        "DATE",      description="Trading date"),
    bigquery.SchemaField("open",        "FLOAT64",   description="Opening price"),
    bigquery.SchemaField("high",        "FLOAT64",   description="Intraday high"),
    bigquery.SchemaField("low",         "FLOAT64",   description="Intraday low"),
    bigquery.SchemaField("close",       "FLOAT64",   description="Closing price"),
    bigquery.SchemaField("volume",      "INT64",     description="Number of shares traded"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP", description="UTC timestamp when row was written"),
]


def create_dataset(client: bigquery.Client, project: str) -> bigquery.Dataset:
    dataset_ref = bigquery.Dataset(f"{project}.{DATASET_ID}")
    dataset_ref.location = "US"

    try:
        dataset = client.create_dataset(dataset_ref)
        print(f"[OK] Created dataset: {project}.{DATASET_ID}")
    except Conflict:
        # WHY: Conflict means the dataset already exists — safe to continue.
        dataset = client.get_dataset(dataset_ref)
        print(f"[OK] Dataset already exists: {project}.{DATASET_ID}")

    return dataset


def create_table(client: bigquery.Client, project: str) -> bigquery.Table:
    table_ref = f"{project}.{DATASET_ID}.{TABLE_ID}"
    table = bigquery.Table(table_ref, schema=SCHEMA)

    # WHY: Partition by date so queries that filter on a date range only scan
    # the relevant partitions — keeps costs low on the free sandbox tier.
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date",
    )

    try:
        table = client.create_table(table)
        print(f"[OK] Created table: {table_ref}")
    except Conflict:
        print(f"[OK] Table already exists: {table_ref}")

    return table


def main():
    parser = argparse.ArgumentParser(description="Initialize BigQuery resources for FinSight")
    parser.add_argument("--project", required=True, help="GCP project ID")
    args = parser.parse_args()

    # WHY: No credentials argument — BigQuery client resolves ADC automatically.
    client = bigquery.Client(project=args.project)

    print(f"\nInitializing BigQuery resources in project: {args.project}")
    print("-" * 50)

    create_dataset(client, args.project)
    create_table(client, args.project)

    print("-" * 50)
    print("Done. BigQuery is ready for FinSight ingestion.\n")


if __name__ == "__main__":
    main()
