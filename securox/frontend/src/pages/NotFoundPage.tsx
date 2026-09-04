import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 text-center font-mono">
      <ShieldAlert className="w-16 h-16 text-rose-500 mb-4 animate-bounce" />
      <h1 className="text-4xl font-bold tracking-wider mb-2">404 // NOT FOUND</h1>
      <p className="text-xs text-slate-400 max-w-sm mb-6">
        The requested endpoint or operational boundary does not exist in the Securox smart city grid.
      </p>
      <Link
        to="/"
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to SOC Command Center</span>
      </Link>
    </div>
  );
};
export default NotFoundPage;
