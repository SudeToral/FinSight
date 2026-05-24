import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter
} from 'recharts';
import { 
  TrendingUp, AlertTriangle, Newspaper, ShieldCheck, Activity, Cpu, 
  ArrowDownRight, RefreshCw, Brain, CheckCircle2, Clock, UserCheck,
  ThumbsUp, ThumbsDown, Flame, ArrowUpRight
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

interface AgentStateValues {
  symbol?: string;
  current_price?: number;
  news_headlines?: string[];
  anomaly_detected?: boolean;
  risk_score?: number;
  decision?: string;
  reasoning?: string;
  critic_feedback?: string;
  market_analyzed?: boolean;
  news_researched?: boolean;
  trade_executed?: boolean;
}

interface AgentStateResponse {
  thread_id: string;
  next_step: string[];
  values: AgentStateValues;
  metadata?: any;
}

const App = () => {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [newSymbol, setNewSymbol] = useState("");
  const [trades, setTrades] = useState<Trade[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [stats, setStats] = useState({ total_trades: 0, total_anomalies: 0 });
  const [agentState, setAgentState] = useState<AgentStateResponse | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

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
      const [tradesRes, anomaliesRes, statsRes, agentStateRes] = await Promise.all([
        axios.get(`${API_BASE}/trades/${symbol}`),
        axios.get(`${API_BASE}/anomalies/${symbol}`),
        axios.get(`${API_BASE}/stats`),
        axios.get(`${API_BASE}/agent/state/${symbol}`)
      ]);
      setTrades(tradesRes.data);
      setAnomalies([...anomaliesRes.data].reverse());
      setStats(statsRes.data);
      setAgentState(agentStateRes.data);
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll fast (2 seconds) to keep the pipeline and HITL panel fully interactive and responsive
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [symbol]);

  const handleApprove = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await axios.post(`${API_BASE}/agent/approve`, { symbol });
      setActionMessage({ type: 'success', text: res.data.message || "Trade successfully approved!" });
      setTimeout(() => setActionMessage(null), 5000);
      fetchData();
    } catch (err: any) {
      console.error("Approval error:", err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || "Failed to approve trade." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await axios.post(`${API_BASE}/agent/reject`, { symbol });
      setActionMessage({ type: 'success', text: res.data.message || "Trade successfully rejected." });
      setTimeout(() => setActionMessage(null), 5000);
      fetchData();
    } catch (err: any) {
      console.error("Rejection error:", err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || "Failed to reject trade." });
    } finally {
      setActionLoading(false);
    }
  };

  const latestPrice = anomalies.length > 0 ? anomalies[anomalies.length - 1].price : 0;
  const isLastAnomaly = anomalies.length > 0 ? anomalies[anomalies.length - 1].is_anomaly : false;

  // Determine current pipeline active/completed steps
  const isPausedForHuman = agentState?.next_step?.includes("human_node");
  const values = agentState?.values;
  const marketAnalyzed = values?.market_analyzed;
  const newsResearched = values?.news_researched;
  const riskAssessed = values?.risk_score !== undefined && values.risk_score > 0;
  const criticCompleted = values?.critic_feedback !== undefined && values.critic_feedback !== "";
  const executionFinished = values?.trade_executed;

  return (
    <div className="min-h-screen bg-[#0b0e14] text-gray-100 font-sans p-6">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 glass p-4 px-6 border-accent/20 shadow-[0_0_15px_rgba(0,209,255,0.05)]">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/20 rounded-lg shadow-[0_0_10px_rgba(0,209,255,0.2)]">
            <TrendingUp className="text-accent w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">FinSight <span className="text-accent">Terminal</span></h1>
            <p className="text-[10px] text-gray-400 mt-0.5 tracking-wider font-mono">AUTONOMOUS MULTI-AGENT SWARM</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <form onSubmit={addSymbol} className="relative">
            <input 
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              placeholder="Add Ticker (e.g. TSLA)"
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-1.5 text-sm focus:outline-none focus:border-accent/50 w-48 pr-10 transition-all font-mono"
            />
            <button type="submit" className="absolute right-2 top-1.5 text-accent hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </form>

          <div className="flex bg-panel rounded-lg p-1 border border-white/5 overflow-x-auto max-w-md shadow-inner">
            {symbols.map(s => (
              <div key={s} className="relative group">
                <button 
                  onClick={() => { setSymbol(s); setAgentState(null); }}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all mr-1 whitespace-nowrap ${
                    symbol === s ? "bg-accent text-dark shadow-lg shadow-accent/30 font-bold" : "hover:bg-white/5"
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
          <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
            <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-ping" />
            <div className="w-2.5 h-2.5 bg-green-500 rounded-full absolute" />
            LIVE FEED
          </div>
        </div>
      </header>

      {/* Dynamic Agentic Swarm Workflow Tracker */}
      <section className="glass p-5 mb-8 border-accent/10 shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
          <h3 className="text-xs font-bold font-mono text-gray-400 tracking-widest flex items-center gap-2">
            <Cpu className="w-4 h-4 text-accent animate-spin-slow" /> LIVE AGENT SWARM PIPELINE STATUS
          </h3>
          <span className="text-[10px] font-mono bg-accent/10 text-accent px-2 py-0.5 rounded border border-accent/20">
            THREAD_ID: {agentState?.thread_id || `thread_${symbol}`}
          </span>
        </div>
        <div className="grid grid-cols-6 gap-4 relative">
          
          {/* Connector Line in background */}
          <div className="absolute top-[22px] left-[5%] right-[5%] h-0.5 bg-white/5 z-0" />
          
          <PipelineStep 
            stepNum={1} 
            title="Market Analyzer" 
            desc="Anomaly Detection" 
            isActive={!marketAnalyzed} 
            isCompleted={!!marketAnalyzed} 
          />
          <PipelineStep 
            stepNum={2} 
            title="News Swarm" 
            desc="Sentiment Extraction" 
            isActive={!!marketAnalyzed && !newsResearched} 
            isCompleted={!!newsResearched} 
          />
          <PipelineStep 
            stepNum={3} 
            title="Risk Manager" 
            desc="Portfolio Guard" 
            isActive={!!newsResearched && !riskAssessed} 
            isCompleted={riskAssessed} 
          />
          <PipelineStep 
            stepNum={4} 
            title="Reflexion Loop" 
            desc="Critic Evaluation" 
            isActive={riskAssessed && !criticCompleted} 
            isCompleted={criticCompleted} 
          />
          <PipelineStep 
            stepNum={5} 
            title="Human Gate" 
            desc="Security Approval" 
            isActive={!!isPausedForHuman} 
            isCompleted={criticCompleted && !isPausedForHuman && (!!executionFinished || trades.length > 0)} 
            isAlert={!!isPausedForHuman}
          />
          <PipelineStep 
            stepNum={6} 
            title="Executor" 
            desc="Order Placement" 
            isActive={criticCompleted && !isPausedForHuman && !executionFinished && trades.length > 0} 
            isCompleted={!!executionFinished || (trades.length > 0 && trades[0]?.action !== "HOLD")} 
          />
        </div>
      </section>

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
              subColor={isLastAnomaly ? "text-anomaly font-bold" : "text-green-400 font-medium"}
              glow={isLastAnomaly}
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
          <div className="glass p-6 min-h-[400px] border-white/5 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-accent/2 rounded-full blur-[100px] -z-10 pointer-events-none" />
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Cpu className="w-5 h-5 text-accent" /> Neural Prediction Engine
              </h3>
              <div className="flex gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-accent"><span className="w-2 h-2 rounded-full bg-accent" /> Real-time Price</span>
                <span className="flex items-center gap-1.5 text-anomaly"><span className="w-2 h-2 rounded-full bg-anomaly animate-pulse" /> Anomalous Ticks</span>
              </div>
            </div>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={anomalies}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2230" vertical={false} />
                  <XAxis 
                    dataKey="timestamp" 
                    hide 
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    stroke="#4b5563" 
                    fontSize={11}
                    tickFormatter={(val) => `$${val}`}
                    axisLine={false}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#131722', border: '1px solid #2a2e3f', borderRadius: '8px' }}
                    itemStyle={{ color: '#00d1ff' }}
                    labelStyle={{ color: '#9ca3af', fontSize: '10px' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#00d1ff" 
                    strokeWidth={2.5} 
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

        {/* Right Column: Interactive Approval Panel & Decisions */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          
          {/* HITL Control Panel (The Interactive Cockpit) */}
          <div className={`glass border-2 transition-all duration-500 overflow-hidden flex flex-col rounded-xl shadow-2xl relative ${
            isPausedForHuman 
              ? "border-anomaly/40 shadow-anomaly/5" 
              : "border-white/5"
          }`}>
            <div className={`p-4 border-b border-white/5 flex justify-between items-center transition-colors ${
              isPausedForHuman ? "bg-anomaly/10" : "bg-white/2"
            }`}>
              <h3 className="font-semibold flex items-center gap-2 tracking-wide">
                <Brain className={`w-5 h-5 ${isPausedForHuman ? "text-anomaly animate-pulse" : "text-accent"}`} />
                {isPausedForHuman ? "📢 DECISION SUSPENDED" : "🤖 AGENT STATUS"}
              </h3>
              {isPausedForHuman ? (
                <span className="text-[9px] bg-anomaly/20 text-anomaly border border-anomaly/40 px-2 py-0.5 rounded font-bold animate-pulse font-mono">
                  APPROVAL REQUIRED
                </span>
              ) : (
                <span className="text-[9px] bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded font-mono">
                  MONITORING ACTIVE
                </span>
              )}
            </div>

            <div className="p-5 flex-1 flex flex-col justify-between min-h-[300px]">
              
              {/* Scenario A: Agent is paused and waiting for human approval */}
              {isPausedForHuman && values ? (
                <div className="space-y-4 flex-1 flex flex-col justify-between">
                  <div>
                    {/* Glowing Proposed Action Header */}
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <span className="text-xs text-gray-400 font-mono tracking-wider">PROPOSED ACTION</span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-3 py-1 rounded text-base font-black tracking-widest shadow-lg ${
                            values.decision === "BUY" 
                              ? "bg-green-500 text-dark shadow-green-500/20" 
                              : values.decision === "SELL" 
                              ? "bg-anomaly text-white shadow-anomaly/20" 
                              : "bg-white/10 text-gray-300"
                          }`}>
                            {values.decision}
                          </span>
                          <span className="text-xl font-bold font-mono">{values.symbol}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-gray-400 font-mono tracking-wider">TRIGGER PRICE</span>
                        <div className="text-lg font-black text-white font-mono mt-1">${values.current_price?.toFixed(2)}</div>
                      </div>
                    </div>

                    {/* Risk & Anomaly Indicators */}
                    <div className="grid grid-cols-2 gap-3 p-3 bg-white/2 border border-white/5 rounded-lg mb-4">
                      <div>
                        <span className="text-[10px] text-gray-400 font-mono block">CRITIC RISK SCORE</span>
                        <div className="flex items-center gap-1.5 mt-1">
                          <Flame className={`w-4 h-4 ${values.risk_score && values.risk_score > 6 ? "text-anomaly" : "text-amber-400"}`} />
                          <span className="text-sm font-black font-mono">{values.risk_score} <span className="text-[10px] font-normal text-gray-500">/ 10</span></span>
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-gray-400 font-mono block">ANOMALY FLAG</span>
                        <span className={`text-xs font-bold block mt-1.5 ${values.anomaly_detected ? "text-anomaly" : "text-green-400"}`}>
                          {values.anomaly_detected ? "🚨 CRITICAL OUTLIER" : "NORMAL FLUCTUATION"}
                        </span>
                      </div>
                    </div>

                    {/* Agent Reasoning */}
                    <div className="mb-4">
                      <span className="text-[10px] text-gray-400 font-mono block mb-1">BRAIN REASONING</span>
                      <p className="text-xs text-gray-300 leading-relaxed bg-white/2 p-3 rounded-lg border border-white/5 font-sans italic max-h-[80px] overflow-y-auto custom-scrollbar">
                        "{values.reasoning}"
                      </p>
                    </div>

                    {/* Reflexion Loop (Critic Feedback) */}
                    {values.critic_feedback && (
                      <div className="mb-4">
                        <span className="text-[10px] text-amber-400 font-bold font-mono flex items-center gap-1 mb-1">
                          <Brain className="w-3.5 h-3.5 text-amber-400 animate-pulse" /> REFLEXION CRITIC REVIEW
                        </span>
                        <p className="text-xs text-amber-200/90 leading-relaxed bg-amber-400/5 p-3 rounded-lg border border-amber-400/20 font-sans font-medium">
                          {values.critic_feedback}
                        </p>
                      </div>
                    )}

                    {/* Scraped News Section */}
                    {values.news_headlines && values.news_headlines.length > 0 && (
                      <div className="mb-4">
                        <span className="text-[10px] text-gray-400 font-mono block mb-1">LATEST NEWS PARSED</span>
                        <div className="max-h-[85px] overflow-y-auto space-y-1.5 pr-1.5 custom-scrollbar">
                          {values.news_headlines.map((h, i) => (
                            <div key={i} className="text-[10px] text-gray-400 leading-snug bg-white/2 p-1.5 px-2.5 rounded border border-white/2 hover:border-white/5 flex gap-1.5 items-start">
                              <Newspaper className="w-3.5 h-3.5 text-accent shrink-0 mt-0.5" />
                              <span className="line-clamp-2">{h}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Feedback Messages */}
                  {actionMessage && (
                    <div className={`p-3 rounded-lg text-xs font-medium border text-center transition-all ${
                      actionMessage.type === 'success' 
                        ? 'bg-green-500/10 border-green-500/30 text-green-400' 
                        : 'bg-anomaly/10 border-anomaly/30 text-anomaly'
                    }`}>
                      {actionMessage.text}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <button
                      onClick={handleReject}
                      disabled={actionLoading}
                      className="group py-2.5 px-4 rounded-xl border border-white/10 hover:border-anomaly/40 bg-white/2 hover:bg-anomaly/5 text-gray-300 hover:text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
                    >
                      <ThumbsDown className="w-4 h-4 group-hover:scale-110 transition-transform" />
                      REJECT
                    </button>
                    <button
                      onClick={handleApprove}
                      disabled={actionLoading}
                      className="group py-2.5 px-4 rounded-xl bg-green-500 hover:bg-green-400 text-dark font-black text-xs flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-green-500/20 cursor-pointer disabled:opacity-50"
                    >
                      <ThumbsUp className="w-4 h-4 group-hover:scale-110 transition-transform" />
                      {actionLoading ? "PROCESSING..." : "APPROVE"}
                    </button>
                  </div>
                </div>
              ) : (
                /* Scenario B: Agent is idle or monitoring normal ticks */
                <div className="flex-1 flex flex-col justify-between py-4">
                  <div className="text-center py-6">
                    <div className="relative inline-block mb-3">
                      <div className="w-12 h-12 rounded-full border border-accent/20 bg-accent/5 flex items-center justify-center mx-auto shadow-inner">
                        <Activity className="w-6 h-6 text-accent animate-pulse" />
                      </div>
                      <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-[#0b0e14] rounded-full animate-pulse" />
                    </div>
                    <h4 className="text-sm font-bold text-white tracking-wide">Neural Monitoring Active</h4>
                    <p className="text-xs text-gray-400 max-w-[250px] mx-auto mt-2 leading-relaxed">
                      Ajan ağı, {symbol} senedini canlı olarak tarıyor. Anomaliler veya kritik piyasa olayları oluştuğunda işlem teklifi üreterek onayınızı isteyecektir.
                    </p>
                  </div>

                  <div className="space-y-3 bg-white/2 border border-white/5 rounded-xl p-4 font-mono text-xs">
                    <div className="flex justify-between items-center text-gray-400">
                      <span>MONITOR TICKET:</span>
                      <span className="text-white font-bold">{symbol}</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-400">
                      <span>CURRENT PRICE:</span>
                      <span className="text-white font-bold">${latestPrice.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-400">
                      <span>STATE RETRIEVAL:</span>
                      <span className="text-green-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-ping" /> HEALTHY</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Historical Decision Feed */}
          <div className="glass flex-1 overflow-hidden flex flex-col min-h-[300px] border-white/5">
            <div className="p-4 border-b border-white/5 bg-white/2 flex justify-between items-center">
              <h3 className="font-semibold flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-accent" /> Agent Decision Log
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar max-h-[350px]">
              {trades.length === 0 && (
                <div className="text-center py-20 text-gray-500 italic text-xs">
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

// Sub-component for pipeline steps
interface PipelineStepProps {
  stepNum: number;
  title: string;
  desc: string;
  isActive: boolean;
  isCompleted: boolean;
  isAlert?: boolean;
}

const PipelineStep = ({ stepNum, title, desc, isActive, isCompleted, isAlert }: PipelineStepProps) => {
  return (
    <div className="flex flex-col items-center text-center relative z-10">
      <div className={`w-11 h-11 rounded-full flex items-center justify-center transition-all duration-500 border ${
        isCompleted 
          ? "bg-green-500/25 border-green-500 text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.2)]" 
          : isActive && isAlert
          ? "bg-anomaly/20 border-anomaly text-anomaly animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.4)]"
          : isActive 
          ? "bg-accent/20 border-accent text-accent animate-pulse shadow-[0_0_15px_rgba(0,209,255,0.3)]" 
          : "bg-[#161925] border-white/10 text-gray-500"
      }`}>
        {isCompleted ? (
          <CheckCircle2 className="w-5 h-5" />
        ) : isActive && isAlert ? (
          <UserCheck className="w-5 h-5" />
        ) : isActive ? (
          <Clock className="w-5 h-5" />
        ) : (
          <span className="font-mono font-bold text-xs">{stepNum}</span>
        )}
      </div>
      <h4 className={`text-xs font-bold mt-3 transition-colors ${
        isActive ? "text-white" : isCompleted ? "text-gray-300" : "text-gray-500"
      }`}>
        {title}
      </h4>
      <p className={`text-[9px] mt-0.5 max-w-[90px] leading-tight transition-colors ${
        isActive ? "text-accent" : "text-gray-500"
      }`}>
        {desc}
      </p>
    </div>
  );
};

// Sub-component for individual stat cards
interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  sub: string;
  subColor?: string;
  glow?: boolean;
}

const StatCard = ({ label, value, icon, sub, subColor = "text-gray-400", glow = false }: StatCardProps) => (
  <div className={`glass p-5 flex flex-col gap-2 transition-all duration-300 ${
    glow ? "border-anomaly/40 shadow-[0_0_15px_rgba(239,68,68,0.15)]" : "border-white/5"
  }`}>
    <div className="flex justify-between items-start">
      <span className="text-xs font-medium text-gray-400 font-mono tracking-wider">{label}</span>
      <div className="p-2 bg-white/5 rounded-lg border border-white/5">{icon}</div>
    </div>
    <div className="text-3xl font-black font-mono tracking-tight">{value}</div>
    <div className={`text-xs ${subColor}`}>{sub}</div>
  </div>
);

// Sub-component for rendering decision cards
const DecisionCard = ({ trade }: { trade: Trade }) => (
  <div className="p-4 rounded-xl bg-white/2 border border-white/5 hover:border-accent/30 transition-all duration-300 shadow-md">
    <div className="flex justify-between items-center mb-3">
      <span className={`px-2.5 py-0.5 rounded text-[10px] font-black tracking-widest ${
        trade.action === "BUY" ? "bg-green-500/20 text-green-400 border border-green-500/30" : 
        trade.action === "SELL" ? "bg-anomaly/20 text-anomaly border border-anomaly/30" : 
        "bg-white/5 text-gray-400 border border-white/10"
      }`}>
        {trade.action}
      </span>
      <span className="text-[9px] text-gray-500 font-mono">
        {new Date(trade.timestamp).toLocaleTimeString()}
      </span>
    </div>
    <p className="text-xs leading-relaxed text-gray-300 font-sans">
      {trade.reasoning}
    </p>
    <div className="mt-3 pt-3 border-t border-white/5 flex justify-between items-center">
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
        <span className="text-[10px] text-gray-400 font-mono font-medium">Risk Score: {trade.risk_score}</span>
      </div>
      {trade.action !== "HOLD" && (
        <ArrowUpRight className={`w-4 h-4 ${trade.action === "BUY" ? "text-green-400" : "text-anomaly"}`} />
      )}
    </div>
  </div>
);

export default App;
