# FinSight

End-to-end MLOps pipeline for stock price anomaly detection.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Apache Airflow                        │
│                                                              │
│  ingest_dag:                                                 │
│  fetch_stock_data → load_to_bigquery → validate_row_count   │
└──────────────────────────┬──────────────────────────────────┘
                           │ OHLCV rows
                           ▼
                  ┌─────────────────┐
                  │   BigQuery      │
                  │ finsight.       │
                  │ stock_prices    │
                  └────────┬────────┘
                           │ features
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubeflow Pipelines v2          (Phase 2)  │
│                                                              │
│  preprocess → train (Isolation Forest) → evaluate           │
└──────────────────────────┬──────────────────────────────────┘
                           │ model artifact
                           ▼
                  ┌─────────────────┐
                  │  GCS + MLflow   │
                  │  Model Registry │
                  └────────┬────────┘
                           │ served model
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           KServe + Prometheus + Grafana          (Phase 3)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- Docker + Docker Compose
- [k3d](https://k3d.io/) (Phase 2)
- Python 3.11

---

## Setup

### 1. Authenticate with GCP (ADC)

```bash
gcloud auth application-default login
```

### 2. Initialize BigQuery

```bash
pip install google-cloud-bigquery
python scripts/init_bigquery.py --project YOUR_GCP_PROJECT_ID
```

### 3. Initialize Airflow database

```bash
docker compose up airflow-init
```

### 4. Start Airflow

```bash
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080) — login: `admin` / `admin`

### 5. Trigger the ingestion DAG

In the Airflow UI, find `ingest_dag` and click **Trigger DAG**.

---

## What you'll learn

**Phase 1 — Data layer + Airflow**
BigQuery Python client, Airflow TaskFlow API (`@dag`, `@task`), XCom for inter-task data passing, Google provider operators, ADC authentication.

**Phase 2 — Kubeflow Pipelines**
KFP SDK v2 component authoring, pipeline compilation, artifact lineage, local k3d cluster setup, model training with scikit-learn Isolation Forest.

**Phase 3 — Serving + Observability**
KServe inference endpoints, Prometheus metrics scraping, Grafana dashboard setup, GKE Autopilot deployment.

---

## Project structure

```
finsight/
├── dags/
│   ├── ingest_dag.py       # Daily OHLCV ingestion to BigQuery
│   └── training_dag.py     # Triggers Kubeflow training pipeline (Phase 2)
├── kubeflow/
│   ├── components/
│   │   ├── preprocess.py
│   │   ├── train.py
│   │   └── evaluate.py
│   └── pipeline.py
├── scripts/
│   └── init_bigquery.py    # One-time BigQuery bootstrap
├── monitoring/
│   └── grafana-dashboard.json
├── docker-compose.yaml
├── requirements.txt
└── README.md
```
