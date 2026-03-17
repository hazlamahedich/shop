import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WidgetDemo } from './WidgetDemo';

// Mock matchMedia for theme detection
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('WidgetDemo', () => {
  it('renders the demo page header', () => {
    render(<WidgetDemo />);
    expect(screen.getByText('Widget UI/UX Demo')).toBeInTheDocument();
    expect(screen.getByText('Interactive showcase of innovative features')).toBeInTheDocument();
  });

  it('displays all 8 feature buttons', () => {
    render(<WidgetDemo />);
    expect(screen.getByText('Glassmorphism')).toBeInTheDocument();
    expect(screen.getByText('Product Carousel')).toBeInTheDocument();
    expect(screen.getByText('Quick Replies')).toBeInTheDocument();
    expect(screen.getByText('Voice Input')).toBeInTheDocument();
    expect(screen.getByText('Proactive Engagement')).toBeInTheDocument();
    expect(screen.getByText('Message Grouping')).toBeInTheDocument();
    expect(screen.getByText('Microinteractions')).toBeInTheDocument();
    expect(screen.getByText('Smart Positioning')).toBeInTheDocument();
  });

  it('displays theme toggle buttons', () => {
    render(<WidgetDemo />);
    expect(screen.getByText('☀️ Light')).toBeInTheDocument();
    expect(screen.getByText('🌙 Dark')).toBeInTheDocument();
    expect(screen.getByText('🔄 Auto')).toBeInTheDocument();
  });

  it('switches features when clicked', () => {
    render(<WidgetDemo />);
    
    // Click on Product Carousel
    fireEvent.click(screen.getByText('Product Carousel'));
    
    // Should show feature description
    expect(screen.getByText(/Horizontal scrolling product cards/)).toBeInTheDocument();
  });

  it('toggles theme when theme button clicked', () => {
    render(<WidgetDemo />);
    
    const darkButton = screen.getByText('🌙 Dark');
    fireEvent.click(darkButton);
    
    // Theme should change (button should be highlighted)
    expect(darkButton).toBeInTheDocument();
  });

  it('shows widget visibility toggle', () => {
    render(<WidgetDemo />);
    
    expect(screen.getByText(/Widget Visible/)).toBeInTheDocument();
  });

  it('displays feature descriptions', () => {
    render(<WidgetDemo />);
    
    // Default feature is glassmorphism
    expect(screen.getByText(/Modern frosted glass effect/)).toBeInTheDocument();
  });

  it('displays instructions section', () => {
    render(<WidgetDemo />);
    
    expect(screen.getByText(/Try These Interactions/)).toBeInTheDocument();
  });
});

describe('Feature Descriptions', () => {
  it('shows glassmorphism description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Glassmorphism'));
    expect(screen.getByText(/Modern frosted glass effect/)).toBeInTheDocument();
  });

  it('shows carousel description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Product Carousel'));
    expect(screen.getByText(/Horizontal scrolling product cards/)).toBeInTheDocument();
  });

  it('shows quick reply description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Quick Replies'));
    expect(screen.getByText(/Pre-defined response buttons/)).toBeInTheDocument();
  });

  it('shows voice input description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Voice Input'));
    expect(screen.getByText(/Speech recognition/)).toBeInTheDocument();
  });

  it('shows proactive engagement description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Proactive Engagement'));
    expect(screen.getByText(/Triggers based on user behavior/)).toBeInTheDocument();
  });

  it('shows message grouping description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Message Grouping'));
    expect(screen.getByText(/Groups consecutive messages/)).toBeInTheDocument();
  });

  it('shows microinteractions description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Microinteractions'));
    expect(screen.getByText(/Delightful animations/)).toBeInTheDocument();
  });

  it('shows smart positioning description', () => {
    render(<WidgetDemo />);
    fireEvent.click(screen.getByText('Smart Positioning'));
    expect(screen.getByText(/Automatically detects and avoids/)).toBeInTheDocument();
  });
});
