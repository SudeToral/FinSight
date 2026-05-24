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
    # If a final execution step has already been determined by the critic or risk manager, bypass LLM
    if state.get("next_step") in ["compliance", "human_node", "mlops_monitor"]:
        print(f"[Supervisor] Bypassing LLM. Routing to already determined step: {state['next_step'].upper()}")
        return {"next_step": state['next_step']}

    print(f"[Supervisor] Analyzing Strategy for {state['symbol']} | Price: {state['current_price']}")
    print(f"[Supervisor] DEBUG STATE: market_analyzed={state.get('market_analyzed')}, news_researched={state.get('news_researched')}, next_step={state.get('next_step')}, risk_score={state.get('risk_score')}, critic_feedback={state.get('critic_feedback')}")
    
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

        # 3. Loop Prevention: If already analyzed, do NOT route back to analyzer
        if state.get('market_analyzed') and next_step == "market_analyzer":
            if not state.get('news_researched'):
                next_step = "news_researcher"
            else:
                next_step = "risk_manager"
                
        # 4. Loop Prevention: If already researched, do NOT route back to researcher
        if state.get('news_researched') and next_step == "news_researcher":
            next_step = "risk_manager"

        # 5. Loop Prevention: If risk manager and critic have already run, force progression to human/compliance
        if state.get('risk_score', 0) > 0 and next_step in ["risk_manager", "market_analyzer", "news_researcher"]:
            if state.get('critic_feedback') and state.get('human_approval') is None:
                next_step = "human_node"
            elif state.get('critic_feedback'):
                next_step = "compliance"
            else:
                next_step = "risk_manager"

        print(f"[Supervisor] Strategic Decision: {next_step.upper()}")
        return {"next_step": next_step}
        
    except Exception as e:
        print(f"[Supervisor] Ollama Connection Failed ({e}). Using deterministic rule-based router.")
        # Ensure sequential flow: analyzer -> researcher -> risk_manager -> critic -> human/compliance
        if not state.get('market_analyzed'):
            next_step = "market_analyzer"
        elif not state.get('news_researched'):
            next_step = "news_researcher"
        elif state.get('risk_score', 0) == 0:
            next_step = "risk_manager"
        elif not state.get('critic_feedback'):
            next_step = "critic"
        elif state.get('human_approval') is None:
            next_step = "human_node"
        else:
            next_step = "compliance"
        return {"next_step": next_step}
