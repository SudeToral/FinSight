import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.database import get_db_connection

def check_counts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM trade_history")
        trades = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM anomaly_history")
        anomalies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM watchlist")
        watchlist = cur.fetchone()[0]
        
        print(f"Trades: {trades}")
        print(f"Anomalies: {anomalies}")
        print(f"Watchlist: {watchlist}")
        
        if watchlist > 0:
            cur.execute("SELECT symbol FROM watchlist")
            symbols = [r[0] for r in cur.fetchall()]
            print(f"Symbols in watchlist: {symbols}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_counts()
