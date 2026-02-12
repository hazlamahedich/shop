# Business Info & FAQ API Documentation

**Story 1.11: Business Info & FAQ Configuration**

This API allows merchants to configure their business information and manage FAQ items for the conversational bot.

## Base URL

```
/api/v1/merchant
```

## Authentication

All endpoints require merchant authentication. The merchant ID should be provided via:
- `X-Merchant-Id` header (DEBUG mode only)
- Session authentication (production)

---

## Business Info Endpoints

### Get Business Info

Retrieve the current merchant's business information.

**Endpoint:** `GET /business-info`

**Authentication:** Required

**Request:**
```http
GET /api/v1/merchant/business-info
X-Merchant-Id: 1
```

**Response (200 OK):**
```json
{
  "data": {
    "businessName": "Alex's Athletic Gear",
    "businessDescription": "Premium athletic apparel and equipment",
    "businessHours": "9 AM - 6 PM PST, Mon-Sat"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Field Constraints:**
- `businessName`: string (nullable), max 100 characters
- `businessDescription`: string (nullable), max 500 characters
- `businessHours`: string (nullable), max 100 characters

---

### Update Business Info

Update the merchant's business information. All fields are optional - only provided fields will be updated.

**Endpoint:** `PUT /business-info`

**Authentication:** Required

**Request:**
```http
PUT /api/v1/merchant/business-info
Content-Type: application/json

{
  "business_name": "Alex's Athletic Gear",
  "business_description": "Premium athletic apparel and equipment",
  "business_hours": "9 AM - 6 PM PST, Mon-Sat"
}
```

**Request Body:**
| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| business_name | string | No | 100 | Name of the business |
| business_description | string | No | 500 | Brief description for bot context |
| business_hours | string | No | 100 | Business operating hours |

**Response (200 OK):**
```json
{
  "data": {
    "businessName": "Alex's Athletic Gear",
    "businessDescription": "Premium athletic apparel and equipment",
    "businessHours": "9 AM - 6 PM PST, Mon-Sat"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | 3001 | Validation error (field exceeds max length) |
| 401 | 1001 | Authentication failed |
| 404 | 2003 | Merchant not found |
| 500 | 1000 | Internal server error |

---

## FAQ Endpoints

### List FAQs

Retrieve all FAQ items for the authenticated merchant, ordered by `orderIndex`.

**Endpoint:** `GET /faqs`

**Authentication:** Required

**Request:**
```http
GET /api/v1/merchant/faqs
X-Merchant-Id: 1
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "question": "What are your shipping options?",
      "answer": "We offer free shipping on orders over $50.",
      "keywords": "shipping,delivery,free",
      "orderIndex": 0,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "question": "Do you accept returns?",
      "answer": "Yes, within 30 days of purchase.",
      "keywords": "returns,refund",
      "orderIndex": 1,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

### Create FAQ

Create a new FAQ item. The FAQ will be added at the end of the list.

**Endpoint:** `POST /faqs`

**Authentication:** Required

**Request:**
```http
POST /api/v1/merchant/faqs
Content-Type: application/json

{
  "question": "What are your shipping options?",
  "answer": "We offer free shipping on orders over $50.",
  "keywords": "shipping,delivery",
  "order_index": 0
}
```

**Request Body:**
| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| question | string | Yes | 200 | The FAQ question |
| answer | string | Yes | 1000 | The FAQ answer |
| keywords | string | No | 500 | Comma-separated keywords for matching |
| order_index | number | No | - | Position in list (default: end) |

**Response (201 Created):**
```json
{
  "data": {
    "id": 3,
    "question": "What are your shipping options?",
    "answer": "We offer free shipping on orders over $50.",
    "keywords": "shipping,delivery",
    "orderIndex": 2,
    "createdAt": "2024-01-01T12:00:00Z",
    "updatedAt": "2024-01-01T12:00:00Z"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

### Update FAQ

Update an existing FAQ item. Only provided fields will be updated.

**Endpoint:** `PUT /faqs/{faq_id}`

**Authentication:** Required

**Path Parameters:**
- `faq_id` (number, required): ID of the FAQ to update

**Request:**
```http
PUT /api/v1/merchant/faqs/3
Content-Type: application/json

{
  "question": "What shipping options are available?",
  "answer": "We offer free standard shipping (3-5 days) on orders over $50, and expedited shipping (1-2 days) for $10.",
  "keywords": "shipping,delivery,expedited"
}
```

**Request Body:**
| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| question | string | No | 200 | Updated question |
| answer | string | No | 1000 | Updated answer |
| keywords | string | No | 500 | Updated keywords |
| order_index | number | No | - | New position in list |

**Response (200 OK):**
```json
{
  "data": {
    "id": 3,
    "question": "What shipping options are available?",
    "answer": "We offer free standard shipping (3-5 days) on orders over $50, and expedited shipping (1-2 days) for $10.",
    "keywords": "shipping,delivery,expedited",
    "orderIndex": 2,
    "createdAt": "2024-01-01T12:00:00Z",
    "updatedAt": "2024-01-01T12:01:00Z"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:01:00Z"
  }
}
```

---

### Delete FAQ

Permanently delete an FAQ item. Remaining FAQs will have their `orderIndex` values adjusted.

**Endpoint:** `DELETE /faqs/{faq_id}`

**Authentication:** Required

**Path Parameters:**
- `faq_id` (number, required): ID of the FAQ to delete

**Request:**
```http
DELETE /api/v1/merchant/faqs/3
X-Merchant-Id: 1
```

**Response (204 No Content):**
```
(no response body)
```

---

### Reorder FAQs

Specify the exact order of FAQs by providing an ordered list of FAQ IDs.

**Endpoint:** `PUT /faqs/reorder`

**Authentication:** Required

**Request:**
```http
PUT /api/v1/merchant/faqs/reorder
Content-Type: application/json

{
  "faq_ids": [3, 1, 2]
}
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| faq_ids | number[] | Yes | Ordered list of FAQ IDs |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 3,
      "question": "What shipping options are available?",
      "answer": "We offer free standard shipping...",
      "keywords": "shipping,delivery",
      "orderIndex": 0,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T12:01:00Z"
    },
    {
      "id": 1,
      "question": "Do you accept returns?",
      "answer": "Yes, within 30 days of purchase.",
      "keywords": "returns,refund",
      "orderIndex": 1,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "question": "What payment methods do you accept?",
      "answer": "We accept Visa, MasterCard, and PayPal.",
      "keywords": "payment",
      "orderIndex": 2,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:02:00Z"
  }
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | 3000 | Validation error |
| 401 | 1001 | Authentication failed |
| 403 | 1002 | Access denied (FAQ belongs to another merchant) |
| 404 | 2001 | FAQ not found |
| 422 | 3000 | Invalid reorder data (empty list, invalid IDs) |
| 500 | 1000 | Internal server error |

---

## Data Types

### BusinessInfoRequest
```typescript
{
  business_name?: string;     // max 100
  business_description?: string; // max 500
  business_hours?: string;     // max 100
}
```

### BusinessInfoResponse
```typescript
{
  businessName: string | null;
  businessDescription: string | null;
  businessHours: string | null;
}
```

### FaqRequest (Create)
```typescript
{
  question: string;     // max 200, required
  answer: string;       // max 1000, required
  keywords?: string;    // max 500, optional
  order_index?: number; // optional
}
```

### FaqUpdateRequest
```typescript
{
  question?: string;    // max 200
  answer?: string;      // max 1000
  keywords?: string;    // max 500
  order_index?: number;
}
```

### FaqResponse
```typescript
{
  id: number;
  question: string;
  answer: string;
  keywords: string | null;
  orderIndex: number;
  createdAt: string;     // ISO 8601 timestamp
  updatedAt: string;     // ISO 8601 timestamp
}
```

---

## Usage Examples

### Complete Business Info Setup Flow

```javascript
// 1. Fetch current business info
const info = await fetch('/api/v1/merchant/business-info', {
  headers: { 'X-Merchant-Id': '1' }
}).then(r => r.json());

// 2. Update business information
await fetch('/api/v1/merchant/business-info', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Id': '1'
  },
  body: JSON.stringify({
    business_name: "Alex's Athletic Gear",
    business_description: 'Premium athletic apparel',
    business_hours: '9 AM - 6 PM PST'
  })
});
```

### Complete FAQ Management Flow

```javascript
// 1. List all FAQs
const faqs = await fetch('/api/v1/merchant/faqs', {
  headers: { 'X-Merchant-Id': '1' }
}).then(r => r.json());

// 2. Create new FAQ
const newFaq = await fetch('/api/v1/merchant/faqs', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Id': '1'
  },
  body: JSON.stringify({
    question: 'What are your hours?',
    answer: '9 AM - 6 PM PST, Mon-Sat',
    keywords: 'hours,time,open'
  })
}).then(r => r.json());

// 3. Update FAQ
await fetch(`/api/v1/merchant/faqs/${newFaq.data.id}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Id': '1'
  },
  body: JSON.stringify({
    answer: '9 AM - 8 PM PST, Mon-Sat'
  })
});

// 4. Reorder FAQs
await fetch('/api/v1/merchant/faqs/reorder', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Id': '1'
  },
  body: JSON.stringify({
    faq_ids: [newFaq.data.id, 1, 2, 3]
  })
});

// 5. Delete FAQ
await fetch(`/api/v1/merchant/faqs/${newFaq.data.id}`, {
  method: 'DELETE',
  headers: { 'X-Merchant-Id': '1' }
});
```

---

## Common Errors

### Error Response Format
```json
{
  "detail": {
    "error_code": 1000,
    "message": "Error description",
    "details": {}
  }
}
```

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 1000 | INTERNAL_ERROR | Unexpected server error |
| 1001 | AUTH_FAILED | Authentication required |
| 1002 | FORBIDDEN | Access denied |
| 2001 | NOT_FOUND | Resource not found |
| 2003 | MERCHANT_NOT_FOUND | Merchant does not exist |
| 3000 | VALIDATION_ERROR | Request validation failed |
| 3001 | INVALID_FIELD_VALUE | Field exceeds max length |

---

## Notes

1. **Character Limits**: All string fields have maximum lengths enforced at the API level
2. **Whitespace**: Input values are automatically trimmed before storage
3. **Empty Strings**: Empty strings after trimming are stored as `null`
4. **Order Index**: The `orderIndex` field determines FAQ display order
5. **Isolation**: Merchants can only access their own business info and FAQs
6. **Persistence**: Business info and FAQs are persisted in the database
