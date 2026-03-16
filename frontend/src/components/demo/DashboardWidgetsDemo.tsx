/**
 * Dashboard Widgets Demo Component
 * Toggle between current and planned widgets
 */

import * as React from 'react';
import { styles } from './styles';
import { MockDashboardGrid } from './MockDashboardGrid';

interface DashboardWidgetsDemoProps {
  theme: 'light' | 'dark' | 'auto';
}

export function DashboardWidgetsDemo({ theme }: DashboardWidgetsDemoProps) {
  const [viewMode, setViewMode] = React.useState<'current' | 'planned'>('current');

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      {/* Toggle */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', alignItems: 'center' }}>
        <div style={styles.toggleContainer}>
          <button
            style={{
              ...styles.toggleButton,
              backgroundColor: viewMode === 'current' ? '#6366f1' : '#f3f4f6',
              color: viewMode === 'current' ? 'white' : '#374151',
            }}
            onClick={() => setViewMode('current')}
          >
            ✅ Current Widgets
          </button>
          <button
            style={{
              ...styles.toggleButton,
              backgroundColor: viewMode === 'planned' ? '#6366f1' : '#f3f4f6',
              color: viewMode === 'planned' ? 'white' : '#374151',
            }}
            onClick={() => setViewMode('planned')}
          >
            🚧 Planned Widgets
          </button>
        </div>
        
        <div style={{ fontSize: '13px', color: '#6b7280' }}>
          {viewMode === 'current' 
            ? 'Widgets currently available in General mode'
            : 'New widgets planned for implementation'}
        </div>
      </div>

      {/* Legend for planned widgets */}
      {viewMode === 'planned' && (
        <div style={{ 
          marginBottom: '16px', 
          padding: '12px 16px', 
          backgroundColor: '#fef3c7', 
          borderRadius: '8px',
          border: '1px solid #fcd34d',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '16px' }}>💡</span>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#92400e' }}>
              Planned Widgets
            </div>
            <div style={{ fontSize: '12px', color: '#b45309' }}>
              These widgets are designed but not yet implemented. Dashed borders indicate new components.
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Grid */}
      <MockDashboardGrid viewMode={viewMode} />

      {/* Widget Explanations */}
      <div style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div style={styles.descriptionBox}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🚨</span>
            Zone 1: Action Required
          </h4>
          <p style={{ fontSize: '12px', color: '#6b7280', lineHeight: 1.6 }}>
            Real-time alerts that need immediate attention. Includes pending handoffs, bot health issues, and knowledge base processing status.
          </p>
        </div>
        
        <div style={styles.descriptionBox}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📊</span>
            Zone 2: Business Health
          </h4>
          <p style={{ fontSize: '12px', color: '#6b7280', lineHeight: 1.6 }}>
            Key performance indicators showing how your bot is performing. Tracks conversations, costs, and knowledge effectiveness.
          </p>
        </div>
        
        <div style={styles.descriptionBox}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📈</span>
            Zone 3: Insights & Trends
          </h4>
          <p style={{ fontSize: '12px', color: '#6b7280', lineHeight: 1.6 }}>
            Analytics and patterns to help you understand user behavior. Includes peak hours, sentiment trends, and topic analysis.
          </p>
        </div>
      </div>

      {/* Implementation Status */}
      <div style={{ marginTop: '24px', ...styles.descriptionBox }}>
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '12px' }}>
          Implementation Status
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#10b981', marginBottom: '8px' }}>
              ✅ Already Implemented (Config Change Only)
            </div>
            <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: '11px', color: '#6b7280', lineHeight: 1.8 }}>
              <li>BotQualityWidget - Just needs config update</li>
              <li>PeakHoursHeatmapWidget - Data available</li>
              <li>CustomerSentimentWidget - Data available</li>
              <li>KnowledgeGapWidget - Already working</li>
            </ul>
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#f59e0b', marginBottom: '8px' }}>
              🚧 New Widgets (Development Required)
            </div>
            <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: '11px', color: '#6b7280', lineHeight: 1.8 }}>
              <li>KnowledgeEffectivenessWidget - New analytics endpoint</li>
              <li>TopTopicsWidget - Topic clustering logic</li>
              <li>ResponseTimeWidget - Percentile tracking</li>
              <li>FAQUsageWidget - Interaction tracking</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
