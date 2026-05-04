from agents.state import AgentState

def human_node(state: AgentState) -> AgentState:
    """
    Pauses execution and waits for human approval via terminal.
    """
    print("\n" + "="*50)
    print("📢 HUMAN APPROVAL REQUIRED")
    print(f"Agent wants to execute: {state['decision']}")
    print(f"Symbol: {state['symbol']} | Price: {state['current_price']}")
    print(f"Risk Score: {state['risk_score']} | Anomaly: {state['anomaly_detected']}")
    print(f"Reasoning: {state['reasoning']}")
    print(f"Critic Feedback: {state.get('critic_feedback', 'N/A')}")
    print("="*50)
    
    user_input = input("\nDo you approve this trade? (yes/no): ").strip().lower()
    
    if user_input in ['yes', 'y', 'evet']:
        print("✅ Trade approved by human.")
        return {
            "human_approval": True,
            "next_step": "compliance" # Proceed to execution
        }
    else:
        print("❌ Trade rejected by human.")
        return {
            "human_approval": False,
            "next_step": "mlops_monitor", # Track this rejection as a potential model drift
            "decision": "HOLD",
            "reasoning": state['reasoning'] + " | REJECTED BY HUMAN."
        }
