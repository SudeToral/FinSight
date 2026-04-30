"""
preprocess.py

Kubeflow Pipeline component — Phase 2.

Reads raw OHLCV data from BigQuery, cleans it, and outputs a feature
matrix ready for Isolation Forest training.

Learning goals:
- KFP v2 @component decorator and typed I/O
- How artifacts carry data between pipeline steps
- Why preprocessing is a separate component (reproducibility, caching)
"""

from kfp import dsl
from kfp.dsl import Output, Dataset


@dsl.component(
    # WHY: base_image pins the Python version so the component runs identically
    # on your laptop, in k3d, and later on GKE Autopilot. Never rely on the
    # default image — it may not have the packages you need.
    base_image="python:3.11-slim",
    packages_to_install=[
        "google-cloud-bigquery>=3.0,<4.0",
        "pandas>=2.0,<3.0",
        "pyarrow>=14.0",  # WHY: BigQuery client uses pyarrow for data transfer
        "db-dtypes",      # WHY: Required for to_dataframe() method
    ],
)
def preprocess(
    gcp_project: str,
    dataset: str,
    table: str,
    output_features: Output[Dataset],
) -> None:
    """
    Pull stock price data from BigQuery and engineer features for anomaly detection.

    WHY these features:
    - daily_return: percentage price change — the primary signal for anomalies
    - volatility_5d: rolling 5-day std of returns — captures unusual volatility bursts
    - volume_ratio: today's volume vs 5-day average — volume spikes often precede anomalies
    - price_range_pct: (high-low)/close — intraday range as a fraction of price

    These four features are scale-invariant (percentages/ratios), which matters
    because Isolation Forest is sensitive to feature scale differences.
    """
    import pandas as pd
    from google.cloud import bigquery

    client = bigquery.Client(project=gcp_project)

    query = f"""
        SELECT symbol, date, open, high, low, close, volume
        FROM `{gcp_project}.{dataset}.{table}`
        ORDER BY symbol, date
    """

    print(f"Fetching data from {gcp_project}.{dataset}.{table}...")
    df = client.query(query).to_dataframe()
    print(f"Loaded {len(df)} rows, {df['symbol'].nunique()} symbols")

    features_list = []

    for symbol, group in df.groupby("symbol"):
        g = group.sort_values("date").copy()

        # WHY: pct_change() computes (current - previous) / previous
        # fill_value=0 for the first row avoids NaN propagation
        g["daily_return"] = g["close"].pct_change().fillna(0)

        # WHY: min_periods=1 prevents NaN in the first 4 rows of each symbol
        g["volatility_5d"] = g["daily_return"].rolling(5, min_periods=1).std().fillna(0)

        volume_ma5 = g["volume"].rolling(5, min_periods=1).mean()
        # WHY: clip at 0.01 avoids division by zero if volume_ma5 rounds to 0
        g["volume_ratio"] = g["volume"] / volume_ma5.clip(lower=0.01)

        g["price_range_pct"] = (g["high"] - g["low"]) / g["close"].clip(lower=0.01)

        features_list.append(g[[
            "symbol", "date",
            "daily_return", "volatility_5d", "volume_ratio", "price_range_pct",
        ]])

    features_df = pd.concat(features_list, ignore_index=True)
    print(f"Feature matrix shape: {features_df.shape}")

    # WHY: We write to output_features.path — KFP manages this path and passes
    # it to downstream components automatically via artifact lineage.
    features_df.to_csv(output_features.path, index=False)
    print(f"Features written to {output_features.path}")
