import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle, getNextThemeMode } from './ThemeToggle';
import type { ThemeMode } from '../types/widget';

describe('ThemeToggle', () => {
  it('renders sun icon for light mode', () => {
    render(<ThemeToggle themeMode="light" onToggle={vi.fn()} />);
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Light theme'));
  });

  it('renders moon icon for dark mode', () => {
    render(<ThemeToggle themeMode="dark" onToggle={vi.fn()} />);
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Dark theme'));
  });

  it('renders auto icon for auto mode', () => {
    render(<ThemeToggle themeMode="auto" onToggle={vi.fn()} />);
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Auto'));
  });

  it('cycles modes on click', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle themeMode="light" onToggle={onToggle} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('has correct aria-label with current mode', () => {
    render(<ThemeToggle themeMode="dark" onToggle={vi.fn()} />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Theme: Dark theme. Click to change.');
  });

  it('has correct title attribute', () => {
    render(<ThemeToggle themeMode="auto" onToggle={vi.fn()} />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Auto (follows system)');
  });
});

describe('getNextThemeMode', () => {
  it('cycles from light to dark', () => {
    expect(getNextThemeMode('light')).toBe('dark');
  });

  it('cycles from dark to auto', () => {
    expect(getNextThemeMode('dark')).toBe('auto');
  });

  it('cycles from auto to light', () => {
    expect(getNextThemeMode('auto')).toBe('light');
  });

  it('returns valid ThemeMode for all inputs', () => {
    const modes: ThemeMode[] = ['light', 'dark', 'auto'];
    modes.forEach(mode => {
      const next = getNextThemeMode(mode);
      expect(['light', 'dark', 'auto']).toContain(next);
    });
  });
});
