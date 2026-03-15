import * as React from 'react';
import type { ThemeMode } from '../types/widget';

interface ThemeToggleProps {
  themeMode: ThemeMode;
  onToggle: () => void;
}

const modeIcons: Record<ThemeMode, React.ReactNode> = {
  light: (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  ),
  dark: (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  ),
  auto: (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
    </svg>
  ),
};

const modeDescriptions: Record<ThemeMode, string> = {
  light: 'Light theme',
  dark: 'Dark theme',
  auto: 'Auto (follows system)',
};

export function ThemeToggle({ themeMode, onToggle }: ThemeToggleProps) {
  const ariaLabel = `Theme: ${modeDescriptions[themeMode]}. Click to change.`;
  
  return (
    <button
      type="button"
      onClick={onToggle}
      className="shopbot-theme-toggle"
      aria-label={ariaLabel}
      title={modeDescriptions[themeMode]}
    >
      {modeIcons[themeMode]}
    </button>
  );
}

export function getNextThemeMode(current: ThemeMode): ThemeMode {
  const cycle: ThemeMode[] = ['light', 'dark', 'auto'];
  const currentIndex = cycle.indexOf(current);
  const nextIndex = (currentIndex + 1) % cycle.length;
  return cycle[nextIndex];
}
