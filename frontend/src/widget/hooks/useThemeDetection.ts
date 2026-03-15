import * as React from 'react';

type SystemTheme = 'light' | 'dark';

interface ThemeDetectionResult {
  systemTheme: SystemTheme;
  isDark: boolean;
}

export function useThemeDetection(): ThemeDetectionResult {
  const [systemTheme, setSystemTheme] = React.useState<SystemTheme>(() => {
    if (typeof window === 'undefined') {
      return 'light';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  React.useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return {
    systemTheme,
    isDark: systemTheme === 'dark',
  };
}
