"""
train.py

Kubeflow Pipeline component — Phase 2.

Trains an Isolation Forest model on the preprocessed feature matrix
and saves the model artifact to GCS via MLflow.

Learning goals:
- KFP v2 Input[Dataset] / Output[Model] artifact passing
- Why Isolation Forest for anomaly detection (unsupervised, no labels needed)
- MLflow model logging from inside a KFP component
"""

from kfp import dsl
from kfp.dsl import Input, Output, Dataset, Model


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "scikit-learn>=1.4,<2.0",
        "pandas>=2.0,<3.0",
        "mlflow>=2.10,<3.0",
        "boto3>=1.34",  # WHY: mlflow uses boto3 for GCS/S3-compatible artifact stores
    ],
)
def train(
    input_features: Input[Dataset],
    mlflow_tracking_uri: str,
    contamination: float,
    output_model: Output[Model],
) -> None:
    """
    Train an Isolation Forest on the feature matrix produced by preprocess.

    WHY Isolation Forest:
    - Unsupervised: we don't have labelled anomaly data for stock prices
    - Efficient on tabular data: O(n log n), fast on 360-row datasets
    - contamination param: expected fraction of anomalies in the data.
      0.05 means we expect ~5% of trading days to be anomalous.
      This is a hyperparameter to tune — start with 0.05 and observe results.

    WHY MLflow:
    - Tracks hyperparameters and metrics alongside the model artifact
    - Makes it easy to compare runs and roll back to a previous model version
    - The tracking URI points to a local MLflow server (Phase 2) or
      a managed MLflow instance (Phase 3 on GKE)
    """
    import pandas as pd
    import mlflow
    import mlflow.sklearn
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import pickle

    # Load features produced by the preprocess component
    df = pd.read_csv(input_features.path)
    print(f"Training on {len(df)} rows")

    feature_cols = ["daily_return", "volatility_5d", "volume_ratio", "price_range_pct"]
    X = df[feature_cols].values

    # WHY: StandardScaler ensures all features contribute equally to the
    # Isolation Forest's random splits. Without scaling, volume_ratio
    # (which can be >10) would dominate daily_return (typically <0.05).
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("finsight-anomaly-detection")

    with mlflow.start_run():
        mlflow.log_param("contamination", contamination)
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("feature_cols", feature_cols)
        mlflow.log_param("n_samples", len(df))

        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,  # WHY: fixed seed for reproducible runs
        )
        model.fit(X_scaled)

        # Score: -1 = anomaly, 1 = normal (sklearn convention)
        scores = model.decision_function(X_scaled)
        n_anomalies = (model.predict(X_scaled) == -1).sum()

        mlflow.log_metric("n_anomalies_detected", int(n_anomalies))
        mlflow.log_metric("anomaly_rate", float(n_anomalies / len(df)))
        mlflow.sklearn.log_model(model, artifact_path="isolation_forest")

        print(f"Detected {n_anomalies} anomalies ({n_anomalies/len(df)*100:.1f}%)")

    # WHY: We save both model and scaler together — the scaler must be applied
    # at inference time with the same parameters used during training.
    artifact = {"model": model, "scaler": scaler, "feature_cols": feature_cols}
    with open(output_model.path, "wb") as f:
        pickle.dump(artifact, f)

    print(f"Model artifact written to {output_model.path}")
