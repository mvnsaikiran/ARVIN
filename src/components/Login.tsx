import { auth } from '../lib/firebase';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { LogIn } from 'lucide-react';
import { motion } from 'motion/react';

export default function Login() {
  const handleLogin = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm"
      >
        <div className="mb-8 text-center">
          <div className="flex justify-center mb-6">
            <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-100">
              <LogIn className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900 mb-2">Arvind HR Pulse</h1>
          <p className="text-slate-500 text-sm">Enterprise HR Intelligence</p>
        </div>

        <button
          onClick={handleLogin}
          id="google-login-btn"
          className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-slate-200 rounded-xl bg-white text-slate-700 font-medium hover:bg-slate-50 transition-colors shadow-sm"
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
          Continue with Employee Account
        </button>

        <p className="mt-8 text-center text-xs text-slate-400 leading-relaxed uppercase tracking-widest">
          Secure Internal Access Only
        </p>
      </motion.div>
    </div>
  );
}
