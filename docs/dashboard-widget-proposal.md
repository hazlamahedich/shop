# Dashboard Widget Enhancement Proposal

**Version:** 1.1  
**Date:** 2026-03-15  
**Status:** ✅ Completed  
**Source:** Epic 7 Retrospective Action Items #2 and #3

 **New P2 Widgets:**
- BenchmarkComparisonWidget - Compare your metrics to industry benchmarks
- CustomerSentimentWidget - Analyze customer messages for sentiment trends

 **Overview:**

| Widget | Description | Decision |
|---|------------------------||----------|
|------------------------|--------------------|
| **Bot Quality** | "Is my bot working correctly?" | 🟢 Healthy / 🟡 Warning | ⚠ Needs Attention |
| **CSAT Score** | Customer satisfaction (1-5 scale) with stars | ✅ Overall health status indicator |
| **VIP Handoff** | Enhanced handoff queue with VIP flags | 🟡 High / 🟡 Low priority handoffs |
    **Action:** View handoff queue | 📊 **Peak Hours Heatmap** | When should I staff for availability | |
    **Conversion Funnel** | Track conversation to checkout completion |
    **Knowledge Gap Widget** | What is my bot failing on? | FAQ suggestions from gaps | "Add to Knowledge Base" action |

**Color Coding System**
    - Zone 1 (Red): Action Required
    - Zone 2 (Blue) - Business Health
    - Zone 3 (Purple) - Insights & Trends

    - Zone backgrounds differentiate zones
    - Mobile breakpoint: Zone 3 hidden (expandable)

---

## Summary

This proposal defines new widgets and layout changes to transform the dashboard from a data display into a decision-making tool.

### Goals

1. **Support 15+ merchant decisions** (up from 5 currently)
2. **Reduce decision time** to <30 seconds for common actions
3. **Prioritize action over information** in layout

---

## Widget Backlog

### P0 - CRITICAL (Sprint 1)

#### 1. BotQualityWidget

**Decision:** "Is my bot working correctly?"

| Metric | Description | Target |
|--------|-------------|--------|
| Response Time | Average bot reply latency | <2s |
| Fallback Rate | % of "I don't understand" responses | <5% |
| Resolution Rate | % of conversations resolved by bot | >80% |
| CSAT Score | Customer satisfaction (1-5) | >4.0 |

**UI Components:**
- Status indicator (🟢 Healthy / 🟡 Warning / 🔴 Critical)
- 4 metric cards with trend arrows
- "View Details" → Quality analytics page

**Data Sources:**
- `GET /api/v1/analytics/bot-quality`
- New backend endpoint required

**Effort:** Medium (2-3 days)

---

#### 2. VIPHandoffIndicator

**Decision:** "Who should I prioritize?"

**Enhancement to existing HandoffQueueWidget:**

| Feature | Description |
|---------|-------------|
| Customer LTV Badge | 🏆 icon for high-value customers |
| Order Count | "12 orders" shown on hover |
| Total Spend | "$1,234 lifetime" on hover |
| Urgency Dot | 🔴 High / 🟡 Medium / 🟢 Low |

**Data Sources:**
- Existing: `GET /api/handoff-alerts?view=queue`
- Enhancement: Include `customer_ltv`, `order_count`, `total_spend` in response

**Effort:** Low (1 day)

---

### P1 - HIGH (Sprint 2)

#### 3. PeakHoursHeatmap

**Decision:** "When should I be available?"

**UI Components:**
- 7x24 grid (days × hours)
- Color intensity = conversation volume
- Peak hours highlighted
- "Staff accordingly" recommendation

**Data Sources:**
- `GET /api/v1/analytics/peak-hours`
- New backend endpoint required

**Effort:** Medium (2-3 days)

---

#### 4. ConversionFunnelWidget

**Decision:** "Is the bot actually selling?"

**Funnel Stages:**

```
Conversations Started: 1,234 (100%)
        ↓
Products Viewed:        856 (69%)
        ↓
Added to Cart:          432 (35%)
        ↓
Checkout Started:       234 (19%)
        ↓
Completed:              189 (15%)
```

**UI Components:**
- Horizontal funnel visualization
- Drop-off percentages between stages
- MoM comparison
- Alert if conversion drops >10%

**Data Sources:**
- `GET /api/v1/analytics/conversion-funnel`
- New backend endpoint required

**Effort:** Medium (2-3 days)

---

#### 5. MoMTrendBadges

**Decision:** "Are we improving?"

**Enhancement to existing widgets:**

| Widget | MoM Metric | Display |
|--------|------------|---------|
| RevenueWidget | Revenue change | ▲ 12% MoM |
| AICostWidget | Cost change | ▲ 5% MoM |
| ConversationOverviewWidget | Volume change | ▼ 3% MoM |
| BotQualityWidget (new) | CSAT change | ▲ 0.2 MoM |

**Data Sources:**
- Existing endpoints, add `previous_period` data
- Or new comparison endpoint

**Effort:** Low (1 day)

---

### P2 - MEDIUM (Future Sprints)

#### 6. KnowledgeGapWidget

**Decision:** "What is the bot failing on?"

**Features:**
- Top 10 failed queries
- Low-confidence responses
- FAQ suggestions from gaps
- "Add to Knowledge Base" action

**Effort:** Medium (2-3 days)

---

#### 7. BenchmarkComparison

**Decision:** "Is my cost/performance normal?"

**Features:**
- Industry benchmarks for LLM cost
- Your cost vs. industry average
- Performance percentile ranking

**Effort:** Low (1 day) - requires benchmark data source

---

#### 8. CustomerSentimentTrend

**Decision:** "Are customers getting happier?"

**Features:**
- NPS trend over time
- Sentiment analysis from messages
- Alert on negative trend

**Effort:** Medium (2-3 days)

---

## Layout Proposal

### 3-Zone Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🔴 ZONE 1: ACTION REQUIRED                                              │
│                                                                          │
│ Purpose: "What needs my attention NOW?"                                  │
│ Refresh: 30 seconds                                                      │
│ Mental Model: Red/Yellow/Green indicators                               │
│                                                                          │
│ [HandoffQueue + VIP]  [BotQuality]  [Alerts]                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 ZONE 2: BUSINESS HEALTH                                              │
│                                                                          │
│ Purpose: "How is my business doing?"                                     │
│ Refresh: 60 seconds                                                      │
│ Mental Model: Trend arrows, benchmarks, progress bars                   │
│                                                                          │
│ [Revenue + MoM]     [AI Cost + MoM]                                      │
│ [Conversion Funnel] [Conversations + MoM]                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 📈 ZONE 3: INSIGHTS & TRENDS                                            │
│                                                                          │
│ Purpose: "What patterns should I know?"                                  │
│ Refresh: 120 seconds                                                     │
│ Mental Model: Heatmaps, lists, geographic data                          │
│                                                                          │
│ [Peak Hours Heatmap - Full Width]                                        │
│ [Top Products] [Geographic] [Pending Orders]                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Zone Details

| Zone | Widgets | Height | Priority |
|------|---------|--------|----------|
| **Zone 1** | HandoffQueue (2 cols), BotQuality (1 col), Alerts (1 col) | Auto | Always visible |
| **Zone 2** | Revenue (2 cols), AICost (2 cols), Funnel (2 cols), Conversations (2 cols) | Auto | Scroll if needed |
| **Zone 3** | PeakHours (4 cols), Products (1 col), Geo (1 col), Orders (2 cols) | Auto | Scroll if needed |

### Responsive Behavior

| Screen Size | Zone 1 | Zone 2 | Zone 3 |
|-------------|--------|--------|--------|
| **Desktop (1440px+)** | 4 columns | 4 columns | 4 columns |
| **Tablet (768-1439px)** | 2 columns | 2 columns | 2 columns |
| **Mobile (<768px)** | 1 column | 1 column | Hidden (expandable) |

---

## Implementation Plan

### Sprint 1: Critical Widgets (Week 1-2)

| Task | Owner | Effort | Dependency |
|------|-------|--------|------------|
| Backend: `/api/v1/analytics/bot-quality` | Backend | 1 day | None |
| Backend: Enhance handoff endpoint with LTV | Backend | 0.5 day | None |
| Frontend: BotQualityWidget | Frontend | 1.5 days | Backend API |
| Frontend: VIPHandoffIndicator | Frontend | 0.5 day | Backend enhancement |
| Frontend: MoMTrendBadges | Frontend | 1 day | None |

**Total:** ~4.5 days

### Sprint 2: High Priority Widgets (Week 3-4)

| Task | Owner | Effort | Dependency |
|------|-------|--------|------------|
| Backend: `/api/v1/analytics/peak-hours` | Backend | 1 day | None |
| Backend: `/api/v1/analytics/conversion-funnel` | Backend | 1 day | None |
| Frontend: PeakHoursHeatmap | Frontend | 2 days | Backend API |
| Frontend: ConversionFunnelWidget | Frontend | 2 days | Backend API |
| Frontend: Layout restructure | Frontend | 1 day | All widgets |

**Total:** ~7 days

### Sprint 3: Layout & Polish (Week 5)

| Task | Owner | Effort | Dependency |
|------|-------|--------|------------|
| Frontend: Zone layout implementation | Frontend | 1 day | Sprint 2 |
| Frontend: Responsive design | Frontend | 1 day | Zone layout |
| Frontend: Color coding system | Frontend | 0.5 day | None |
| Testing: E2E tests | QA | 1 day | All widgets |
| Documentation: Update user guide | Docs | 0.5 day | None |

**Total:** ~4 days

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Decisions supported | 5 | 15 | Framework coverage |
| Widget coverage | 60% | 95% | Gap analysis |
| Time to decision | TBD | <30s | User testing |
| Merchant satisfaction | TBD | 4.5/5 | Survey |
| Dashboard engagement | TBD | Daily | Analytics |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend API delays | Blocks frontend | Use mock data for development |
| Performance with many widgets | Slow dashboard | Lazy load Zone 3 |
| Mobile complexity | Poor UX | Progressive disclosure |
| Data accuracy | Wrong decisions | Validation checks |

---

## Appendix: Component List

### New Components

| Component | Path | Zone |
|-----------|------|------|
| BotQualityWidget | `frontend/src/components/dashboard/BotQualityWidget.tsx` | Zone 1 |
| PeakHoursHeatmap | `frontend/src/components/dashboard/PeakHoursHeatmap.tsx` | Zone 3 |
| ConversionFunnelWidget | `frontend/src/components/dashboard/ConversionFunnelWidget.tsx` | Zone 2 |
| AlertsWidget | `frontend/src/components/dashboard/AlertsWidget.tsx` | Zone 1 |

### Enhanced Components

| Component | Enhancement |
|-----------|-------------|
| HandoffQueueWidget | VIP flags, LTV badges |
| RevenueWidget | MoM trend badge |
| AICostWidget | MoM trend badge, benchmark |
| ConversationOverviewWidget | MoM trend badge |
| Dashboard.tsx | 3-zone layout |

### New Backend Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/analytics/bot-quality` | Response time, fallback rate, CSAT |
| `GET /api/v1/analytics/peak-hours` | Hourly conversation distribution |
| `GET /api/v1/analytics/conversion-funnel` | Funnel stages and drop-offs |
| Enhancement: `GET /api/handoff-alerts` | Include customer LTV data |

---

*Proposal created as part of Epic 7 Retrospective Action Items #2 and #3*
*Related: `docs/merchant-decision-framework.md`*
