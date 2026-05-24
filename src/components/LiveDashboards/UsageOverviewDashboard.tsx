// src/components/LiveDashboards/UsageOverviewDashboard.tsx
import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import "chart.js/auto";

interface Metrics {
  sessions: number;
  activeUsers: number;
  topQueries: string[];
}

export default function UsageOverviewDashboard() {
  const [metrics, setMetrics] = useState<Metrics>({ sessions: 0, activeUsers: 0, topQueries: [] });

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("/api/metrics/usage");
      const data = await res.json();
      setMetrics(data);
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: ["Sessions", "Active Users"],
    datasets: [
      {
        label: "Counts",
        data: [metrics.sessions, metrics.activeUsers],
        backgroundColor: ["rgba(59,130,246,0.7)", "rgba(236,72,153,0.7)"],
        borderColor: ["rgba(59,130,246,1)", "rgba(236,72,153,1)"],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="p-6 bg-white rounded-2xl shadow-lg glassmorphism">
      <h2 className="text-xl font-bold mb-4 text-slate-800">Conversation & Usage Overview</h2>
      <Bar data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
      <div className="mt-4 text-sm text-slate-600">
        <strong>Top Queries:</strong> {metrics.topQueries.join(", ")}
      </div>
    </div>
  );
}
