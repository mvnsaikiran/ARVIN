// src/components/LiveDashboards/LiveDashboard.tsx
import React, { useState } from "react";
import PolicyResolutionMatrix from "./PolicyResolutionMatrix";
import UserExperienceDashboard from "./UserExperienceDashboard";
import UsageOverviewDashboard from "./UsageOverviewDashboard";

const tabs = [
  { id: "policy", label: "Policy‑Resolution Matrix" },
  { id: "experience", label: "User Experience & Satisfaction" },
  { id: "usage", label: "Conversation & Usage Overview" },
] as const;

type TabId = typeof tabs[number]["id"]; 

export default function LiveDashboard() {
  const [activeTab, setActiveTab] = useState<TabId>("policy");

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white glassmorphism">
      <h1 className="text-2xl font-bold mb-4 text-center">Live Dashboard</h1>
      <div className="flex justify-center mb-6 space-x-4">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 rounded transition-colors ${
              activeTab === t.id ? "bg-purple-600" : "bg-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="space-y-8">
        {activeTab === "policy" && <PolicyResolutionMatrix />}
        {activeTab === "experience" && <UserExperienceDashboard />}
        {activeTab === "usage" && <UsageOverviewDashboard />}
      </div>
    </div>
  );
}
