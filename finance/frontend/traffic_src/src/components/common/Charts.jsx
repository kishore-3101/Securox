import React from 'react';

export const Sparkline = ({ data = [40, 45, 52, 58, 65, 60, 72, 85, 78, 88], color = '#06b6d4', height = 36, width = 120 }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((val, idx) => {
    const x = (idx / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 6) - 3;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

export const MiniBarChart = ({ data = [25, 45, 60, 75, 40, 85, 90, 65, 45, 30], height = 48, color = '#06b6d4' }) => {
  const max = Math.max(...data, 100);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: `${height}px`, width: '100%' }}>
      {data.map((val, idx) => {
        const barHeight = Math.max(4, (val / max) * height);
        return (
          <div
            key={idx}
            style={{
              flex: 1,
              height: `${barHeight}px`,
              backgroundColor: val > 80 ? '#ef4444' : (val > 60 ? '#f59e0b' : color),
              borderRadius: '2px 2px 0 0',
              opacity: 0.85
            }}
            title={`Value: ${val}`}
          />
        );
      })}
    </div>
  );
};

export const DonutGauge = ({ value = 75, max = 100, size = 110, strokeWidth = 10, color = '#06b6d4', label = "Index" }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(1, Math.max(0, value / max));
  const strokeDashoffset = circumference - progress * circumference;

  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border-subtle)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff' }}>
          {value.toFixed(0)}
        </div>
        <div style={{ fontSize: '10px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
          {label}
        </div>
      </div>
    </div>
  );
};
