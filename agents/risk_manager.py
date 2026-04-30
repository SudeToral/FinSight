from agents.state import AgentState

def risk_manager_node(state: AgentState) -> AgentState:
    """
    Evaluates the anomaly and decides if a trade should be executed.
    """
    print(f"[Risk Manager] Evaluating anomaly status: {state['anomaly_detected']}")
    
    risk_score = 0.0
    if state['anomaly_detected']:
        risk_score = 0.9
        decision = "SELL"
        reasoning = "Anomaly detected by FinSight model indicating sharp irregular price drop."
    else:
        risk_score = 0.2
        decision = "HOLD"
        reasoning = "Market is behaving normally according to Isolation Forest."
        
    return {"risk_score": risk_score, "decision": decision, "reasoning": reasoning}
