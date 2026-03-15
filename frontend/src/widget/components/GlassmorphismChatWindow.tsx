import * as React from 'react';
import type { ThemeMode } from '../types/widget';

interface GlassmorphismChatWindowProps {
  themeMode: ThemeMode;
  systemTheme: 'light' | 'dark';
  children: React.ReactNode;
}

export function GlassmorphismChatWindow({
  themeMode,
  systemTheme,
  children,
}: GlassmorphismChatWindowProps) {
  const activeTheme = themeMode === 'auto' ? systemTheme : themeMode;
  
  return (
    <div className={`glassmorphism-wrapper ${activeTheme}-mode`}>
      {children}
    </div>
  );
}
