"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";

export function MiniTrendChart({ data, color = "#10b981", className = "" }) {
  // Generate sample trend data if none provided
  const chartData = data || [
    { value: 65 },
    { value: 68 },
    { value: 72 },
    { value: 69 },
    { value: 75 },
    { value: 78 },
    { value: 82 },
  ];

  return (
    <div className={`h-8 w-16 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MiniSparkline({ data, color = "#10b981" }) {
  const chartData =
    data ||
    Array.from({ length: 12 }, (_, i) => ({
      value: Math.floor(Math.random() * 40) + 60,
    }));

  return (
    <div className="h-6 w-20">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            activeDot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
