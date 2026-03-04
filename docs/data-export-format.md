# Merchant Data Export Format

**Story:** 6-3-merchant-csv-export  
**Version:** 1.0  
**Last Updated:** 2026-03-04  
**Status:** Draft

---

## Overview

This document defines the CSV format for merchant data exports (GDPR/CCPA compliance). Exports include all merchant data: conversations, messages, LLM costs, and configuration.

**Key Features:**
- Consent-based data filtering (exclude opted-out voluntary data)
- Multi-section format with metadata header
- Standard CSV with proper escaping (CSV injection prevention)
- ISO 8601 timestamps
- Anonymized customer IDs for opted-out users

---

## CSV Structure

### File Naming

```
merchant_{merchant_id}_export_{YYYYMMDD}.csv
```

**Example:** `merchant_123_export_20260304.csv`

### Metadata Header

```csv
# Merchant Data Export
# Export Date: 2026-03-04T12:00:00Z
# Merchant ID: 123
# Total Conversations: 45
# Total Messages: 234
# Total LLM Cost: $12.34
# Opted-Out Excluded: 5 conversations

```

**Fields:**
- **Export Date:** ISO 8601 timestamp (UTC)
- **Merchant ID:** Unique merchant identifier
- **Total Conversations:** Count of conversations exported
- **Total Messages:** Count of messages exported
- **Total LLM Cost:** Sum of LLM API costs (USD)
- **Opted-Out Excluded:** Count of conversations excluded due to consent status

---

## Section 1: Conversations

**Header Row:**

```csv
## SECTION: CONVERSATIONS
conversation_id,platform,customer_id,consent_status,started_at,ended_at,message_count
```

**Column Definitions:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `conversation_id` | Integer | Unique conversation ID | `12345` |
| `platform` | String | Platform identifier | `messenger`, `widget` |
| `customer_id` | String | Customer identifier (anonymized if opted-out) | `customer_abc123` or `anon_12345` |
| `consent_status` | String | Consent status for this conversation | `opted_in`, `opted_out`, `pending` |
| `started_at` | ISO 8601 | Conversation start timestamp | `2026-02-01T10:00:00Z` |
| `ended_at` | ISO 8601 | Conversation end timestamp (nullable) | `2026-02-01T10:15:00Z` or empty |
| `message_count` | Integer | Number of messages in conversation | `12` |

**Consent Status Values:**
- `opted_in`: Customer consented to save conversation data
- `opted_out`: Customer opted out - content excluded, ID anonymized
- `pending`: No consent decision yet - treat as opted_out

**Data Tier Rules:**
- **Opted-In:** Include all conversation data (content, customer ID, timestamps)
- **Opted-Out:** Exclude message content, anonymize customer ID, keep metadata only
- **Pending:** Same as opted-out (conservative approach)

**Example Rows:**

```csv
12345,messenger,anon_12345,opted_out,2026-02-01T10:00:00Z,2026-02-01T10:15:00Z,5
12346,widget,customer_xyz789,opted_in,2026-02-02T14:30:00Z,2026-02-02T14:45:00Z,8
```

---

## Section 2: Messages

**Header Row:**

```csv
## SECTION: MESSAGES
message_id,conversation_id,role,content,created_at
```

**Column Definitions:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `message_id` | Integer | Unique message ID | `101` |
| `conversation_id` | Integer | Foreign key to conversation | `12346` |
| `role` | String | Message sender role | `user`, `assistant`, `system` |
| `content` | Text | Decrypted message content (empty if opted-out) | `I want to buy running shoes` or empty |
| `created_at` | ISO 8601 | Message timestamp | `2026-02-02T14:30:05Z` |

**Consent-Based Filtering:**
- **Opted-In:** Include full decrypted message content
- **Opted-Out:** `content` field is empty (preserves message existence for audit trail)
- **Pending:** Same as opted-out

**Example Rows:**

```csv
101,12346,user,I want to buy running shoes,2026-02-02T14:30:05Z
102,12346,assistant,Sure! What size do you need?,2026-02-02T14:30:07Z
103,12345,user,,2026-02-01T10:00:05Z
```

**Note:** Row 103 shows opted-out user - content is empty but message existence is preserved.

---

## Section 3: LLM Costs

**Header Row:**

```csv
## SECTION: LLM COSTS
cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at
```

**Column Definitions:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `cost_id` | Integer | Unique cost tracking ID | `201` |
| `conversation_id` | Integer | Foreign key to conversation | `12346` |
| `provider` | String | LLM provider name | `openai`, `anthropic`, `ollama` |
| `model` | String | Model identifier | `gpt-4`, `claude-3-opus`, `llama2` |
| `input_tokens` | Integer | Number of input tokens | `150` |
| `output_tokens` | Integer | Number of output tokens | `80` |
| `cost_usd` | Decimal | Cost in USD (4 decimal places) | `0.0046` |
| `created_at` | ISO 8601 | Cost tracking timestamp | `2026-02-02T14:30:07Z` |

**Data Tier:** Always include (operational data, no consent filtering)

**Example Rows:**

```csv
201,12346,openai,gpt-4,150,80,0.0046,2026-02-02T14:30:07Z
202,12346,openai,gpt-4,200,120,0.0064,2026-02-02T14:30:09Z
```

---

## Section 4: Configuration

**Header Row:**

```csv
## SECTION: CONFIGURATION
setting_name,setting_value
```

**Column Definitions:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `setting_name` | String | Configuration key | `personality` |
| `setting_value` | Text | Configuration value (JSON for complex settings) | `friendly` or `{"greeting": "Hi!"}` |

**Data Tier:** Always include (operational data, no consent filtering)

**Standard Settings:**

| Setting Name | Description | Example Value |
|--------------|-------------|---------------|
| `bot_name` | Bot display name | `ShopBot` |
| `personality` | Bot personality trait | `friendly`, `professional`, `casual` |
| `greeting_template` | Greeting message template | `Hi! I'm here to help you shop!` |
| `business_hours` | Operating hours (JSON) | `{"start": "09:00", "end": "17:00", "timezone": "UTC"}` |
| `faqs` | FAQ list (JSON) | `[{"question": "...", "answer": "..."}]` |

**Example Rows:**

```csv
bot_name,ShopBot
personality,friendly
greeting_template,Hi! I'm here to help you shop!
business_hours,"{""start"": ""09:00"", ""end"": ""17:00"", ""timezone"": ""UTC""}"
```

---

## CSV Injection Prevention

**Dangerous Characters:**
- Formula injection: `=`, `+`, `-`, `@`
- Control characters: `\t` (tab), `\r` (carriage return)

**Escaping Rules:**

1. **Prefix with single quote** if field starts with dangerous character:
   ```
   =SUM(A1:A10) → '=SUM(A1:A10)
   +1-800-555-1234 → '+1-800-555-1234
   ```

2. **Quote all fields** using CSV standard quoting (`QUOTE_ALL`):
   ```python
   import csv
   writer = csv.DictWriter(output, fieldnames=headers, quoting=csv.QUOTE_ALL)
   ```

3. **Escape quotes** by doubling:
   ```
   He said "Hello" → "He said ""Hello"""
   ```

**Implementation Pattern:**

```python
def sanitize_csv_field(value: str) -> str:
    """Prevent CSV formula injection."""
    dangerous_chars = ('=', '+', '-', '@', '\t', '\r')
    if value.startswith(dangerous_chars):
        return "'" + value
    return value
```

---

## Consent Status Handling

### Opted-In Users

**Include:**
- Full conversation content
- Actual customer identifier
- All message content (decrypted)
- Complete metadata

**Example:**
```csv
12346,widget,customer_xyz789,opted_in,2026-02-02T14:30:00Z,2026-02-02T14:45:00Z,8
101,12346,user,I want to buy running shoes,2026-02-02T14:30:05Z
```

### Opted-Out Users

**Include:**
- Anonymized customer ID: `anon_{conversation_id}`
- Metadata only (timestamps, counts)
- Empty message content
- Consent status: `opted_out`

**Exclude:**
- Message content (GDPR requirement)
- Customer identifiers
- Any voluntary data

**Example:**
```csv
12345,messenger,anon_12345,opted_out,2026-02-01T10:00:00Z,2026-02-01T10:15:00Z,5
103,12345,user,,2026-02-01T10:00:05Z
```

### Pending Consent

**Treat as opted-out** (conservative approach):
- Anonymize customer ID
- Exclude message content
- Consent status: `pending`

---

## Data Tier Classification

| Data Type | Tier | Consent Required? | Inclusion Rule |
|-----------|------|-------------------|----------------|
| Conversation content | Voluntary | YES | **EXCLUDE if opted-out** |
| Customer preferences | Voluntary | YES | **EXCLUDE if opted-out** |
| Order references | Operational | NO | **Always include** |
| Timestamps | Operational | NO | **Always include** |
| LLM costs | Operational | NO | **Always include** |
| Merchant config | Operational | NO | **Always include** |
| Aggregated analytics | Anonymized | NO | **Include anonymized only** |

---

## Edge Cases

### No Data to Export

If merchant has no data:

```csv
# Merchant Data Export
# Export Date: 2026-03-04T12:00:00Z
# Merchant ID: 123
# Total Conversations: 0
# Total Messages: 0
# Total LLM Cost: $0.00
# Opted-Out Excluded: 0

## SECTION: CONVERSATIONS
conversation_id,platform,customer_id,consent_status,started_at,ended_at,message_count

## SECTION: MESSAGES
message_id,conversation_id,role,content,created_at

## SECTION: LLM COSTS
cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at

## SECTION: CONFIGURATION
setting_name,setting_value
```

### Mixed Consent Status

Merchant has conversations with both opted-in and opted-out customers:

```csv
# Total Conversations: 45
# Opted-Out Excluded: 5

## SECTION: CONVERSATIONS
12345,messenger,anon_12345,opted_out,2026-02-01T10:00:00Z,2026-02-01T10:15:00Z,5
12346,widget,customer_xyz789,opted_in,2026-02-02T14:30:00Z,2026-02-02T14:45:00Z,8
```

### Special Characters in Data

Message contains commas, quotes, or newlines:

```csv
101,12346,user,"I want shoes, size 10, in ""navy blue""",2026-02-02T14:30:05Z
```

**Escaping:** CSV standard quoting handles commas, quotes, and embedded newlines automatically.

---

## Performance Considerations

### Large Datasets (>10K conversations)

**Streaming Strategy:**
- Stream in chunks of 1000 rows
- Use FastAPI `StreamingResponse`
- Avoid loading full dataset into memory

**Memory Target:** <100MB regardless of dataset size

### File Size Estimates

| Conversations | Messages | Estimated Size |
|---------------|----------|----------------|
| 100 | 500 | ~50 KB |
| 1,000 | 5,000 | ~500 KB |
| 10,000 | 50,000 | ~5 MB |
| 100,000 | 500,000 | ~50 MB |

**Note:** Actual size depends on message length and configuration complexity.

---

## Import Compatibility

**Spreadsheet Tools:**
- Microsoft Excel: Compatible (standard CSV)
- Google Sheets: Compatible (standard CSV)
- LibreOffice Calc: Compatible (standard CSV)

**Database Import:**
- PostgreSQL `COPY` command: Compatible
- MySQL `LOAD DATA INFILE`: Compatible
- SQLite `.import` command: Compatible

**Programming Languages:**
- Python `csv` module: Compatible
- JavaScript `Papa Parse`: Compatible
- R `read.csv()`: Compatible

---

## Validation Checklist

Before considering export complete, verify:

- [ ] CSV file has metadata header with export date and counts
- [ ] All four sections present (Conversations, Messages, LLM Costs, Configuration)
- [ ] Opted-out conversations have anonymized customer IDs (`anon_*`)
- [ ] Opted-out message content is empty (preserves message existence)
- [ ] All fields properly escaped (no formula injection)
- [ ] Timestamps in ISO 8601 format (UTC)
- [ ] File size within expected range
- [ ] No CSV parsing errors in standard tools

---

## References

- **Story File:** `_bmad-output/implementation-artifacts/6-3-merchant-csv-export.md`
- **GDPR Compliance:** `docs/project-context.md#gdprccpa-compliance`
- **Consent Service:** Story 6-1 (visitor_id-first pattern)
- **CSV Injection Prevention:** [OWASP CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection)
- **Message Encryption:** Story 5-11 (use `decrypted_content` for export)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial specification |
