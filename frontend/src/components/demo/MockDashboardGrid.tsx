/**
 * Mock Dashboard Grid Component
 * Dashboard layout with mock widget cards
 */

import * as React from 'react';
import { styles, colors } from './styles';
import { mockDashboardStats } from './mockData';

interface MockDashboardGridProps {
  viewMode: 'current' | 'planned';
}

export function MockDashboardGrid({ viewMode }: MockDashboardGridProps) {
  return (
    <div style={styles.dashboardContainer}>
      {/* Zone 1: Action Required */}
      <section style={{ ...styles.zoneSection, backgroundColor: colors.zone1Bg, border: `1px solid ${colors.zone1Border}` }}>
        <div style={styles.zoneHeader}>
          <span>🚨</span>
          <h3 style={styles.zoneTitle}>Zone 1: Action Required</h3>
          <span style={styles.zoneDescription}>What needs my attention NOW?</span>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <HandoffQueueWidget />
          <KnowledgeBaseWidget viewMode={viewMode} />
        </div>
      </section>

      {/* Zone 2: Business Health */}
      <section style={{ ...styles.zoneSection, backgroundColor: colors.zone2Bg, border: `1px solid ${colors.zone2Border}` }}>
        <div style={styles.zoneHeader}>
          <span>📊</span>
          <h3 style={styles.zoneTitle}>Zone 2: Business Health</h3>
          <span style={styles.zoneDescription}>How is my bot performing?</span>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <ConversationOverviewWidget />
          <AICostWidget />
          {viewMode === 'planned' && <KnowledgeEffectivenessWidget />}
        </div>
      </section>

      {/* Zone 3: Insights & Trends */}
      <section style={{ ...styles.zoneSection, backgroundColor: colors.zone3Bg, border: `1px solid ${colors.zone3Border}` }}>
        <div style={styles.zoneHeader}>
          <span>📈</span>
          <h3 style={styles.zoneTitle}>Zone 3: Insights & Trends</h3>
          <span style={styles.zoneDescription}>What patterns should I know?</span>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <PeakHoursWidget />
          <SentimentWidget />
          <BotQualityWidget />
          <KnowledgeGapsWidget />
          
          {viewMode === 'planned' && (
            <>
              <TopTopicsWidget />
              <ResponseTimeWidget />
              <FAQUsageWidget />
            </>
          )}
        </div>
      </section>
    </div>
  );
}

// ============================================
// WIDGET COMPONENTS
// ============================================

function HandoffQueueWidget() {
  const { handoffs } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>👋</span>
        Handoff Queue
      </div>
      <div style={styles.widgetValue}>{handoffs.pending}</div>
      <div style={styles.widgetSubValue}>pending handoffs</div>
      
      {handoffs.items.slice(0, 3).map((item) => (
        <div key={item.id} style={{ ...styles.statRow, padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 500, color: '#374151' }}>
              {item.isVip && <span style={{ color: '#f59e0b' }}>⭐ </span>}
              {item.customer}
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>{item.message}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: item.urgency === 'high' ? '#ef4444' : '#6b7280' }}>
              {item.waitTime}
            </div>
          </div>
        </div>
      ))}
      
      <button style={{ marginTop: '12px', padding: '8px 12px', backgroundColor: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', width: '100%' }}>
        Take Over
      </button>
    </div>
  );
}

function KnowledgeBaseWidget({ viewMode }: { viewMode: 'current' | 'planned' }) {
  const { knowledgeBase } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>📄</span>
        Knowledge Base
        {viewMode === 'planned' && <span style={styles.plannedBadge}>ENHANCED</span>}
      </div>
      <div style={styles.widgetValue}>{knowledgeBase.totalDocs}</div>
      <div style={styles.widgetSubValue}>documents uploaded</div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Ready</span>
          <span style={{ ...styles.statValue, color: '#10b981' }}>{knowledgeBase.ready}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Processing</span>
          <span style={{ ...styles.statValue, color: '#f59e0b' }}>{knowledgeBase.processing}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Total Chunks</span>
          <span style={styles.statValue}>{knowledgeBase.totalChunks}</span>
        </div>
      </div>
      
      <button style={{ marginTop: '12px', padding: '8px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', width: '100%' }}>
        Upload Document
      </button>
    </div>
  );
}

function ConversationOverviewWidget() {
  const { conversations } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>💬</span>
        Conversations
      </div>
      <div style={styles.widgetValue}>{conversations.total}</div>
      <div style={{ ...styles.widgetSubValue, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>30 days</span>
        <span style={styles.trendUp}>↑ {conversations.change}%</span>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Active Now</span>
          <span style={{ ...styles.statValue, color: '#6366f1' }}>{conversations.active}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Pending Handoffs</span>
          <span style={styles.statValue}>{conversations.handoffs}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Satisfaction</span>
          <span style={{ ...styles.statValue, color: '#10b981' }}>{conversations.satisfaction}%</span>
        </div>
      </div>
    </div>
  );
}

function AICostWidget() {
  const { aiCost } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>💰</span>
        AI Costs
      </div>
      <div style={styles.widgetValue}>${aiCost.total.toFixed(2)}</div>
      <div style={{ ...styles.widgetSubValue, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>this month</span>
        <span style={styles.trendDown}>↓ {Math.abs(aiCost.change)}%</span>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Total Requests</span>
          <span style={styles.statValue}>{aiCost.requests.toLocaleString()}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>OpenAI</span>
          <span style={styles.statValue}>${aiCost.breakdown.openai.toFixed(2)}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Anthropic</span>
          <span style={styles.statValue}>${aiCost.breakdown.anthropic.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

function KnowledgeEffectivenessWidget() {
  const { knowledgeEffectiveness } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2', border: '2px dashed #6366f1' }}>
      <div style={styles.widgetTitle}>
        <span>🎯</span>
        Knowledge Effectiveness
        <span style={styles.plannedBadge}>NEW</span>
      </div>
      <div style={styles.widgetValue}>{knowledgeEffectiveness.hitRate}%</div>
      <div style={{ ...styles.widgetSubValue, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>RAG hit rate</span>
        <span style={styles.trendUp}>↑ {knowledgeEffectiveness.change}%</span>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Avg Relevance</span>
          <span style={styles.statValue}>{knowledgeEffectiveness.avgRelevance.toFixed(2)}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Chunks Used</span>
          <span style={styles.statValue}>{knowledgeEffectiveness.chunksUsed}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>No Match</span>
          <span style={{ ...styles.statValue, color: '#f59e0b' }}>{knowledgeEffectiveness.queriesWithoutMatch}</span>
        </div>
      </div>
    </div>
  );
}

function PeakHoursWidget() {
  const { peakHours } = mockDashboardStats;
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 4' }}>
      <div style={styles.widgetTitle}>
        <span>🔥</span>
        Peak Hours Heatmap
      </div>
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '12px' }}>Conversation volume by day and hour</div>
      
      <div style={{ display: 'flex', gap: '2px' }}>
        {/* Day labels */}
        <div style={{ width: '40px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <div style={{ height: '24px' }} />
          {days.map((day) => (
            <div key={day} style={{ height: '24px', fontSize: '10px', color: '#9ca3af', display: 'flex', alignItems: 'center' }}>
              {day}
            </div>
          ))}
        </div>
        
        {/* Heatmap grid */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ display: 'flex', gap: '2px', marginBottom: '2px' }}>
            {Array.from({ length: 24 }, (_, i) => (
              <div key={i} style={{ width: '12px', fontSize: '8px', color: '#9ca3af', textAlign: 'center' }}>
                {i % 6 === 0 ? i : ''}
              </div>
            ))}
          </div>
          {peakHours.map((day, dayIdx) => (
            <div key={dayIdx} style={{ display: 'flex', gap: '2px', marginBottom: '2px' }}>
              {day.map((value, hourIdx) => (
                <div
                  key={hourIdx}
                  style={{
                    width: '12px',
                    height: '24px',
                    borderRadius: '2px',
                    backgroundColor: getHeatmapColor(value),
                  }}
                  title={`${days[dayIdx]} ${hourIdx}:00 - ${value} conversations`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', fontSize: '10px', color: '#6b7280' }}>
        <span>Less</span>
        <div style={{ width: '8px', height: '8px', backgroundColor: '#f3f4f6', borderRadius: '2px' }} />
        <div style={{ width: '8px', height: '8px', backgroundColor: '#c7d2fe', borderRadius: '2px' }} />
        <div style={{ width: '8px', height: '8px', backgroundColor: '#818cf8', borderRadius: '2px' }} />
        <div style={{ width: '8px', height: '8px', backgroundColor: '#4f46e5', borderRadius: '2px' }} />
        <span>More</span>
      </div>
    </div>
  );
}

function SentimentWidget() {
  const { sentiment } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>😊</span>
        Customer Sentiment
      </div>
      <div style={styles.widgetValue}>{sentiment.positive}%</div>
      <div style={{ ...styles.widgetSubValue, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>positive</span>
        <span style={styles.trendUp}>↑ {sentiment.trendChange}%</span>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={{ ...styles.statLabel, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#10b981', borderRadius: '50%' }} />
            Positive
          </span>
          <span style={{ ...styles.statValue, color: '#10b981' }}>{sentiment.positive}</span>
        </div>
        <div style={styles.statRow}>
          <span style={{ ...styles.statLabel, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#ef4444', borderRadius: '50%' }} />
            Negative
          </span>
          <span style={{ ...styles.statValue, color: '#ef4444' }}>{sentiment.negative}</span>
        </div>
        <div style={styles.statRow}>
          <span style={{ ...styles.statLabel, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#9ca3af', borderRadius: '50%' }} />
            Neutral
          </span>
          <span style={styles.statValue}>{sentiment.neutral}</span>
        </div>
      </div>
      
      {/* Mini trend chart */}
      <div style={{ marginTop: '12px', display: 'flex', gap: '4px', alignItems: 'flex-end', height: '24px' }}>
        {sentiment.dailyBreakdown.slice(-7).map((day, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: `${day.positiveRate * 100}%`,
              backgroundColor: day.positiveRate > 0.6 ? '#86efac' : day.positiveRate > 0.4 ? '#fcd34d' : '#fca5a5',
              borderRadius: '2px',
            }}
            title={`${day.date}: ${Math.round(day.positiveRate * 100)}%`}
          />
        ))}
      </div>
    </div>
  );
}

function BotQualityWidget() {
  const { botQuality } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>🤖</span>
        Bot Quality
      </div>
      <div style={styles.widgetValue}>{botQuality.csat.toFixed(1)}</div>
      <div style={{ ...styles.widgetSubValue, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>CSAT score</span>
        <span style={styles.trendUp}>↑ {botQuality.csatChange}%</span>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Response Time</span>
          <span style={styles.statValue}>{botQuality.responseTime}s</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Fallback Rate</span>
          <span style={{ ...styles.statValue, color: '#f59e0b' }}>{botQuality.fallbackRate}%</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Resolution Rate</span>
          <span style={{ ...styles.statValue, color: '#10b981' }}>{botQuality.resolutionRate}%</span>
        </div>
      </div>
    </div>
  );
}

function KnowledgeGapsWidget() {
  const { knowledgeGaps } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2' }}>
      <div style={styles.widgetTitle}>
        <span>🔍</span>
        Knowledge Gaps
      </div>
      <div style={styles.widgetSubValue}>Missing knowledge detected</div>
      
      <div style={{ marginTop: '12px' }}>
        {knowledgeGaps.map((gap, idx) => (
          <div key={idx} style={styles.statRow}>
            <span style={{ ...styles.statLabel, display: 'flex', alignItems: 'center', gap: '4px' }}>
              {gap.trend === 'up' && <span style={{ color: '#ef4444' }}>↑</span>}
              {gap.trend === 'down' && <span style={{ color: '#10b981' }}>↓</span>}
              {gap.trend === 'stable' && <span style={{ color: '#9ca3af' }}>→</span>}
              {gap.topic}
            </span>
            <span style={{ ...styles.statValue, color: gap.count > 15 ? '#ef4444' : '#6b7280' }}>
              {gap.count} queries
            </span>
          </div>
        ))}
      </div>
      
      <button style={{ marginTop: '12px', padding: '8px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', width: '100%' }}>
        Add Documentation
      </button>
    </div>
  );
}

function TopTopicsWidget() {
  const { topTopics } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2', border: '2px dashed #6366f1' }}>
      <div style={styles.widgetTitle}>
        <span>🏷️</span>
        Top Topics
        <span style={styles.plannedBadge}>NEW</span>
      </div>
      <div style={styles.widgetSubValue}>Most queried topics</div>
      
      <div style={{ marginTop: '12px' }}>
        {topTopics.slice(0, 5).map((topic, idx) => (
          <div key={idx} style={styles.statRow}>
            <span style={{ ...styles.statLabel, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '16px', fontSize: '10px', color: '#9ca3af' }}>#{idx + 1}</span>
              {topic.topic}
            </span>
            <span style={{ ...styles.statValue, display: 'flex', alignItems: 'center', gap: '4px' }}>
              {topic.count}
              {topic.trend === 'up' && <span style={{ color: '#ef4444', fontSize: '10px' }}>↑</span>}
              {topic.trend === 'down' && <span style={{ color: '#10b981', fontSize: '10px' }}>↓</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResponseTimeWidget() {
  const { responseTimes } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2', border: '2px dashed #6366f1' }}>
      <div style={styles.widgetTitle}>
        <span>⚡</span>
        Response Time Distribution
        <span style={styles.plannedBadge}>NEW</span>
      </div>
      <div style={styles.widgetSubValue}>Percentile response times</div>
      
      <div style={{ marginTop: '12px' }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>P50 (Median)</span>
          <span style={styles.statValue}>{responseTimes.p50}s</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>P95</span>
          <span style={{ ...styles.statValue, color: '#f59e0b' }}>{responseTimes.p95}s</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>P99</span>
          <span style={{ ...styles.statValue, color: '#ef4444' }}>{responseTimes.p99}s</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Average</span>
          <span style={styles.statValue}>{responseTimes.avg}s</span>
        </div>
      </div>
      
      {/* Visual bar */}
      <div style={{ marginTop: '12px', display: 'flex', gap: '4px', height: '8px' }}>
        <div style={{ flex: 1, backgroundColor: '#10b981', borderRadius: '4px' }} title="P50" />
        <div style={{ width: '20px', backgroundColor: '#f59e0b', borderRadius: '4px' }} title="P95" />
        <div style={{ width: '8px', backgroundColor: '#ef4444', borderRadius: '4px' }} title="P99" />
      </div>
    </div>
  );
}

function FAQUsageWidget() {
  const { faqUsage } = mockDashboardStats;
  
  return (
    <div style={{ ...styles.widgetCard, gridColumn: 'span 2', border: '2px dashed #6366f1' }}>
      <div style={styles.widgetTitle}>
        <span>❓</span>
        FAQ Usage
        <span style={styles.plannedBadge}>NEW</span>
      </div>
      <div style={styles.widgetSubValue}>Top FAQs triggered</div>
      
      <div style={{ marginTop: '12px' }}>
        {faqUsage.slice(0, 4).map((faq, idx) => (
          <div key={idx} style={styles.statRow}>
            <span style={{ ...styles.statLabel, maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {faq.question}
            </span>
            <span style={{ ...styles.statValue, display: 'flex', alignItems: 'center', gap: '4px' }}>
              {faq.clicks}
              <span style={{ fontSize: '9px', color: '#10b981' }}>({faq.helpful}👍)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Helper function to get heatmap color
function getHeatmapColor(value: number): string {
  if (value === 0) return '#f3f4f6';
  if (value < 10) return '#e0e7ff';
  if (value < 20) return '#c7d2fe';
  if (value < 30) return '#a5b4fc';
  if (value < 40) return '#818cf8';
  return '#4f46e5';
}
