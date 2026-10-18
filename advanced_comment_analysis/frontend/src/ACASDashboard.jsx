import React, { useState } from 'react';
import * as Icons from 'lucide-react';

const ACASDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  // Shared UI Components
  const Card = ({ children, className = "" }) => (
    <div className={`p-6 rounded-xl border border-gray-800 bg-[#1A1A1A] ${className}`}>
      {children}
    </div>
  );

  const getIcon = (IconName, props) => {
    const Icon = Icons[IconName];
    return Icon ? <Icon {...props} /> : null;
  }

  // --- TAB: DASHBOARD (Home View) ---
  const DashboardView = () => {
    const kpis = [
      { title: "Analyzed (24h)", value: "142.5k", change: "+12%", icon: 'MessageSquare', color: "text-blue-400" },
      { title: "Crisis Alerts", value: "24", change: "-5", icon: 'AlertOctagon', color: "text-red-500", highlight: true },
      { title: "Avg. Confidence", value: "94.2%", change: "+0.8%", icon: 'BrainCircuit', color: "text-purple-400" },
      { title: "Noise Filtered", value: "38.1%", change: "+2.1%", icon: 'ShieldCheck', color: "text-emerald-400" }
    ];

    const liveQueue = [
      { id: "TKT-8992", user: "@dev_alex", comment: "Oh great, another UI update nobody asked for while the core API still crashes every Tuesday. Brilliant work team. 🙄", emotion: "Sarcasm", intent: "Product / Tech", confidence: 96, status: "Immediate Intervention", time: "2m ago" },
      { id: "TKT-8993", user: "Sarah Jenkins", comment: "I've been trying to reset my password for 3 days. I am locked out of my entire enterprise account. Please help NOW.", emotion: "Frustration", intent: "Support", confidence: 98, status: "High Priority", time: "5m ago" },
      { id: "TKT-8994", user: "CryptoKing99", comment: "Click here to win 5000 free coins instantly!!! [link]", emotion: "Spam", intent: "Noise", confidence: 99, status: "Filtered", time: "12m ago" }
    ];

    return (
      <div className="space-y-8 animate-in fade-in duration-500">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis.map((kpi, index) => (
            <div key={index} className={`p-6 rounded-xl border ${kpi.highlight ? 'border-red-500/50 bg-red-500/5' : 'border-gray-800 bg-[#1A1A1A]'} relative overflow-hidden`}>
              <div className="flex justify-between items-start mb-4">
                <div className={`p-2 rounded-lg bg-gray-800/50 ${kpi.color}`}>{getIcon(kpi.icon, {size:20})}</div>
                <span className={`text-xs font-bold ${kpi.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>{kpi.change}</span>
              </div>
              <h3 className="text-gray-400 text-sm font-medium">{kpi.title}</h3>
              <p className="text-3xl font-bold mt-1">{kpi.value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">{getIcon('Zap',{size:18, className:'text-red-500'})} Priority Triage Queue</h3>
            <div className="space-y-4">
              {liveQueue.map((item, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-[#242424] border border-gray-800 flex justify-between items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm text-gray-200">{item.user}</span>
                      <span className="text-[10px] text-gray-500 uppercase">{item.time}</span>
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-1">{item.comment}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-500 border border-red-500/20">{item.emotion}</span>
                    <p className="text-[10px] text-gray-500 mt-1">{item.confidence}% Conf.</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <h3 className="text-lg font-semibold mb-6">Sentiment Mix</h3>
            <div className="space-y-4">
               {[
                 { label: "Positive", val: 65, color: "bg-emerald-500" },
                 { label: "Neutral", val: 20, color: "bg-gray-500" },
                 { label: "Negative", val: 15, color: "bg-red-500" }
               ].map((s, i) => (
                 <div key={i}>
                   <div className="flex justify-between text-xs text-gray-400 mb-1"><span>{s.label}</span><span>{s.val}%</span></div>
                   <div className="h-1.5 w-full bg-gray-800 rounded-full"><div className={`h-full rounded-full ${s.color}`} style={{width: `${s.val}%`}}></div></div>
                 </div>
               ))}
            </div>
          </Card>
        </div>
      </div>
    );
  };

  // --- TAB: ROUTING ---
  const RoutingView = () => (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <div className="flex justify-between items-center mb-8">
          <div>
            <h3 className="text-xl font-bold">Auto-Routing Logic</h3>
            <p className="text-sm text-gray-500">How ACAS distributes tickets across your stack</p>
          </div>
          <button className="bg-red-600 px-4 py-2 rounded-lg text-sm font-bold">Edit Rules</button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { name: "Support Queue", icon: 'MessageSquare', color: "border-blue-500", desc: "General inquiries and account issues.", load: "78.3k" },
            { name: "Tech / Bugs", icon: 'Server', color: "border-purple-500", desc: "API errors, crashes, and performance logs.", load: "42.7k" },
            { name: "Product / Feedback", icon: 'Zap', color: "border-emerald-500", desc: "Feature requests and UX suggestions.", load: "21.3k" }
          ].map((item, i) => (
            <div key={i} className={`p-6 rounded-xl border-2 ${item.color} bg-gray-800/20 flex flex-col items-center text-center`}>
              {getIcon(item.icon, {className: 'mb-4 opacity-80', size:32})}
              <h4 className="font-bold text-lg mb-2">{item.name}</h4>
              <p className="text-xs text-gray-500 mb-6">{item.desc}</p>
              <div className="mt-auto w-full">
                <div className="text-2xl font-mono font-bold">{item.load}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-widest">Total Routed</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

  // --- rest omitted for brevity in this message (unchanged) ---

  return (
    <div className="min-h-screen bg-[#121212] text-white font-sans flex flex-col md:flex-row">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 bg-[#1A1A1A] border-r border-gray-800 flex flex-col shrink-0">
        <div className="p-6 flex items-center gap-3 border-b border-gray-800">
          <div className="w-8 h-8 rounded bg-red-600 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(220,38,38,0.5)]">
            A
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wider">ACAS</h1>
            <p className="text-xs text-gray-500 uppercase tracking-widest">Intelligence</p>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {[
            { id: 'dashboard', icon: 'LayoutDashboard', label: 'Live Dashboard' },
            { id: 'routing', icon: 'GitMerge', label: 'Auto-Routing' },
            { id: 'emotions', icon: 'BrainCircuit', label: 'Sentic Mapping' },
            { id: 'performance', icon: 'Activity', label: 'System Health' },
            { id: 'settings', icon: 'Settings', label: 'Configuration' }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                activeTab === item.id 
                  ? 'bg-red-500/10 text-red-500 border border-red-500/20' 
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}>
              {getIcon(item.icon, {size:18})}
              <span className="font-medium text-sm">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-6 border-t border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-700"></div>
            <div>
              <p className="text-sm font-medium">Admin User</p>
              <p className="text-xs text-green-500 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500 block animate-pulse"></span> System Online
              </p>
            </div>
          </div>
        </div>
      </aside>
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <header className="h-20 border-b border-gray-800 bg-[#1A1A1A]/50 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
          <div>
            <h2 className="text-2xl font-semibold capitalize">{activeTab.replace('-', ' ')}</h2>
            <p className="text-sm text-gray-400">Advanced Comment Analysis Platform</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="relative hidden md:block">
              <input type="text" placeholder="Search triage logs..." className="bg-[#242424] border border-gray-700 text-sm rounded-full pl-10 pr-4 py-2 w-64 focus:outline-none focus:border-red-500 transition-colors" />
            </div>
            <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
              {getIcon('Bell', {size:20})}
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#1A1A1A]"></span>
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-8 bg-[#121212]">
          {activeTab === 'dashboard' && <DashboardView />}
          {activeTab === 'routing' && <RoutingView />}
          {/* other tabs omitted for brevity */}
        </div>
      </main>
    </div>
  );
};

export default ACASDashboard;
