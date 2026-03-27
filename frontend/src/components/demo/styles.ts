/**
 * Shared Styles for General Mode Widgets Demo
 * CSS-in-JS styles following the WidgetDemo.tsx pattern
 */

export const colors = {
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  
  // Light theme
  lightBg: '#ffffff',
  lightText: '#1f2937',
  lightMuted: '#6b7280',
  lightBorder: '#e5e7eb',
  lightSurface: '#f9fafb',
  
  // Dark theme
  darkBg: '#0f172a',
  darkText: '#f1f5f9',
  darkMuted: '#94a3b8',
  darkBorder: '#334155',
  darkSurface: '#1e293b',
  
  // Zone colors
  zone1Bg: '#fef2f2',
  zone1Border: '#fecaca',
  zone2Bg: '#eff6ff',
  zone2Border: '#bfdbfe',
  zone3Bg: '#faf5ff',
  zone3Border: '#e9d5ff',
};

export const styles: Record<string, React.CSSProperties> = {
  // Main container
  demoContainer: {
    minHeight: '100vh',
    backgroundColor: '#f8fafc',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  
  // Header
  header: {
    padding: '32px 24px',
    backgroundColor: 'white',
    borderBottom: '1px solid #e5e7eb',
    textAlign: 'center',
  },
  title: {
    fontSize: '32px',
    fontWeight: 700,
    color: '#1f2937',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '16px',
    color: '#6b7280',
  },
  
  // Control Panel
  controlPanel: {
    padding: '16px 24px',
    backgroundColor: 'white',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
    flexWrap: 'wrap',
  },
  modeToggle: {
    display: 'flex',
    gap: '8px',
    backgroundColor: '#f3f4f6',
    padding: '4px',
    borderRadius: '8px',
  },
  modeButton: {
    padding: '8px 20px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  themeToggle: {
    display: 'flex',
    gap: '4px',
  },
  themeButton: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s ease',
    backgroundColor: '#f3f4f6',
  },
  resetButton: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    cursor: 'pointer',
    fontSize: '14px',
    backgroundColor: 'white',
    color: '#6b7280',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  
  // Demo Area
  demoArea: {
    flex: 1,
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    minHeight: '600px',
  },
  
  // Feature Tabs (Chat Widgets)
  featureTabs: {
    width: '280px',
    flexShrink: 0,
  },
  featureTab: {
    padding: '12px 16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    width: '100%',
    textAlign: 'left',
    marginBottom: '4px',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  
  // Feature Description
  descriptionBox: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '16px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  descriptionTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#1f2937',
    marginBottom: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  descriptionText: {
    fontSize: '14px',
    color: '#6b7280',
    lineHeight: 1.6,
  },
  
  // Chat Window
  chatWindow: {
    flex: 1,
    maxWidth: '420px',
    borderRadius: '16px',
    overflow: 'hidden',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    height: '600px',
  },
  chatHeader: {
    padding: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid #e5e7eb',
  },
  chatTitle: {
    fontSize: '16px',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
  },
  chatInput: {
    padding: '16px',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    gap: '8px',
  },
  
  // Messages
  message: {
    marginBottom: '12px',
    display: 'flex',
    flexDirection: 'column',
  },
  messageUser: {
    alignItems: 'flex-end',
  },
  messageBot: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: '12px 16px',
    borderRadius: '16px',
    fontSize: '14px',
    lineHeight: 1.5,
  },
  messageBubbleUser: {
    backgroundColor: '#6366f1',
    color: 'white',
    borderBottomRightRadius: '4px',
  },
  messageBubbleBot: {
    backgroundColor: '#f3f4f6',
    color: '#1f2937',
    borderBottomLeftRadius: '4px',
  },
  messageTime: {
    fontSize: '11px',
    color: '#9ca3af',
    marginTop: '4px',
  },
  botName: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#6b7280',
    marginBottom: '4px',
  },
  
  // Widgets (inside chat)
  widgetContainer: {
    marginTop: '12px',
    maxWidth: '100%',
  },
  
  // Source Citations
  sourcesContainer: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  sourceCard: {
    backgroundColor: 'white',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    padding: '10px 12px',
    fontSize: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    minWidth: '120px',
  },
  sourceIcon: {
    fontSize: '14px',
  },
  sourceExpanded: {
    marginTop: '8px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#6b7280',
    lineHeight: 1.5,
    border: '1px solid #e5e7eb',
  },
  
  // FAQ Chips
  faqChips: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  faqChip: {
    padding: '8px 14px',
    backgroundColor: 'white',
    border: '1px solid #6366f1',
    borderRadius: '20px',
    fontSize: '13px',
    color: '#6366f1',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontWeight: 500,
  },
  
  // Quick Reply Chips
  replyChips: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  replyChip: {
    padding: '8px 14px',
    backgroundColor: '#f3f4f6',
    borderRadius: '20px',
    fontSize: '13px',
    color: '#374151',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    border: 'none',
  },
  
  // Feedback Buttons
  feedbackContainer: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  feedbackButton: {
    padding: '6px 12px',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s ease',
  },
  feedbackCount: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: 500,
  },
  
  // Contact Card
  contactContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  contactButton: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    transition: 'all 0.2s ease',
    textAlign: 'left',
  },
  contactInfo: {
    flex: 1,
  },
  contactLabel: {
    fontWeight: 500,
    color: '#374151',
  },
  contactValue: {
    fontSize: '12px',
    color: '#6b7280',
  },
  
  // Dashboard
  dashboardContainer: {
    flex: 1,
    padding: '0',
  },
  
  // Zone sections
  zoneSection: {
    borderRadius: '12px',
    padding: '16px',
    marginBottom: '16px',
  },
  zoneHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
  },
  zoneTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#374151',
  },
  zoneDescription: {
    fontSize: '12px',
    color: '#9ca3af',
  },
  
  // Widget cards
  widgetCard: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '16px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
  },
  widgetTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#374151',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  widgetValue: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#1f2937',
    marginBottom: '4px',
  },
  widgetSubValue: {
    fontSize: '12px',
    color: '#6b7280',
  },
  
  // Stat rows
  statRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 0',
    borderBottom: '1px solid #f3f4f6',
  },
  statLabel: {
    fontSize: '12px',
    color: '#6b7280',
  },
  statValue: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#374151',
  },
  
  // Trend indicators
  trendUp: {
    color: '#10b981',
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '2px',
  },
  trendDown: {
    color: '#ef4444',
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '2px',
  },
  
  // Heatmap
  heatmapContainer: {
    display: 'flex',
    gap: '2px',
  },
  heatmapCell: {
    width: '12px',
    height: '24px',
    borderRadius: '2px',
  },
  
  // Toggle buttons
  toggleContainer: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
  },
  toggleButton: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 0.2s ease',
  },
  
  // Planned badge
  plannedBadge: {
    fontSize: '10px',
    padding: '2px 6px',
    backgroundColor: '#fef3c7',
    color: '#92400e',
    borderRadius: '4px',
    fontWeight: 500,
    marginLeft: '8px',
  },
  
  // Input field
  input: {
    flex: 1,
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    fontSize: '14px',
    outline: 'none',
  },
  sendButton: {
    padding: '10px 16px',
    borderRadius: '8px',
    backgroundColor: '#6366f1',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '14px',
  },
  
  // Instructions
  instructions: {
    padding: '24px',
    backgroundColor: 'white',
    margin: '0 24px 24px',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  instructionsTitle: {
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  instructionsList: {
    margin: 0,
    padding: '0 0 0 20px',
    color: '#6b7280',
    fontSize: '14px',
    lineHeight: 1.8,
  },
  
  // Toast notification
  toast: {
    position: 'fixed',
    bottom: '24px',
    left: '50%',
    transform: 'translateX(-50%)',
    padding: '12px 24px',
    backgroundColor: '#1f2937',
    color: 'white',
    borderRadius: '8px',
    fontSize: '14px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    zIndex: 1000,
    animation: 'slideUp 0.3s ease',
  },
};
