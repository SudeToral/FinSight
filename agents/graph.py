from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import AgentState
from agents.market_analyzer import market_analyzer_node
from agents.risk_manager import risk_manager_node
from agents.compliance_agent import compliance_node
from agents.trade_executor import trade_executor_node
from agents.news_researcher import news_researcher_node

# Define the workflow
workflow = StateGraph(AgentState)

workflow.add_node("market_analyzer", market_analyzer_node)
workflow.add_node("news_researcher", news_researcher_node)
workflow.add_node("risk_manager", risk_manager_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("trade_executor", trade_executor_node)

workflow.set_entry_point("market_analyzer")
workflow.add_edge("market_analyzer", "news_researcher")
workflow.add_edge("news_researcher", "risk_manager")
workflow.add_edge("risk_manager", "compliance")
workflow.add_edge("compliance", "trade_executor")
workflow.add_edge("trade_executor", END)

# Use MemorySaver for local state checkpointing (Phase 3 of Sprint 2)
# LangGraph Checkpoint Redis can be plugged in here easily
checkpointer = MemorySaver()

# Compile with memory
app = workflow.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    mock_tick = {
        "symbol": "AAPL",
        "current_price": 145.50,
        "timestamp": "2024-05-01T10:00:00Z",
        "daily_return": -0.08,
        "volatility_5d": 0.05,
        "volume_ratio": 3.5,
        "price_range_pct": 0.04,
        "news_headlines": [],
        "anomaly_detected": False,
        "risk_score": 0.0,
        "decision": "",
        "reasoning": "",
        "compliance_approved": False,
        "trade_executed": False
    }
    
    print("\n--- Running Mock Tick ---")
    config = {"configurable": {"thread_id": "test_thread"}}
    result = app.invoke(mock_tick, config=config)
    print("\n--- Final Agent Decision ---")
    print(f"Action: {result['decision']}")
    print(f"Reasoning: {result['reasoning']}")
