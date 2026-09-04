import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { socService } from '../services/socService';

export function useCityRisk() {
  const { cityRisk } = useWebSocket();
  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const data = await socService.getCityRisk();
        if (mounted) setDetails(data);
      } catch (err) {
        console.warn('Failed to load full city risk breakdown:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const getRiskTier = (score: number) => {
    if (score >= 80) return { label: 'CRITICAL', color: 'text-rose-500', bg: 'bg-rose-500/20', border: 'border-rose-500/40' };
    if (score >= 60) return { label: 'HIGH', color: 'text-amber-500', bg: 'bg-amber-500/20', border: 'border-amber-500/40' };
    if (score >= 40) return { label: 'ELEVATED', color: 'text-yellow-400', bg: 'bg-yellow-400/20', border: 'border-yellow-400/40' };
    return { label: 'NORMAL', color: 'text-emerald-400', bg: 'bg-emerald-400/20', border: 'border-emerald-400/40' };
  };

  return {
    score: cityRisk,
    tier: getRiskTier(cityRisk),
    details,
    loading,
  };
}
