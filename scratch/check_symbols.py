import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.database import get_db_connection

def check_symbol_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for symbol in ['MSFT', 'GOOGL', 'AAPL']:
            cur.execute("SELECT COUNT(*) FROM anomaly_history WHERE symbol = %s", (symbol,))
            count = cur.fetchone()[0]
            print(f"Data for {symbol}: {count} records")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_symbol_data()
