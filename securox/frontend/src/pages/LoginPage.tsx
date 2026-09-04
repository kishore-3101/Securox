import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  Shield,
  Stethoscope,
  Ambulance,
  Car,
  Landmark,
  Eye,
  KeyRound,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, switchRole } = useAuth();

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const personas = [
    {
      id: 'admin',
      name: 'Global CISO / SOC Administrator',
      role: 'admin',
      sector: 'Pan-City Infrastructure',
      icon: Shield,
      path: '/',
      color: 'text-sky-400 border-sky-500/30 hover:border-sky-500/60 bg-sky-950/20',
    },
    {
      id: 'doctor',
      name: 'Dr. Sarah Chen (Cardiologist)',
      role: 'doctor',
      sector: 'Clinical Healthcare & ICU',
      icon: Stethoscope,
      path: '/doctor',
      color: 'text-emerald-400 border-emerald-500/30 hover:border-emerald-500/60 bg-emerald-950/20',
    },
    {
      id: 'ambulance',
      name: 'Mobile ALS Unit CAD-04',
      role: 'ambulance_driver',
      sector: 'Emergency Dispatch & Triage',
      icon: Ambulance,
      path: '/ambulance',
      color: 'text-rose-400 border-rose-500/30 hover:border-rose-500/60 bg-rose-950/20',
    },
    {
      id: 'traffic',
      name: 'Inspector Rajesh (Traffic Ops)',
      role: 'traffic_operator',
      sector: 'Bangalore Corridor Signals',
      icon: Car,
      path: '/traffic',
      color: 'text-cyan-400 border-cyan-500/30 hover:border-cyan-500/60 bg-cyan-950/20',
    },
    {
      id: 'finance',
      name: 'Treasury & AML Investigator',
      role: 'finance_investigator',
      sector: 'Fintech, Wire Escrow & AML',
      icon: Landmark,
      path: '/finance',
      color: 'text-amber-400 border-amber-500/30 hover:border-amber-500/60 bg-amber-950/20',
    },
    {
      id: 'viewer',
      name: 'Public Infrastructure Auditor',
      role: 'viewer',
      sector: 'Read-Only Transparency',
      icon: Eye,
      path: '/',
      color: 'text-slate-300 border-slate-700 hover:border-slate-500 bg-slate-900/40',
    },
  ];

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFastPersonaLogin = async (persona: typeof personas[0]) => {
    setLoading(true);
    setError(null);
    try {
      await switchRole(persona.role || persona.id);
      navigate(persona.path);
    } catch (err: any) {
      setError(err.message || 'Failed to switch persona');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 relative font-sans">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl w-full space-y-8 z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Cyber-Physical Protection Platform</span>
          </div>
          <h1 className="text-3xl font-extrabold font-mono tracking-wider text-slate-100">
            SECUROX ENTERPRISE
          </h1>
          <p className="text-xs font-mono text-slate-400 max-w-md mx-auto">
            Zero-Trust Authorization, Dynamic ABAC Policy Enforcement & AI Multi-Sector Resilience
          </p>
        </div>

        {error && (
          <div className="max-w-md mx-auto p-3 rounded-lg bg-rose-950/50 border border-rose-500/50 text-rose-300 text-xs font-mono text-center">
            {error}
          </div>
        )}

        {/* 1-Click Interactive Persona Selector */}
        <div className="space-y-3">
          <div className="text-center">
            <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
              1-Click Interactive Evaluator Personas
            </span>
            <p className="text-[11px] font-mono text-slate-500 mt-0.5">
              Instantly switch role boundaries, permissions, and landing pages
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {personas.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.id}
                  onClick={() => handleFastPersonaLogin(p)}
                  disabled={loading}
                  className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.02] shadow-lg flex flex-col justify-between ${p.color}`}
                >
                  <div className="flex items-start justify-between w-full mb-3">
                    <div className="p-2 rounded-lg bg-slate-950/80 border border-white/10">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/40 border border-white/10 font-bold uppercase">
                      {p.role}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-xs font-mono font-bold text-slate-100">{p.name}</h3>
                    <p className="text-[11px] font-mono text-slate-400 mt-0.5">{p.sector}</p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-mono opacity-80">
                    <span>Enter Portal</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Manual Credentials Form */}
        <div className="max-w-md mx-auto bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <KeyRound className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Manual System Authentication
            </h3>
          </div>

          <form onSubmit={handleManualLogin} className="space-y-3 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">USERNAME</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-sky-500"
                required
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">PASSWORD</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-sky-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold transition shadow-lg disabled:opacity-50 mt-2"
            >
              {loading ? 'Authenticating...' : 'Sign In with Credentials'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
export default LoginPage;
