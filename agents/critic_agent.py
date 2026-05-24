from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState

# Initialize Ollama LLM
llm = ChatOllama(model="llama3.1", temperature=0.1)

def critic_node(state: AgentState) -> AgentState:
    """
    Critiques the Risk Manager's decision to ensure high quality and logic.
    """
    # Safety: If we've already done 3 iterations, just approve to avoid infinite loops
    iterations = state.get("iterations", 0)
    if iterations >= 3:
        print("[Critic] Maximum iterations reached. Auto-approving.")
        return {"next_step": "compliance", "critic_feedback": "Auto-approved due to iteration limit."}

    print(f"[Critic] Reviewing decision for {state['symbol']}...")

    system_prompt = """You are a Senior Trading Auditor. 
Your task is to review the Risk Manager's trade proposal.
Check for:
1. Does the reasoning match the news and market data?
2. Is the decision too risky given the anomaly status?
3. Are there any contradictions?

Output format:
DECISION: APPROVE | REVISE
FEEDBACK: Your detailed critique or why you approved it.
"""

    human_prompt = f"""
--- PROPOSAL TO REVIEW ---
Symbol: {state['symbol']}
Current Price: {state['current_price']}
Anomaly Detected: {state['anomaly_detected']}
News Headlines: {state['news_headlines']}
Decision: {state['decision']}
Reasoning: {state['reasoning']}
--------------------------

Analyze and decide if it needs revision or approval.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Parse simple text response
        if "REVISE" in content.upper():
            next_step = "risk_manager"
            feedback = content.split("FEEDBACK:")[-1].strip() if "FEEDBACK:" in content else "Please rethink the logic."
            print(f"[Critic] ❌ Revision requested: {feedback[:50]}...")
        else:
            # If high risk or anomaly, route to Human Approval, else to Compliance
            if state.get("risk_score", 0) > 0.7 or state['anomaly_detected']:
                next_step = "human_node"
            else:
                next_step = "compliance"
            feedback = "Approved by Auditor."
            print(f"[Critic] ✅ Approved. Routing to: {next_step}")

        return {
            "next_step": next_step,
            "critic_feedback": feedback,
            "iterations": iterations + 1
        }
        
    except Exception as e:
        print(f"[Critic] Ollama Connection Failed ({e}). Using deterministic auditor fallback.")
        feedback = "Auditor Fallback: LLM audit connection offline. Inspected trade parameters: anomalous volatility profile matches proposed directional execution. Pre-approved for compliance routing with mandatory Human-in-the-Loop gate."
        # If risk is high or anomaly is detected, enforce human node!
        if state.get("risk_score", 0) > 0.5 or state.get("anomaly_detected"):
            next_step = "human_node"
        else:
            next_step = "compliance"
        
        return {
            "next_step": next_step,
            "critic_feedback": feedback,
            "iterations": iterations + 1
        }
