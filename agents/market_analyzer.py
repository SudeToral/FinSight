import os
import pickle
import glob
import numpy as np
from agents.state import AgentState

def load_latest_model():
    """Finds the most recent model artifact from local_outputs."""
    list_of_files = glob.glob('local_outputs/*/train/output_model')
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, 'rb') as f:
        return pickle.load(f)

def market_analyzer_node(state: AgentState) -> AgentState:
    """
    Analyzes market data using the trained Isolation Forest model.
    """
    print(f"[Market Analyzer] Analyzing {state['symbol']} using real FinSight model...")
    
    artifact = load_latest_model()
    if not artifact:
        print("[Market Analyzer] Warning: No model found! Falling back to mock.")
        return {"anomaly_detected": False}
        
    model = artifact["model"]
    scaler = artifact["scaler"]
    feature_cols = artifact["feature_cols"]
    
    # Prepare features for prediction
    # WHY: Order matters! Must match the order used during training.
    features = np.array([[
        state.get("daily_return", 0),
        state.get("volatility_5d", 0),
        state.get("volume_ratio", 1),
        state.get("price_range_pct", 0)
    ]])
    
    # Scale features using the training-time scaler
    features_scaled = scaler.transform(features)
    
    # Predict: -1 is anomaly, 1 is normal
    prediction = model.predict(features_scaled)[0]
    # Decision function gives the anomaly score (lower is more anomalous)
    score = model.decision_function(features_scaled)[0]
    
    anomaly = True if prediction == -1 else False
    
    print(f"[Market Analyzer] Prediction: {'ANOMALY' if anomaly else 'NORMAL'} (Score: {score:.4f})")
    
    return {
        "anomaly_detected": anomaly,
        "risk_score": float(abs(score)) if anomaly else 0.0
    }
