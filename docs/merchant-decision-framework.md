# Merchant Decision Framework

**Version:** 1.0
**Date:** 2026-03-15
**Owner:** Product Team

---

## Overview

This framework defines the key decisions merchants need to make when operating their AI chatbot, organized by urgency and the data required to make those decisions.

---

## Decision Tiers

### Tier 1: REAL-TIME DECISIONS (Seconds to Minutes)

*These require immediate attention and real-time data updates (30-60 second refresh)*

| Decision | Data Needed | Action Triggered | Current Widget |
|----------|-------------|------------------|----------------|
| **Should I take over this conversation?** | Urgency level, Wait time, Customer value, Sentiment | Take over or let bot continue | HandoffQueueWidget ✅ |
| **Is a customer at risk of churning?** | Frustration signals, Escalation count, Conversation tone | Proactive intervention | ⚠️ MISSING |
| **Am I about to hit my budget cap?** | Current spend vs budget, Run rate, Days remaining | Adjust or pause | AICostWidget ✅ (partial) |
| **Are there orders needing attention?** | Unfulfilled orders, Delivery issues, Payment failures | Fulfillment action | PendingOrdersWidget ✅ |

### Tier 2: DAILY DECISIONS (Morning Review)

*These require daily data updates (once per day or on-demand)*

| Decision | Data Needed | Action Triggered | Current Widget |
|----------|-------------|------------------|----------------|
| **Is the bot performing well?** | Response time, Resolution rate, Customer satisfaction | Quality review | ⚠️ MISSING |
| **Which products should I promote?** | Top products, Low stock alerts, Trending queries | Update pins/recommendations | TopProductsWidget ✅ |
| **Are there unresolved issues?** | Pending handoffs, Unread alerts, Open tickets | Prioritize work | HandoffQueueWidget ✅ |
| **How many active conversations?** | Active count, 30d trends, Handoff count | Capacity planning | ConversationOverviewWidget ✅ |

### Tier 3: WEEKLY/STRATEGIC DECISIONS

*These require weekly data updates or on-demand for planning*

| Decision | Data Needed | Action Triggered | Current Widget |
|----------|-------------|------------------|----------------|
| **Is my AI cost sustainable?** | MoM spend trend, Cost per conversation, Provider comparison | Budget adjustment | AICostWidget ✅ (needs MoM) |
| **What do customers ask about?** | FAQ hit rates, Knowledge gaps, Failed queries | Update FAQs/content | ⚠️ MISSING |
| **Where are my customers?** | Geographic distribution, Peak hours, Time zones | Staffing/promotion | GeographicSnapshotWidget ✅ |
| **How is my business trending?** | Revenue MoM, Order volume, AOV trends | Strategy adjustment | RevenueWidget ✅ (needs MoM) |
| **When should I be available?** | Peak hours heatmap, Busiest days, Response time by hour | Schedule planning | ⚠️ MISSING |

---

## Chatbot-Specific Metrics

*Metrics unique to AI chatbot operations*

| Metric | Purpose | Decision | Priority |
|--------|---------|----------|----------|
| **Intent Classification Accuracy** | Is the bot understanding users? | Improve training | HIGH |
| **Fallback Rate** | How often does bot say "I don't understand"? | Add knowledge | HIGH |
| **Handoff Rate** | What % of conversations need human help? | Bot improvement | HIGH |
| **Resolution Time** | How fast are issues resolved? | Process optimization | MEDIUM |
| **Conversation Completion Rate** | What % of conversations reach a conclusion? | UX improvement | MEDIUM |
| **Response Time (Bot)** | How fast does bot reply? | Performance tuning | HIGH |
| **Customer Satisfaction (CSAT)** | Are customers happy with bot? | Quality review | HIGH |

---

## Customer Journey Analytics

*Decisions across the customer lifecycle*

### Discovery → Acquisition → Conversion → Retention → Advocacy

| Stage | Key Metrics | Decisions |
|-------|-------------|-----------|
| **Discovery** | Impressions, Reach, Engagement | Where to promote |
| **Acquisition** | CAC, CTR, New visitors | Channel optimization |
| **Conversion** | Conversion rate, AOV, Cart abandonment | Funnel optimization |
| **Retention** | CLV, Retention rate, Repeat purchases | Loyalty programs |
| **Advocacy** | NPS, Referrals, Reviews | Brand building |

---

## Decision Priority Matrix

| Priority | Criteria | Examples |
|----------|----------|----------|
| **P0 - CRITICAL** | Revenue impact, Customer risk | Budget cap, VIP handoff, Payment failure |
| **P1 - HIGH** | Quality impact, Cost impact | Bot accuracy, Response time, Cost trend |
| **P2 - MEDIUM** | Optimization, Planning | Peak hours, Product promotion, Geographic |
| **P3 - LOW** | Nice to have, Future planning | Long-term trends, Industry benchmarks |

---

## Widget Gap Analysis

### Currently Implemented (Epic 7)

| Widget | Decisions Supported | Gap |
|--------|---------------------|-----|
| RevenueWidget | Revenue tracking | Missing MoM comparison |
| ConversationOverviewWidget | Activity monitoring | Missing satisfaction trend |
| HandoffQueueWidget | Takeover decisions | Missing VIP flags |
| AICostWidget | Budget monitoring | Missing benchmarks |
| GeographicSnapshotWidget | Location insights | ✅ Complete |
| TopProductsWidget | Product promotion | ✅ Complete |
| PendingOrdersWidget | Fulfillment | ✅ Complete |

### Missing Widgets (Proposed)

| Widget | Decision | Priority | Effort |
|--------|----------|----------|--------|
| **BotQualityWidget** | Is bot performing well? | P0 | Medium |
| **VIPHandoffIndicator** | Who to prioritize? | P0 | Low |
| **PeakHoursHeatmap** | When to be available? | P1 | Medium |
| **KnowledgeGapWidget** | What to add to FAQs? | P1 | Medium |
| **ConversionFunnelWidget** | Where are we losing customers? | P1 | Low |
| **MoMTrendIndicators** | Are we improving? | P1 | Low |

---

## Implementation Roadmap

### Phase 1: Critical Gaps (Week 1-2)

1. **VIPHandoffIndicator** - Add customer value flags to handoff queue
2. **BotQualityWidget** - Response time, fallback rate, satisfaction
3. **MoMTrendIndicators** - Add to RevenueWidget and AICostWidget

### Phase 2: High Priority (Week 3-4)

4. **PeakHoursHeatmap** - When is bot busiest
5. **KnowledgeGapWidget** - Failed queries analysis
6. **ConversionFunnelWidget** - Conversations → Checkouts

### Phase 3: Enhancement (Week 5+)

7. **Layout restructure** - Action zone at top
8. **Benchmark comparisons** - Industry standards
9. **Predictive alerts** - Proactive notifications

---

## Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Decisions supported | 5 | 15 | Q2 2026 |
| Widget coverage | 60% | 95% | Q2 2026 |
| Merchant satisfaction | TBD | 4.5/5 | Q2 2026 |
| Decision speed (self-reported) | TBD | <30s | Q2 2026 |

---

## Appendix: Research Sources

- Shopify: Ecommerce Analytics Guide (2024)
- BigCommerce: Ecommerce Analytics (2026)
- Hootsuite: Social Media Analytics Guide (2025)
- Internal: Epic 7 Retrospective (2026-03-15)

---

*Document created as part of Epic 7 Retrospective Action Item #1*
