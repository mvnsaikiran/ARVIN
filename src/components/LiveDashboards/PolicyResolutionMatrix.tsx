// src/components/LiveDashboards/PolicyResolutionMatrix.tsx
import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import "chart.js/auto";

interface Metrics {
  deterministic: number;
  llm: number;
}

export default function PolicyResolutionMatrix() {
  const [metrics, setMetrics] = useState<Metrics>({ deterministic: 0, llm: 0 });

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("/api/metrics/policy-resolution");
      const data = await res.json();
      setMetrics(data);
    };
    fetchData();
    const interval = setInterval(fetchData, 5000); // poll every 5s
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: ["Deterministic", "LLM"],
    datasets: [
      {
        label: "% of Answers",
        data: [metrics.deterministic, metrics.llm],
        backgroundColor: ["rgba(99,102,241,0.7)", "rgba(239,68,68,0.7)"],
        borderColor: ["rgba(99,102,241,1)", "rgba(239,68,68,1)"],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="p-6 bg-white rounded-2xl shadow-lg glassmorphism">
      <h2 className="text-xl font-bold mb-4 text-slate-800">Policy‑Resolution Matrix</h2>
      <Bar data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
    </div>
  );
}
