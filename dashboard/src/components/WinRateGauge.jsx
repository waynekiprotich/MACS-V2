import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

export default function WinRateGauge({ winRate = 0 }) {
  const data = [
    { name: 'Win', value: winRate },
    { name: 'Loss', value: 100 - winRate },
  ];
  
  const COLORS = ['#3b82f6', '#30363d'];

  return (
    <div className="w-full h-48 relative flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            paddingAngle={0}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute flex flex-col items-center justify-center top-1/2 mt-2">
        <span className="text-3xl font-bold text-white">{winRate.toFixed(1)}%</span>
        <span className="text-xs text-gray-400">Win Rate</span>
      </div>
    </div>
  );
}
