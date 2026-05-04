from agents.state import AgentState
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize Ollama LLM (make sure Ollama is running locally with llama3 or another model)
llm = ChatOllama(model="llama3.1", temperature=0.1)

def risk_manager_node(state: AgentState) -> AgentState:
    """
    Evaluates the anomaly and decides if a trade should be executed using an LLM.
    """
    print(f"[Risk Manager] Evaluating anomaly status: {state['anomaly_detected']}")
    
    # Construct a prompt for the LLM
    system_prompt = """You are an elite autonomous AI trading risk manager.
Your job is to analyze the market data and any detected anomalies to decide whether to BUY, SELL, or HOLD.
Output exactly and only the following JSON format:
{"decision": "BUY|SELL|HOLD", "reasoning": "A short explanation of your decision."}
"""

    human_prompt = f"""
Current Market Data for {state['symbol']}:
- Price: ${state['current_price']}
- Anomaly Detected: {state['anomaly_detected']}
- Recent News: {state['news_headlines']}

--- CRITIC FEEDBACK ---
{state.get('critic_feedback', 'No feedback yet.')}
-----------------------

What is your risk decision? Please address any critic feedback in your reasoning if present.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        # We expect JSON output. In production, we'd use StructuredOutputParser.
        import json
        
        # Simple extraction logic if the model wrapped it in markdown
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
            
        parsed = json.loads(content)
        decision = parsed.get("decision", "HOLD")
        reasoning = parsed.get("reasoning", "Parsed from LLM response.")
        risk_score = 0.9 if decision != "HOLD" else 0.2
        
    except Exception as e:
        print(f"[Risk Manager] Error calling Ollama: {e}")
        decision = "HOLD"
        reasoning = "Fallback to HOLD due to LLM error."
        risk_score = 0.0

    return {"risk_score": risk_score, "decision": decision, "reasoning": reasoning}
