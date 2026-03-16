/**
 * General Mode Widgets Demo Page
 * Interactive showcase of chat and dashboard widgets for General Chatbot Mode
 * 
 * Route: /general-mode-demo
 * Access: Public (no auth required)
 */

import * as React from 'react';
import { styles } from '../components/demo/styles';
import { ChatWidgetsDemo } from '../components/demo/ChatWidgetsDemo';
import { DashboardWidgetsDemo } from '../components/demo/DashboardWidgetsDemo';

type DemoMode = 'chat' | 'dashboard';

export function GeneralModeDemo() {
  const [demoMode, setDemoMode] = React.useState<DemoMode>('chat');
  const [theme, setTheme] = React.useState<'light' | 'dark' | 'auto'>('auto');
  const [systemTheme, setSystemTheme] = React.useState<'light' | 'dark'>('light');

  // Detect system theme for 'auto' mode
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    
    const handler = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };
    
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const handleReset = () => {
    setDemoMode('chat');
    setTheme('auto');
  };

  return (
    <div style={styles.demoContainer}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>🎨 General Chatbot Mode - Interactive Demo</h1>
        <p style={styles.subtitle}>
          Explore widgets for knowledge base support and analytics
        </p>
      </div>

      {/* Control Panel */}
      <div style={styles.controlPanel}>
        {/* Mode Toggle */}
        <div style={styles.modeToggle}>
          <button
            style={{
              ...styles.modeButton,
              backgroundColor: demoMode === 'chat' ? '#6366f1' : 'transparent',
              color: demoMode === 'chat' ? 'white' : '#374151',
            }}
            onClick={() => setDemoMode('chat')}
          >
            <span>💬</span>
            Chat Widgets
          </button>
          <button
            style={{
              ...styles.modeButton,
              backgroundColor: demoMode === 'dashboard' ? '#6366f1' : 'transparent',
              color: demoMode === 'dashboard' ? 'white' : '#374151',
            }}
            onClick={() => setDemoMode('dashboard')}
          >
            <span>📊</span>
            Dashboard Widgets
          </button>
        </div>

        {/* Theme Toggle */}
        <div style={styles.themeToggle}>
          <button
            style={{
              ...styles.themeButton,
              backgroundColor: theme === 'light' ? '#6366f1' : '#f3f4f6',
              color: theme === 'light' ? 'white' : '#374151',
            }}
            onClick={() => setTheme('light')}
            title="Light theme"
          >
            ☀️
          </button>
          <button
            style={{
              ...styles.themeButton,
              backgroundColor: theme === 'dark' ? '#6366f1' : '#f3f4f6',
              color: theme === 'dark' ? 'white' : '#374151',
            }}
            onClick={() => setTheme('dark')}
            title="Dark theme"
          >
            🌙
          </button>
          <button
            style={{
              ...styles.themeButton,
              backgroundColor: theme === 'auto' ? '#6366f1' : '#f3f4f6',
              color: theme === 'auto' ? 'white' : '#374151',
            }}
            onClick={() => setTheme('auto')}
            title="Auto (system preference)"
          >
            🔄
          </button>
        </div>

        {/* Reset Button */}
        <button
          style={styles.resetButton}
          onClick={handleReset}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'white';
          }}
        >
          ↻ Reset
        </button>
      </div>

      {/* Demo Area */}
      <div style={styles.demoArea}>
        {demoMode === 'chat' ? (
          <ChatWidgetsDemo theme={theme} />
        ) : (
          <DashboardWidgetsDemo theme={theme} />
        )}
      </div>

      {/* Instructions */}
      <div style={styles.instructions}>
        <h3 style={styles.instructionsTitle}>
          💡 Try These Interactions
        </h3>
        <ul style={styles.instructionsList}>
          {demoMode === 'chat' ? (
            <>
              <li><strong>Source Citations:</strong> Click source cards to expand and see document snippets</li>
              <li><strong>FAQ Chips:</strong> Click any FAQ chip to send it as a question</li>
              <li><strong>Quick Replies:</strong> Click suggested questions to continue the conversation</li>
              <li><strong>Feedback:</strong> Rate bot responses with thumbs up/down</li>
              <li><strong>Contact Card:</strong> Click contact options to see how they work</li>
              <li>Type your own messages in the chat input</li>
              <li>Toggle between light and dark themes to see widget styling</li>
            </>
          ) : (
            <>
              <li><strong>Current vs Planned:</strong> Toggle to see implemented vs planned widgets</li>
              <li><strong>Zone Layout:</strong> Widgets are organized by priority (Action → Health → Insights)</li>
              <li><strong>Interactive Elements:</strong> Hover over widgets to see tooltips and effects</li>
              <li><strong>Heatmap:</strong> The peak hours widget shows conversation patterns</li>
              <li><strong>New Widgets:</strong> Planned widgets have dashed borders and NEW badges</li>
              <li>Look for trend indicators (↑↓) showing performance changes</li>
            </>
          )}
        </ul>
      </div>

      {/* Footer Info */}
      <div style={{ 
        padding: '16px 24px 32px', 
        textAlign: 'center', 
        borderTop: '1px solid #e5e7eb',
        backgroundColor: 'white',
        margin: '0 24px 24px',
        borderRadius: '12px',
      }}>
        <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '8px' }}>
          <strong>About This Demo</strong>
        </div>
        <div style={{ fontSize: '12px', color: '#9ca3af', lineHeight: 1.6, maxWidth: '800px', margin: '0 auto' }}>
          This demo showcases widgets designed for <strong>General Chatbot Mode</strong> — a mode focused on 
          knowledge base Q&amp;A without e-commerce features. Chat widgets enhance the customer experience 
          by showing sources, FAQs, and contact options. Dashboard widgets help merchants monitor bot 
          performance, knowledge effectiveness, and customer satisfaction.
        </div>
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', padding: '4px 8px', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '4px' }}>
            ✅ 5 Chat Widgets Ready
          </span>
          <span style={{ fontSize: '11px', padding: '4px 8px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: '4px' }}>
            📊 8 Dashboard Widgets
          </span>
          <span style={{ fontSize: '11px', padding: '4px 8px', backgroundColor: '#eff6ff', color: '#1e40af', borderRadius: '4px' }}>
            🎯 4 New Widgets Planned
          </span>
        </div>
      </div>
    </div>
  );
}

export default GeneralModeDemo;
