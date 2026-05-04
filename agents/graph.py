from langgraph.graph import StateGraph, END
from agents.state import AgentState

# Import all nodes
from agents.supervisor import supervisor_node
from agents.market_analyzer import market_analyzer_node
from agents.news_researcher import news_researcher_node
from agents.risk_manager import risk_manager_node
from agents.critic_agent import critic_node
from agents.human_node import human_node
from agents.compliance_agent import compliance_node
from agents.trade_executor import trade_executor_node
from agents.mlops_monitor import mlops_monitor_node

def supervisor_router(state: AgentState):
    """Routes the flow based on supervisor's decision."""
    return state["next_step"]

def critic_router(state: AgentState):
    """Routes the flow based on critic's feedback."""
    return state["next_step"]

def human_router(state: AgentState):
    """Routes the flow based on human approval."""
    return state["next_step"]

# Define the workflow
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("market_analyzer", market_analyzer_node)
workflow.add_node("news_researcher", news_researcher_node)
workflow.add_node("risk_manager", risk_manager_node)
workflow.add_node("critic", critic_node)
workflow.add_node("human_node", human_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("trade_executor", trade_executor_node)
workflow.add_node("mlops_monitor", mlops_monitor_node)

# Entry point
workflow.set_entry_point("supervisor")

# --- Routing Logic ---

# 1. Supervisor decides which specialist to call
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "market_analyzer": "market_analyzer",
        "news_researcher": "news_researcher",
        "risk_manager": "risk_manager",
        "human_node": "human_node",
        "compliance": "compliance"
    }
)

# 2. Specialists always return to Supervisor for the next command
workflow.add_edge("market_analyzer", "supervisor")
workflow.add_edge("news_researcher", "supervisor")

# 3. Risk Manager goes to Critic for review (Reflexion)
workflow.add_edge("risk_manager", "critic")

# 4. Critic returns to Supervisor to decide the next strategic move
workflow.add_edge("critic", "supervisor")

# 5. Human node decides to proceed or trigger MLOps
workflow.add_conditional_edges(
    "human_node",
    human_router,
    {
        "compliance": "compliance",
        "mlops_monitor": "mlops_monitor"
    }
)

# 6. Final Execution Path
workflow.add_edge("compliance", "trade_executor")
workflow.add_edge("trade_executor", END)
workflow.add_edge("mlops_monitor", END)

# NOT: LangGraph Studio / langgraph dev kendi persistence (Postgres) yapısını 
# otomatik kurduğu için manuel checkpointer'ı kaldırıyoruz.
app = workflow.compile()

print("[Graph] Advanced Supervisor + Reflexion Graph successfully compiled.")
