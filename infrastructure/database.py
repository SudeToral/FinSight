import psycopg2

# Postgres connection parameters from agent-docker-compose.yaml
DB_PARAMS = {
    "host": "127.0.0.1",
    "port": "5433",
    "database": "agent_db",
    "user": "agent",
    "password": "agentpassword"
}

def get_db_connection():
    """Returns a psycopg2 database connection."""
    return psycopg2.connect(**DB_PARAMS)

def init_db():
    """Ensure the trade_history table exists."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                action VARCHAR(10) NOT NULL,
                risk_score DECIMAL(5, 2),
                reasoning TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                is_anomaly BOOLEAN NOT NULL,
                score DECIMAL(10, 6)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                symbol VARCHAR(10) PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Initialize with defaults if empty
        cur.execute("SELECT COUNT(*) FROM watchlist")
        if cur.fetchone()[0] == 0:
            for s in ["AAPL", "MSFT", "GOOGL"]:
                cur.execute("INSERT INTO watchlist (symbol) VALUES (%s)", (s,))
        
        conn.commit()
        cur.close()
        conn.close()
        print("[Database] Initialized successfully.")
    except Exception as e:
        print(f"[Database] DB Init Error: {e}")
