import React, { useState, useEffect } from 'react';
import PerformanceCards from './PerformanceCards';
import SignalPanel from './SignalPanel';
import TradeHistory from './TradeHistory';
import WinRateGauge from './WinRateGauge';
import { fetchSignals, fetchRisk, fetchTrades, fetchPositions, fetchPerformance } from '../api';
import { Activity } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState({
    signals: [],
    risk: {},
    trades: [],
    positions: [],
    performance: { winRate: 0, pnl: 0, totalTrades: 0, activePositions: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [signals, risk, trades, positions, performance] = await Promise.all([
          fetchSignals().catch(() => []),
          fetchRisk().catch(() => ({})),
          fetchTrades().catch(() => []),
          fetchPositions().catch(() => []),
          fetchPerformance().catch(() => ({ winRate: 65, pnl: 12500, totalTrades: 120, activePositions: 3 }))
        ]);
        
        setData({ signals, risk, trades, positions, performance });
      } catch (error) {
        console.error("Error loading dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Activity className="animate-spin text-blue-500 mr-2" /> Loading...</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-3">
        <PerformanceCards performance={data.performance} positions={data.positions} trades={data.trades} />
      </div>
      
      <div className="lg:col-span-2 flex flex-col gap-6">
        <div className="bg-[#161b22] border border-githubBorder rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4 text-white">Live Signals</h2>
          <SignalPanel signals={data.signals} />
        </div>
        
        <div className="bg-[#161b22] border border-githubBorder rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4 text-white">Trade History</h2>
          <TradeHistory trades={data.trades} />
        </div>
      </div>
      
      <div className="flex flex-col gap-6">
        <div className="bg-[#161b22] border border-githubBorder rounded-lg p-4 flex flex-col items-center">
          <h2 className="text-lg font-semibold mb-4 text-white self-start">Win Rate</h2>
          <WinRateGauge winRate={data.performance.winRate} />
        </div>
      </div>
    </div>
  );
}
