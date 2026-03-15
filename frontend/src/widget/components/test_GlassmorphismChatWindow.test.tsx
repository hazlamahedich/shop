import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { GlassmorphismChatWindow } from './GlassmorphismChatWindow';

describe('GlassmorphismChatWindow', () => {
  it('applies dark-mode class when activeTheme is dark', () => {
    const { container } = render(
      <GlassmorphismChatWindow themeMode="dark" systemTheme="light">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    const wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('dark-mode');
  });

  it('applies light-mode class when activeTheme is light', () => {
    const { container } = render(
      <GlassmorphismChatWindow themeMode="light" systemTheme="dark">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    const wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('light-mode');
  });

  it('uses systemTheme when mode is auto', () => {
    const { container, rerender } = render(
      <GlassmorphismChatWindow themeMode="auto" systemTheme="dark">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    let wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('dark-mode');
    
    rerender(
      <GlassmorphismChatWindow themeMode="auto" systemTheme="light">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('light-mode');
  });

  it('uses manual mode when mode is light or dark', () => {
    const { container, rerender } = render(
      <GlassmorphismChatWindow themeMode="dark" systemTheme="light">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    let wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('dark-mode');
    
    rerender(
      <GlassmorphismChatWindow themeMode="light" systemTheme="dark">
        <div>Content</div>
      </GlassmorphismChatWindow>
    );
    
    wrapper = container.querySelector('.glassmorphism-wrapper');
    expect(wrapper).toHaveClass('light-mode');
  });

  it('renders children', () => {
    const { getByText } = render(
      <GlassmorphismChatWindow themeMode="auto" systemTheme="light">
        <div>Test Content</div>
      </GlassmorphismChatWindow>
    );
    
    expect(getByText('Test Content')).toBeInTheDocument();
  });
});
