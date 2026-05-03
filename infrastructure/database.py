import psycopg2

# Postgres connection parameters from agent-docker-compose.yaml
DB_PARAMS = {
    "host": "localhost",
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
        conn.commit()
        cur.close()
        conn.close()
        print("[Database] Initialized successfully.")
    except Exception as e:
        print(f"[Database] DB Init Error: {e}")
