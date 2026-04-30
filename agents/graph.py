from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.market_analyzer import market_analyzer_node
from agents.risk_manager import risk_manager_node

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("market_analyzer", market_analyzer_node)
    workflow.add_node("risk_manager", risk_manager_node)
    
    workflow.set_entry_point("market_analyzer")
    workflow.add_edge("market_analyzer", "risk_manager")
    workflow.add_edge("risk_manager", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = build_graph()
    
    # Simulate a price tick coming from Kafka with features
    mock_tick = {
        "symbol": "AAPL",
        "current_price": 145.50,
        "timestamp": "2024-05-01T10:00:00Z",
        "daily_return": -0.08,        # %8 düşüş (Anomali sinyali!)
        "volatility_5d": 0.05,        # Yüksek volatilite
        "volume_ratio": 3.5,          # Normalin 3.5 katı hacim
        "price_range_pct": 0.04,      # Gün içi sert hareket
        "news_headlines": ["Market jittery as tech stocks fluctuate."],
        "anomaly_detected": False,
        "risk_score": 0.0,
        "decision": "",
        "reasoning": ""
    }
    
    print("\n--- Running Mock Tick ---")
    result = app.invoke(mock_tick)
    print("\n--- Final Agent Decision ---")
    print(f"Action: {result['decision']}")
    print(f"Reasoning: {result['reasoning']}")
