// src/components/LiveDashboards/UserExperienceDashboard.tsx
import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

interface Metrics {
  csat: number;
  nps: number;
  avgResponseMs: number;
  dropOffRate: number;
}

export default function UserExperienceDashboard() {
  const [metrics, setMetrics] = useState<Metrics>({ csat: 0, nps: 0, avgResponseMs: 0, dropOffRate: 0 });

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("/api/metrics/user-experience");
      const data = await res.json();
      setMetrics(data);
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: ["CSAT", "NPS", "Avg Resp (ms)", "Drop‑off %"],
    datasets: [
      {
        label: "Metrics",
        data: [metrics.csat, metrics.nps, metrics.avgResponseMs, metrics.dropOffRate],
        backgroundColor: "rgba(34,197,94,0.6)",
        borderColor: "rgba(34,197,94,1)",
        fill: true,
      },
    ],
  };

  return (
    <div className="p-6 bg-white rounded-2xl shadow-lg glassmorphism">
      <h2 className="text-xl font-bold mb-4 text-slate-800">User Experience &amp; Satisfaction</h2>
      <Line data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
    </div>
  );
}
