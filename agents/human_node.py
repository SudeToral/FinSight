from agents.state import AgentState

def human_node(state: AgentState) -> AgentState:
    """
    This node is reached ONLY after the graph is resumed.
    It checks if an approval exists in the state (from API) 
    or asks for it via terminal (local fallback).
    """
    # 1. Check if approval was already injected (via API/State update)
    approval = state.get("human_approval")
    
    if approval is True:
        print("\n✅ Trade approved via external signal (API).")
        return {"next_step": "compliance"}
    
    if approval is False:
        print("\n❌ Trade rejected via external signal (API).")
        return {"next_step": "mlops_monitor", "decision": "HOLD"}

    # 2. Local Fallback: If no approval in state, ask via Terminal
    print("\n" + "="*50)
    print("📢 HUMAN APPROVAL REQUIRED (CLI FALLBACK)")
    print(f"Agent wants to execute: {state.get('decision', 'UNKNOWN')}")
    print(f"Symbol: {state.get('symbol')} | Reasoning: {state.get('reasoning', 'N/A')}")
    print("="*50)
    
    user_input = input("\nDo you approve? (y/n): ").strip().lower()
    
    if user_input in ['y', 'yes', 'evet']:
        return {"human_approval": True, "next_step": "compliance"}
    else:
        return {"human_approval": False, "next_step": "mlops_monitor", "decision": "HOLD"}
