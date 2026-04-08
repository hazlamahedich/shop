import type { ThemeMode } from '../types/widget';

export interface LoadingSpinnerProps {
  themeMode?: ThemeMode;
}

export function LoadingSpinner({ themeMode }: LoadingSpinnerProps) {
  const isDark = themeMode === 'dark';

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
          border: `2px solid ${isDark ? 'rgba(255, 255, 255, 0.15)' : '#e5e7eb'}`,
          borderTopColor: isDark ? '#818cf8' : '#6366f1',
          borderRadius: '50%',
          animation: 'widget-spin 0.8s linear infinite',
        }}
      />
      <style>{`@keyframes widget-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
