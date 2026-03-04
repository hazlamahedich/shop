# Merchant Data Export Guide

**Story 6-3: Merchant CSV Export**  
**Feature:** Complete merchant data export for GDPR/CCPA compliance

---

## Overview

As a merchant, you can export all your data including conversations, messages, LLM costs, and configuration settings. This export provides full data sovereignty and complies with GDPR/CCPA regulations.

---

## How to Export Your Data

### Step 1: Navigate to Dashboard

1. Log in to your merchant dashboard
2. You'll see the "Export All Data" button on the main dashboard page

### Step 2: Click Export

1. Click the **"Export All Data"** button
2. The system will generate your complete data export
3. A CSV file will automatically download to your computer

### Step 3: Review Your Export

The downloaded CSV file contains:
- **Conversation history** (with consent-based filtering)
- **Message content** (excluding opted-out users)
- **LLM cost tracking** (all costs)
- **Configuration settings** (bot settings, personality, greeting)

---

## What's Included in the Export

### ✅ Always Included (Operational Data)

| Data Type | Description | Format |
|-----------|-------------|--------|
| **Conversation Metadata** | Conversation IDs, platforms, timestamps | CSV rows |
| **LLM Costs** | Token usage, costs per conversation | USD amounts |
| **Merchant Config** | Bot name, personality, greeting settings | Key-value pairs |
| **Order References** | Order IDs and timestamps | CSV rows |

### 🔒 Consent-Based (Voluntary Data)

| Data Type | Included If | Excluded If |
|-----------|-------------|-------------|
| **Customer IDs** | Customer opted-in | Anonymized (`anon_123`) |
| **Message Content** | Customer opted-in | Empty (preserves message existence) |
| **Conversation Content** | Customer opted-in | Metadata only |

---

## CSV File Structure

The export CSV has 4 sections:

### 1. Metadata Header

```csv
# Merchant Data Export
# Export Date: 2026-03-04T12:00:00Z
# Merchant ID: 123
# Total Conversations: 45
# Total Messages: 234
# Total LLM Cost: $12.34
```

### 2. Conversations Section

```csv
## SECTION: CONVERSATIONS
conversation_id,platform,customer_id,consent_status,started_at,ended_at,message_count
12345,messenger,customer_abc123,opted_in,2026-02-01T10:00:00Z,2026-02-01T10:15:00Z,5
```

### 3. Messages Section

```csv
## SECTION: MESSAGES
message_id,conversation_id,role,content,created_at
101,12345,user,I want to buy running shoes,2026-02-01T10:00:05Z
```

### 4. LLM Costs Section

```csv
## SECTION: LLM COSTS
cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at
201,12345,openai,gpt-4,150,80,0.0046,2026-02-01T10:00:07Z
```

---

## Rate Limits

- **Maximum:** 1 export per hour per merchant
- **Reason:** Prevent resource exhaustion and ensure system stability
- **If Rate Limited:** Wait for the specified time (shown in error message) before trying again

---

## Consent & Privacy

### Customer Consent Status

Each conversation has a consent status:

| Status | Meaning | Data Included |
|--------|---------|---------------|
| **opted_in** | Customer consented to save data | Full conversation content + customer ID |
| **opted_out** | Customer chose not to save data | Metadata only, anonymized ID, empty content |
| **pending** | No consent decision yet | Treated as opted_out (conservative approach) |

### Data Tier Separation

The export respects GDPR/CCPA data tiers:

1. **Voluntary Data:** Excluded if customer opted out
   - Conversation content
   - Customer preferences
   - Personal identifiers

2. **Operational Data:** Always included
   - Order references
   - Timestamps
   - LLM costs

3. **Anonymized Data:** Aggregated analytics only
   - No personal identifiers

---

## Common Questions

### Q: Why are some message contents empty?

**A:** Customers who opted out of data storage have their message content excluded from the export. This complies with GDPR/CCPA regulations. The message existence is preserved for audit trail purposes.

### Q: Why are some customer IDs anonymized?

**A:** Customer IDs are anonymized (`anon_123`) for customers who opted out. This protects their privacy while maintaining data integrity.

### Q: How often can I export my data?

**A:** You can export your data once per hour. This rate limit prevents system overload and ensures fair resource allocation.

### Q: Can I export data for a specific date range?

**A:** Currently, exports include all historical data. Date range filtering may be added in future updates.

### Q: What format is the export?

**A:** Exports are in standard CSV format compatible with:
- Microsoft Excel
- Google Sheets
- LibreOffice Calc
- Database import tools (PostgreSQL, MySQL, SQLite)

### Q: How long does the export take?

**A:** Export time depends on data size:
- Small datasets (<1K conversations): ~5-10 seconds
- Medium datasets (1-10K conversations): ~10-30 seconds
- Large datasets (>10K conversations): ~30-60 seconds

---

## Technical Details

### File Naming

Exports are named: `merchant_{merchant_id}_export_{YYYYMMDD}.csv`

**Example:** `merchant_123_export_20260304.csv`

### Character Encoding

- **Format:** UTF-8
- **CSV Escaping:** Standard CSV quoting (RFC 4180)
- **Special Characters:** Properly escaped for Excel/Sheets compatibility

### Security

- **Authentication:** Requires valid merchant JWT token
- **CSRF Protection:** Export endpoint requires CSRF token
- **Rate Limiting:** 1 export per hour per merchant
- **Concurrent Locks:** Prevents simultaneous exports

---

## Troubleshooting

### Export Button Not Working

1. **Check authentication:** Ensure you're logged in
2. **Check rate limit:** Wait if you've exported recently
3. **Check browser:** Enable downloads and disable popup blockers

### CSV File Won't Open

1. **Try different application:** Open in Google Sheets or LibreOffice
2. **Check file size:** Large files may take time to load
3. **Check encoding:** Ensure UTF-8 encoding is selected

### Missing Data in Export

1. **Check consent status:** Customers may have opted out
2. **Check date range:** Export includes all historical data
3. **Contact support:** If data is unexpectedly missing

---

## Support

For additional help with data exports:

- **Email:** support@example.com
- **Documentation:** [docs/data-export-format.md](/docs/data-export-format.md)
- **Privacy Policy:** [Privacy Policy](/privacy)

---

## Related Documentation

- [CSV Format Specification](/docs/data-export-format.md)
- [GDPR Compliance Guide](/docs/gdpr-compliance.md)
- [Data Tier Classification](/docs/project-context.md#gdprccpa-compliance)

---

**Last Updated:** 2026-03-04  
**Version:** 1.0  
**Story:** 6-3-merchant-csv-export
