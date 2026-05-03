from agents.state import AgentState

def compliance_node(state: AgentState) -> AgentState:
    """
    Checks if the proposed trade violates any compliance rules.
    """
    print(f"[Compliance Agent] Checking trade decision: {state['decision']}")
    
    approved = True
    reasoning = state.get('reasoning', '')
    
    # Simple hardcoded rules
    if state['decision'] == 'BUY' and state.get('risk_score', 0) > 0.8:
        approved = False
        reasoning += " | REJECTED by Compliance: Risk score too high for BUY."
        
    if not approved:
        print("[Compliance Agent] ⛔ Trade REJECTED.")
        decision = "HOLD" # Fallback to hold if rejected
    else:
        print("[Compliance Agent] ✅ Trade APPROVED.")
        decision = state['decision']
        
    return {
        "compliance_approved": approved,
        "decision": decision,
        "reasoning": reasoning
    }
