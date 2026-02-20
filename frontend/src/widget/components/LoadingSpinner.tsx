import * as React from 'react';

export function LoadingSpinner() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px',
        width: '100%',
        height: '100%',
        minHeight: '200px',
      }}
    >
      <div
        style={{
          width: '24px',
          height: '24px',
          border: '2px solid #e5e7eb',
          borderTopColor: '#6366f1',
          borderRadius: '50%',
          animation: 'widget-spin 0.8s linear infinite',
        }}
      />
      <style>{`@keyframes widget-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
