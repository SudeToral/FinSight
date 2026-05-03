from agents.state import AgentState
from infrastructure.database import get_db_connection, init_db

# Initialize DB on import
init_db()

def trade_executor_node(state: AgentState) -> AgentState:
    """
    Executes the trade by logging it into Postgres.
    """
    decision = state['decision']
    if decision == 'HOLD':
        print("[Trade Executor] Action is HOLD. No trade executed.")
        return {"trade_executed": False}
        
    print(f"[Trade Executor] Executing {decision} for {state['symbol']} at {state['current_price']}")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO trade_history (symbol, price, timestamp, action, risk_score, reasoning)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            state['symbol'], 
            state['current_price'], 
            state['timestamp'], 
            decision, 
            state['risk_score'], 
            state['reasoning']
        ))
        conn.commit()
        cur.close()
        conn.close()
        print("[Trade Executor] Trade successfully logged to Postgres!")
        executed = True
    except Exception as e:
        print(f"[Trade Executor] Failed to execute trade: {e}")
        executed = False
        
    return {"trade_executed": executed}
