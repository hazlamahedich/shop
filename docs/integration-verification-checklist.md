# Integration Verification Checklist

**Purpose:** Track which features require manual verification against real external APIs vs. automated mock tests.

**Last Updated:** 2026-02-17 (Epic 4 Retrospective)

---

## External Integration Status

| Integration | Status | Stories Verified | Stories Mocked Only |
|-------------|--------|------------------|---------------------|
| Facebook Messenger | ⚠️ Not Connected | None | 4-9, 4-10 |
| Shopify Store | 🔄 Setup In Progress | None | 4-1, 4-2, 4-3, 4-4 |
| Email Provider | ❌ Not Configured | None | 4-6, 4-11 |

---

## Manual Verification Required

### Facebook Messenger (Stories 4-9, 4-10)

**Blocker:** No Facebook Page connected to merchant account

**To Verify:**
- [ ] AC1: "Open in Messenger" button opens correct conversation
- [ ] AC2: Merchant authenticated in Messenger (no additional login)
- [ ] AC3: Merchant messages appear naturally (no bot indicator)
- [ ] AC4: Bot hybrid mode - stays silent when merchant active
- [ ] AC5: 5-minute edit window works in Messenger
- [ ] AC6: Hybrid mode auto-expires after 2 hours

**Setup Steps:**
1. Create Meta App at developers.facebook.com
2. Add Messenger product
3. Configure OAuth redirect URI
4. Enter App ID/Secret in Settings → Integrations
5. Complete OAuth flow to connect Page

---

### Shopify Store (Stories 4-1, 4-2, 4-3, 4-4)

**Blocker:** No Shopify store connected

**To Verify:**
- [ ] 4-1: Natural language order queries return real order data
- [ ] 4-2: Shopify webhooks trigger on order create/update/fulfill
- [ ] 4-3: Shipping notifications sent for real fulfillment events
- [ ] 4-4: Polling fallback retrieves real order updates

**Setup Steps:**
1. Create Shopify Partner account
2. Create development store
3. Install custom app with required scopes
4. Configure webhook endpoints
5. Complete OAuth flow in Settings → Integrations

---

### Email Provider (Stories 4-6, 4-11)

**Blocker:** No SMTP provider configured

**To Verify:**
- [ ] 4-6: Handoff alert emails delivered to merchant inbox
- [ ] 4-11: 24-hour follow-up emails with backup contact info

**Setup Options:**
- SendGrid (recommended for production)
- AWS SES
- SMTP server with app passwords

---

## Mock Test Coverage

| Story | Backend Unit | Backend Integration | Frontend Unit | E2E | Mock Used |
|-------|--------------|---------------------|---------------|-----|-----------|
| 4-1 | ✅ | ✅ | ✅ | ✅ | MockShopifyProvider |
| 4-2 | ✅ | ✅ | N/A | N/A | MockShopifyProvider |
| 4-3 | ✅ | ✅ | N/A | N/A | MockShopifyProvider |
| 4-4 | ✅ | ✅ | N/A | ✅ | MockShopifyProvider |
| 4-9 | ✅ | ✅ | ✅ | ✅ | Mock Facebook API |
| 4-10 | ✅ | ✅ | ✅ | ✅ | Mock Facebook API |
| 4-11 | ✅ | ✅ | N/A | ✅ | Mock Facebook API |

**Note:** Mocks follow documented API contracts but may not catch real API behavior changes.

---

## Verification Checklist Template

When a story involves external integration, add this to the story file:

```markdown
## Manual Verification Status

| Feature | Verified | Mocked Only | Blocker |
|---------|----------|-------------|---------|
| [Feature name] | [ ] | [ ] | [Blocker or "None"] |

**Setup Required:** [Steps to enable manual verification]
```

---

## Production Readiness

Before deploying to production with real merchants:

- [ ] Facebook Page connected and tested
- [ ] Shopify store connected and webhooks verified
- [ ] Email provider configured and tested
- [ ] Run integration smoke tests against real APIs
- [ ] Verify error handling for API rate limits and outages

---

*Generated from Epic 4 Retrospective Action Item #3*
