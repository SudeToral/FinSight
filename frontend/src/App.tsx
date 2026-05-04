import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter
} from 'recharts';
import { 
  TrendingUp, AlertTriangle, Newspaper, ShieldCheck, Activity, Cpu, 
  ArrowDownRight, RefreshCw
} from 'lucide-react';

const API_BASE = "http://localhost:8000/api";

interface Trade {
  id: number;
  symbol: string;
  price: number;
  timestamp: string;
  action: string;
  risk_score: number;
  reasoning: string;
}

interface Anomaly {
  id: number;
  symbol: string;
  price: number;
  timestamp: string;
  is_anomaly: boolean;
  score: number;
}

const App = () => {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [newSymbol, setNewSymbol] = useState("");
  const [trades, setTrades] = useState<Trade[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [stats, setStats] = useState({ total_trades: 0, total_anomalies: 0 });
  const [loading, setLoading] = useState(true);
  
  // Use loading to satisfy TSC if needed, or just remove it
  console.log("Loading state:", loading); 

  const fetchWatchlist = async () => {
    try {
      const res = await axios.get(`${API_BASE}/watchlist`);
      setSymbols(res.data);
      if (res.data.length > 0 && !res.data.includes(symbol)) {
        setSymbol(res.data[0]);
      }
    } catch (err) {
      console.error("Watchlist fetch error:", err);
    }
  };

  const addSymbol = async (e: React.FormEvent) => {
    e.preventDefault();
    const sym = newSymbol.toUpperCase().trim();
    if (sym) {
      try {
        await axios.post(`${API_BASE}/watchlist/${sym}`);
        setNewSymbol("");
        fetchWatchlist();
        setSymbol(sym);
      } catch (err) {
        console.error("Add symbol error:", err);
      }
    }
  };

  const removeSymbol = async (sym: string) => {
    try {
      await axios.delete(`${API_BASE}/watchlist/${sym}`);
      fetchWatchlist();
    } catch (err) {
      console.error("Remove symbol error:", err);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchData = async () => {
    try {
      const [tradesRes, anomaliesRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/trades/${symbol}`),
        axios.get(`${API_BASE}/anomalies/${symbol}`),
        axios.get(`${API_BASE}/stats`)
      ]);
      setTrades(tradesRes.data);
      setAnomalies([...anomaliesRes.data].reverse());
      setStats(statsRes.data);
      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [symbol]);

  const latestPrice = anomalies.length > 0 ? anomalies[anomalies.length - 1].price : 0;
  const isLastAnomaly = anomalies.length > 0 ? anomalies[anomalies.length - 1].is_anomaly : false;

  return (
    <div className="min-h-screen bg-[#0b0e14] text-gray-100 font-sans p-6">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 glass p-4 px-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/20 rounded-lg">
            <TrendingUp className="text-accent w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">FinSight <span className="text-accent">Terminal</span></h1>
        </div>
        
        <div className="flex items-center gap-6">
          <form onSubmit={addSymbol} className="relative">
            <input 
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              placeholder="Add Ticker (e.g. TSLA)"
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-1.5 text-sm focus:outline-none focus:border-accent/50 w-48 pr-10"
            />
            <button type="submit" className="absolute right-2 top-1.5 text-accent hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </form>

          <div className="flex bg-panel rounded-lg p-1 border border-white/5 overflow-x-auto max-w-md">
            {symbols.map(s => (
              <div key={s} className="relative group">
                <button 
                  onClick={() => setSymbol(s)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all mr-1 whitespace-nowrap ${
                    symbol === s ? "bg-accent text-dark shadow-lg shadow-accent/20" : "hover:bg-white/5"
                  }`}
                >
                  {s}
                </button>
                {symbols.length > 1 && (
                  <button 
                    onClick={(e) => { e.stopPropagation(); removeSymbol(s); }}
                    className="absolute -top-1 -right-1 bg-anomaly text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <ArrowDownRight className="w-2 h-2 rotate-45" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            LIVE FEED
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        
        {/* Left Column: Stats & Chart */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          
          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-6">
            <StatCard 
              label="Market Price" 
              value={`$${latestPrice.toFixed(2)}`} 
              icon={<Activity className="text-accent" />}
              sub={isLastAnomaly ? "🚨 Anomaly Detected" : "Stable Trend"}
              subColor={isLastAnomaly ? "text-anomaly" : "text-green-400"}
            />
            <StatCard 
              label="AI Actions" 
              value={stats.total_trades.toString()} 
              icon={<ShieldCheck className="text-green-400" />}
              sub="Total Executed"
            />
            <StatCard 
              label="Anomalies" 
              value={stats.total_anomalies.toString()} 
              icon={<AlertTriangle className="text-anomaly" />}
              sub="Captured Today"
            />
          </div>

          {/* Price Chart */}
          <div className="glass p-6 min-h-[400px]">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Cpu className="w-5 h-5 text-accent" /> Real-time Neural Analysis
              </h3>
            </div>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={anomalies}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3f" vertical={false} />
                  <XAxis 
                    dataKey="timestamp" 
                    hide 
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    stroke="#4b5563" 
                    fontSize={12}
                    tickFormatter={(val) => `$${val}`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e2130', border: '1px solid #3e4259', borderRadius: '8px' }}
                    itemStyle={{ color: '#00d1ff' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#00d1ff" 
                    strokeWidth={3} 
                    dot={false}
                    animationDuration={300}
                  />
                  {/* Anomaly Dots */}
                  <Scatter 
                    data={anomalies.filter(d => d.is_anomaly)} 
                    fill="#ff4b4b" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column: Decision Feed */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          <div className="glass flex-1 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-white/5 bg-white/2 flex justify-between items-center">
              <h3 className="font-semibold flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-accent" /> Agent Reasoning
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {trades.length === 0 && (
                <div className="text-center py-20 text-gray-500 italic">
                  Waiting for market triggers...
                </div>
              )}
              {trades.map((trade) => (
                <DecisionCard key={trade.id} trade={trade} />
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  sub: string;
  subColor?: string;
}

const StatCard = ({ label, value, icon, sub, subColor = "text-gray-400" }: StatCardProps) => (
  <div className="glass p-5 flex flex-col gap-2">
    <div className="flex justify-between items-start">
      <span className="text-sm font-medium text-gray-400">{label}</span>
      <div className="p-2 bg-white/5 rounded-lg">{icon}</div>
    </div>
    <div className="text-3xl font-bold">{value}</div>
    <div className={`text-xs font-medium ${subColor}`}>{sub}</div>
  </div>
);

const DecisionCard = ({ trade }: { trade: Trade }) => (
  <div className="p-4 rounded-xl bg-white/2 border border-white/5 hover:border-accent/30 transition-colors">
    <div className="flex justify-between items-center mb-3">
      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${
        trade.action === "BUY" ? "bg-green-500/20 text-green-400" : 
        trade.action === "SELL" ? "bg-anomaly/20 text-anomaly" : "bg-white/10 text-gray-400"
      }`}>
        {trade.action}
      </span>
      <span className="text-[10px] text-gray-500">
        {new Date(trade.timestamp).toLocaleTimeString()}
      </span>
    </div>
    <p className="text-xs leading-relaxed text-gray-300">
      {trade.reasoning}
    </p>
    <div className="mt-3 pt-3 border-t border-white/5 flex justify-between items-center">
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 bg-accent rounded-full" />
        <span className="text-[10px] text-gray-500 font-medium">Risk Score: {trade.risk_score}</span>
      </div>
      {trade.action !== "HOLD" && (
        <ShieldCheck className="w-4 h-4 text-accent/50" />
      )}
    </div>
  </div>
);
export default App;
