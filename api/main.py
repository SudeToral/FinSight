from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from infrastructure.database import get_db_connection
import asyncio
import json

app = FastAPI(title="FinSight API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/trades/{symbol}")
async def get_trades(symbol: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trade_history WHERE symbol = %s ORDER BY timestamp DESC LIMIT 50", (symbol,))
    rows = cur.fetchall()
    
    trades = []
    for r in rows:
        trades.append({
            "id": r[0],
            "symbol": r[1],
            "price": float(r[2]),
            "timestamp": r[3].isoformat(),
            "action": r[4],
            "risk_score": float(r[5]) if r[5] else 0,
            "reasoning": r[6]
        })
    
    cur.close()
    conn.close()
    return trades

@app.get("/api/anomalies/{symbol}")
async def get_anomalies(symbol: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM anomaly_history WHERE symbol = %s ORDER BY timestamp DESC LIMIT 100", (symbol,))
    rows = cur.fetchall()
    
    anomalies = []
    for r in rows:
        anomalies.append({
            "id": r[0],
            "symbol": r[1],
            "price": float(r[2]),
            "timestamp": r[3].isoformat(),
            "is_anomaly": r[4],
            "score": float(r[5])
        })
    
    cur.close()
    conn.close()
    return anomalies

@app.get("/api/stats")
async def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM trade_history WHERE action != 'HOLD'")
    total_trades = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM anomaly_history WHERE is_anomaly = True")
    total_anomalies = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return {
        "total_trades": total_trades,
        "total_anomalies": total_anomalies,
        "status": "Healthy"
    }

@app.get("/api/watchlist")
async def get_watchlist():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM watchlist ORDER BY symbol ASC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

@app.post("/api/watchlist/{symbol}")
async def add_to_watchlist(symbol: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO watchlist (symbol) VALUES (%s) ON CONFLICT DO NOTHING", (symbol.upper(),))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return {"status": "added"}

@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist WHERE symbol = %s", (symbol.upper(),))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "removed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
