import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const KpiCard = ({ title, value, unit, trend, comparison, severity = 'INFO', icon: Icon, onClick }) => {
  const isPositive = trend && trend.startsWith('+');
  const isNegative = trend && trend.startsWith('-');

  return (
    <div 
      className={`kpi-card severity-${severity.toLowerCase()}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div className="kpi-label">
        <span>{title}</span>
        {Icon && <Icon size={16} color="var(--text-dim)" />}
      </div>
      <div className="kpi-value-row">
        <span className="kpi-value">{value}</span>
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      <div className="kpi-meta">
        {trend && (
          <span style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '2px', 
            color: isNegative ? '#34d399' : (isPositive ? '#f87171' : 'var(--text-dim)'),
            fontWeight: 600
          }}>
            {isPositive && <TrendingUp size={12} />}
            {isNegative && <TrendingDown size={12} />}
            {!isPositive && !isNegative && <Minus size={12} />}
            {trend}
          </span>
        )}
        {comparison && <span>{comparison}</span>}
      </div>
    </div>
  );
};
