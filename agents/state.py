from typing import TypedDict, Annotated, List
import operator

class AgentState(TypedDict):
    symbol: str
    current_price: float
    timestamp: str
    news_headlines: List[str]
    daily_return: float
    volatility_5d: float
    volume_ratio: float
    price_range_pct: float
    anomaly_detected: bool
    risk_score: float
    decision: str
    reasoning: str
