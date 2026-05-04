import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database import get_db_connection

# Page Config
st.set_page_config(
    page_title="FinSight | Autonomous Trading AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4259;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title & Status
st.title("📈 FinSight: Advanced Agentic Trading")
st.markdown("---")

# Sidebar for controls
st.sidebar.header("📊 Monitoring Controls")
symbol = st.sidebar.selectbox("Select Symbol", ["AAPL", "MSFT", "GOOGL"])
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 3)

@st.cache_data(ttl=1)
def fetch_data(sym):
    try:
        conn = get_db_connection()
        # Fetch Trade History
        trades_df = pd.read_sql(f"SELECT * FROM trade_history WHERE symbol='{sym}' ORDER BY timestamp DESC LIMIT 5", conn)
        # Fetch Anomaly History (last 100 points)
        anomalies_df = pd.read_sql(f"SELECT * FROM anomaly_history WHERE symbol='{sym}' ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        return trades_df, anomalies_df
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Main Layout
col1, col2, col3 = st.columns(3)

placeholder = st.empty()

while True:
    trades, anomalies = fetch_data(symbol)
    
    with placeholder.container():
        # Metric Row
        if not anomalies.empty:
            curr_price = anomalies.iloc[0]['price']
            is_anomaly = anomalies.iloc[0]['is_anomaly']
            score = anomalies.iloc[0]['score']
            
            with col1:
                st.metric("Current Price", f"${curr_price:.2f}", delta=f"{(curr_price - anomalies.iloc[1]['price']):.2f}" if len(anomalies) > 1 else None)
            with col2:
                status = "🚨 ANOMALY" if is_anomaly else "✅ NORMAL"
                st.metric("Model Status", status, delta_color="inverse" if is_anomaly else "normal")
            with col3:
                st.metric("Anomaly Score", f"{score:.4f}")
        
        st.markdown("### 📊 Real-time Market Analysis")
        
        # Plotly Chart
        if not anomalies.empty:
            fig = go.Figure()
            # Price Line
            fig.add_trace(go.Scatter(
                x=anomalies['timestamp'], 
                y=anomalies['price'],
                mode='lines',
                name='Price',
                line=dict(color='#00d1ff', width=2)
            ))
            # Anomaly Points
            anomaly_points = anomalies[anomalies['is_anomaly'] == True]
            fig.add_trace(go.Scatter(
                x=anomaly_points['timestamp'],
                y=anomaly_points['price'],
                mode='markers',
                name='Anomaly Detected',
                marker=dict(color='#ff4b4b', size=10, symbol='x')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                margin=dict(l=20, r=20, t=20, b=20),
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Agent Decisions Panel
        st.markdown("### 🤖 Agent Decision Log")
        if not trades.empty:
            for _, row in trades.iterrows():
                color = "#ff4b4b" if row['action'] == "SELL" else "#00d1ff" if row['action'] == "BUY" else "#ffffff"
                with st.expander(f"{row['timestamp'].strftime('%H:%M:%S')} - Decision: {row['action']} (Risk: {row['risk_score']})"):
                    st.write(f"**Reasoning:** {row['reasoning']}")
        else:
            st.info("Waiting for agent decisions...")

    time.sleep(refresh_rate)
