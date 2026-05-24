import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { DEMO_PROFILES, useUserProfile } from "./lib/useUserProfile";
import ChatInterface from "./components/ChatInterface";
import FullBenchmark from "./components/FullBenchmark";
import EnterpriseUnseenBenchmark from "./components/EnterpriseUnseenBenchmark";
import AdminDashboard from "./components/AdminDashboard";
import LiveDashboard from "./components/LiveDashboards/LiveDashboard";

type View = "chat" | "operations" | "fullbenchmark" | "enterpriseunseen" | "dashboard";

export default function App() {
  const [view, setView] = useState<View>("chat");
  const [activeUserId, setActiveUserId] = useState<string>(DEMO_PROFILES[0].uid);
  const { profile } = useUserProfile(activeUserId);

  const activeUser = {
    uid: profile.uid,
    email: profile.email,
    displayName: profile.displayName,
    photoURL: profile.photoURL ?? null,
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <AnimatePresence mode="wait">
        <motion.div
          key={view}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.15 }}
          className="h-screen flex flex-col"
        >
          {view === "enterpriseunseen" ? (
            <EnterpriseUnseenBenchmark onBack={() => setView("chat")} />
          ) : view === "fullbenchmark" ? (
            <FullBenchmark onBack={() => setView("chat")} />
          ) : view === "operations" ? (
            <AdminDashboard
              profile={profile!}
              onBack={() => setView("chat")}
              onOpenBenchmark={() => setView("fullbenchmark")}
            />
          ) : view === "dashboard" ? (
            <LiveDashboard />
          ) : (
            <ChatInterface
              user={activeUser}
              profile={profile!}
              onOpenAdmin={() => setView("operations")}
              onSwitchPersona={setActiveUserId}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {view === "chat" && (
        <div className="fixed bottom-6 right-6 flex flex-col items-end gap-2 z-50">
          <button
            onClick={() => setView("enterpriseunseen")}
            className="bg-emerald-600 text-white text-xs px-3 py-2 rounded-full shadow-lg hover:bg-emerald-500 transition-colors"
          >
            Enterprise Unseen (5,000)
          </button>
          <button
            onClick={() => setView("enterpriseunseen")}
            className="bg-emerald-600 text-white text-xs px-3 py-2 rounded-full shadow-lg hover:bg-emerald-500 transition-colors"
          >
            Enterprise Unseen (5,000)
          </button>
          <button
            onClick={() => setView("fullbenchmark")}
            className="bg-slate-800 text-white text-xs px-3 py-2 rounded-full shadow-lg hover:bg-slate-700 transition-colors"
          >
            Balanced Benchmark (7,000)
          </button>
          <button
            onClick={() => setView("dashboard")}
            className="bg-purple-600 text-white text-xs px-3 py-2 rounded-full shadow-lg hover:bg-purple-500 transition-colors"
          >
            Live Dashboard
          </button>
        </div>
      )}
    </div>
  );
}
