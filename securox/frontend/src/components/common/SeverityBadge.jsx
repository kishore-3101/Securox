import React from 'react';

export const SeverityBadge = ({ severity = 'INFO', text = null }) => {
  const sev = (severity || 'INFO').toUpperCase();
  const label = text || sev;

  const getClassName = () => {
    switch (sev) {
      case 'CRITICAL': return 'badge badge-critical';
      case 'HIGH': return 'badge badge-high';
      case 'MEDIUM': return 'badge badge-medium';
      case 'LOW':
      case 'INFO': return 'badge badge-low';
      case 'SUCCESS':
      case 'RESOLVED':
      case 'ONLINE': return 'badge badge-success';
      default: return 'badge badge-info';
    }
  };

  return (
    <span className={getClassName()}>
      {label}
    </span>
  );
};
