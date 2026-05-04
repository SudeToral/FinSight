from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
import json

# Initialize Ollama LLM
llm = ChatOllama(model="llama3.1", temperature=0)

def supervisor_node(state: AgentState) -> AgentState:
    """
    Strategic Manager: Decides the next step based on data severity, 
    agent feedback, and missing information.
    """
    print(f"[Supervisor] Analyzing Strategy for {state['symbol']} | Price: {state['current_price']}")
    
    # ADVANCED LOGIC: Define strategy context
    risk_score = state.get('risk_score', 0)
    is_critical_anomaly = risk_score > 0.8
    has_critic_feedback = bool(state.get('critic_feedback'))
    
    system_prompt = """You are the Strategic Director of an Autonomous Trading System.
Your job is to orchestrate a team of specialists to handle market data efficiently and safely.

Available Specialists:
- market_analyzer: Use if technical features/anomaly scores are missing.
- news_researcher: Use to gather sentiment and external context.
- risk_manager: Final decision maker. Requires both news and technical data UNLESS there is an emergency.

STRATEGIC GUIDELINES:
1. EMERGENCY MODE: If the anomaly risk is EXTREME (>0.8), skip regular news research and go straight to risk_manager for an emergency stop/sell.
2. REFLEXION MODE: If there is 'critic_feedback', you must decide whether to send it back to the specialist (risk_manager) for revision or escalate to a human.
3. STANDARD MODE: Follow the flow: analyzer -> researcher -> risk_manager.

Output ONLY the specialist name as a single word: market_analyzer, news_researcher, risk_manager, human_node, or compliance.
"""

    human_prompt = f"""
--- CURRENT SYSTEM STATE ---
Symbol: {state['symbol']}
Market Analyzed: {state.get('market_analyzed', False)}
News Researched: {state.get('news_researched', False)}
Current Anomaly Score: {risk_score}
Critic Feedback Present: {has_critic_feedback}
Last Step: {state.get('next_step', 'None')}

Strategic Decision: Based on the state and guidelines, who should act next?
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        next_step = response.content.strip().lower()
        
        # Validation and Fallback to ensure system stability
        allowed_nodes = ["market_analyzer", "news_researcher", "risk_manager", "human_node", "compliance"]
        
        # 1. Hallucination check
        if next_step not in allowed_nodes:
            # Smart Fallback
            if not state.get('market_analyzed'):
                next_step = "market_analyzer"
            elif not state.get('news_researched') and not is_critical_anomaly:
                next_step = "news_researcher"
            else:
                next_step = "risk_manager"
        
        # 2. Safety Override: Don't allow bypassing analysis if it's not done
        if not state.get('market_analyzed') and next_step != "market_analyzer":
            print("[Supervisor] Safety Override: Forcing Market Analysis.")
            next_step = "market_analyzer"

        print(f"[Supervisor] Strategic Decision: {next_step.upper()}")
        return {"next_step": next_step}
        
    except Exception as e:
        print(f"[Supervisor] Critical Error: {e}")
        return {"next_step": "market_analyzer"} # Safety fallback
