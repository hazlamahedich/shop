# Widget Email Lookup Fix - Complete

## Issues Fixed

### Original Issue (Fixed Earlier)
When users used the widget to check order status by email, they received an LLM-generated summary instead of the detailed order status with product images and estimated delivery dates.

### New Issues (Fixed March 2026)

#### Issue 1: Bot responded with budget question instead of order ETA
**Scenario:** User typed `hazlamahedich@gmail,com` (comma instead of period)
- Bot didn't recognize the email due to strict regex
- Message fell through to LLM handler as "unknown" intent
- LLM hallucinated a budget question

**Root Cause:** Email regex was too strict - no typo tolerance

#### Issue 2: Bot asked for email again after it was provided
**Scenario:** User provided email (with typo), then asked "whats the status of my order"
- Email wasn't stored because it failed validation
- `pending_cross_device_lookup` flag remained `True`
- Bot had no memory of previous email attempt

**Root Cause:** 
- No fuzzy email matching
- No email extraction from conversation history
- LLM had no context about ongoing order lookup

## Root Cause Analysis

The problem was multi-layered:

### 1. **Metadata Not Persisting Between Requests**
- First request set `pending_cross_device_lookup: True` in `response.metadata`
- Widget didn't persist this metadata for the next request
- Second request couldn't find the pending flag, so it didn't route to OrderHandler

### 2. **Conversation Data vs Metadata Confusion**
- `context.conversation_data` - Persisted in database (✅ works)
- `context.metadata` - In-memory only (❌ lost between requests)
- OrderHandler checks BOTH locations, but widget only loaded conversation_data

### 3. **Intent Classification Interference**
- Without pending flag, email was classified as "general" intent
- Routed to LLM handler instead of OrderHandler
- LLM generated summary instead of detailed status

## Solution Implemented

### Fix 1: UnifiedConversationService - Pending Lookup Check

**File:** `backend/app/services/conversation/unified_conversation_service.py`

Added check before intent classification to route emails/order numbers directly to OrderHandler:

```python
# Story 4-13: Check for pending cross-device order lookup
from app.services.conversation.handlers.order_handler import PENDING_CROSS_DEVICE_KEY
conversation_data = context.conversation_data or {}
metadata = context.metadata or {}
pending_lookup = conversation_data.get(PENDING_CROSS_DEVICE_KEY) or metadata.get(
    PENDING_CROSS_DEVICE_KEY
)

if pending_lookup:
    # Check if message looks like email or order number
    import re
    email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    if email_pattern.match(message.strip()) or self._looks_like_order_number(message):
        # Route directly to OrderHandler
        handler = self._handlers["order"]
        llm_service = await self._get_merchant_llm(merchant, db, context)
        return await handler.handle(...)
```

### Fix 2: WidgetMessageService - Load Metadata from Conversation

**File:** `backend/app/services/widget/widget_message_service.py`

Updated to load conversation_data into BOTH `context.conversation_data` AND `context.metadata`:

```python
if conversation:
    context.conversation_data = conversation.decrypted_metadata
    
    # Also set context.metadata to conversation_data for pending flags
    # This ensures OrderHandler can check both locations
    context.metadata = conversation.decrypted_metadata or {}
```

### Fix 3: OrderHandler - Multiple Orders Support

**File:** `backend/app/services/conversation/handlers/order_handler.py`

Enhanced to show all orders (up to 5) with full details:

```python
orders = await customer_service.get_customer_orders(
    db=db,
    customer_profile_id=profile.id,
    limit=5,  # Changed from 1 to 5
)

if len(orders) == 1:
    # Show single order with details
    order = orders[0]
    product_images = await self._fetch_product_images(db, merchant, order)
    response_text = tracking_service.format_order_response(order, product_images)
else:
    # Show all orders with details
    response_parts = []
    for order in orders:
        product_images = await self._fetch_product_images(db, merchant, order)
        formatted = tracking_service.format_order_response(order, product_images)
        response_parts.append(formatted)
    response_text = "\n\n---\n\n".join(response_parts)
```

### Fix 4: Email Normalization with Typo Correction (March 2026)

**File:** `backend/app/services/conversation/handlers/order_handler.py`

Added robust email normalization to handle common typos:

```python
COMMON_DOMAIN_TYPOS = {
    "gmial": "gmail",
    "gmal": "gmail",
    "gamil": "gmail",
    "hotmal": "hotmail",
    "yaho": "yahoo",
    "outloo": "outlook",
}

def _normalize_email(self, message: str) -> Optional[str]:
    """Normalize and correct common email typos."""
    email = message.strip().lower()
    
    # Fix comma -> period (gmail,com -> gmail.com)
    email = email.replace(",", ".")
    
    # Fix double dots (gmail..com -> gmail.com)
    while ".." in email:
        email = email.replace("..", ".")
    
    # Fix common domain typos (gmial -> gmail)
    if "@" in email:
        parts = email.split("@")
        if len(parts) == 2:
            domain_parts = parts[1].split(".")
            if domain_parts[0] in COMMON_DOMAIN_TYPOS:
                domain_parts[0] = COMMON_DOMAIN_TYPOS[domain_parts[0]]
                email = f"{parts[0]}@{'.'.join(domain_parts)}"
    
    # Validate final result
    if EMAIL_PATTERN.match(email):
        return email
    return None
```

### Fix 5: Email Extraction from Conversation History (March 2026)

**File:** `backend/app/services/conversation/handlers/order_handler.py`

Added logic to scan conversation history for previously provided emails:

```python
def _extract_email_from_history(self, context: ConversationContext) -> Optional[str]:
    """Scan conversation history for previously provided email."""
    history = context.conversation_history or []
    
    # Check last 5 messages in reverse order (most recent first)
    for msg in reversed(history[-5:]):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            normalized = self._normalize_email(content)
            if normalized:
                return normalized
    return None
```

Now when `pending_cross_device_lookup` is True:
1. First check current message for email
2. If not found, scan last 5 messages for any valid email
3. If found, use it for lookup automatically

### Fix 6: LLM Context for Pending Order Lookup (March 2026)

**File:** `backend/app/services/personality/personality_prompts.py`

Added `pending_state` parameter to system prompt builder:

```python
def get_personality_system_prompt(
    personality: PersonalityType,
    # ... other params ...
    pending_state: Optional[dict] = None,
) -> str:
    # ... build prompt ...
    
    if pending_state:
        pending_context_parts = []
        if pending_state.get("pending_cross_device_lookup"):
            pending_context_parts.append(
                "IMPORTANT - ONGOING ORDER LOOKUP:\n"
                "You are in the middle of helping the customer check their order status. "
                "You previously asked for their email address or order number. "
                "If they provide an email or order number, acknowledge it and help them with their order. "
                "Do NOT ask about budgets, products, or other topics - stay focused on the order lookup."
            )
        if pending_context_parts:
            full_prompt += "CONVERSATION STATE:\n" + "\n".join(pending_context_parts) + "\n\n"
```

**File:** `backend/app/services/conversation/handlers/llm_handler.py`

Added `_get_pending_state()` method to extract pending state from context:

```python
def _get_pending_state(self, context: ConversationContext) -> Optional[dict]:
    """Extract pending state from conversation context."""
    conversation_data = context.conversation_data or {}
    metadata = context.metadata or {}
    
    pending_state = {}
    if conversation_data.get("pending_cross_device_lookup") or metadata.get("pending_cross_device_lookup"):
        pending_state["pending_cross_device_lookup"] = True
    
    return pending_state if pending_state else None
```

### Fix 7: Order Number Entity Extraction (March 2026)

**File:** `backend/app/services/intent/classification_schema.py`

Added `order_number` field to `ExtractedEntities`:

```python
class ExtractedEntities(BaseModel):
    # ... existing fields ...
    order_number: Optional[str] = Field(
        None,
        description="Order number for tracking (e.g., '#1003', 'ORD-123', '1003')",
    )
```

**File:** `backend/app/services/conversation/unified_conversation_service.py`

Added order number extraction pattern that matches:
- `#1003`, `order #1003`, `order 1003`, `order number 1003`
- Alphanumeric order numbers like `ORD-123`, `ABC-456`
- Ignores plain text like "order status", "order tracking"

```python
# Pattern matches order numbers with various formats
order_number_pattern = r"(?:^|\s)(?:#|order\s*(?:#|number|no\.?)?\s*)((?:[0-9][A-Za-z0-9\-]*|[A-Za-z]+[-][A-Za-z0-9\-]+|[A-Za-z]+[0-9][A-Za-z0-9\-]*))(?:\b|$)"
order_number_match = re.search(order_number_pattern, lower_msg)

if order_number_match:
    order_number = order_number_match.group(1).strip().lstrip("#")
    entities = ExtractedEntities(order_number=order_number)
```

## Test Results

### Test Script Results (✅ Working)

```
Step 1: User asks 'What's the status of my order?'
Bot Response: 
  "I couldn't find any orders linked to your account..."
  "I couldn't find orders on this device. 😊 I can look it up! What's your email address?"
  
✅ Pending cross-device lookup flag is set

Step 2: User provides email 'hazlamahedich@gmail.com'
Bot Response:
  📦 Order #1003
  Status: Processing
  Estimated Delivery: March 13, 2026
  
  📦 Order Items:
  1. Gift Card
     Quantity: 1
     Price: $10.00
     📷 Image: https://cdn.shopify.com/s/files/...
  
  💰 Payment Summary:
  Items: $10.00
  Total: $10.00
  Paid via: bogus

✅ Response contains detailed order status
✅ Response contains product images
✅ Response contains estimated delivery
```

### Widget Testing Steps

1. **Open widget** (merchant_id=6)
2. **Ask:** "What's the status of my order?"
3. **Expected:** Prompt for email with "I couldn't find orders on this device. 😊 I can look it up! What's your email address?"
4. **Provide:** "hazlamahedich@gmail.com"
5. **Expected:** Detailed order status with:
   - Order number
   - Status
   - Estimated delivery date
   - Product details with images
   - Payment summary

## Key Changes Summary

| Component | Change | Purpose |
|-----------|--------|---------|
| UnifiedConversationService | Added pending lookup check before intent classification | Route emails/order numbers to OrderHandler |
| UnifiedConversationService | Added order number extraction pattern | Extract order number from messages |
| WidgetMessageService | Load conversation_data into both context.conversation_data and context.metadata | Preserve pending flags across requests |
| OrderHandler | Changed limit from 1 to 5 orders, show all with details | Display all orders with full information |
| OrderHandler | Added product image fetching for all orders | Show product images in response |
| OrderHandler | Added email normalization with typo correction | Handle email typos like gmail,com |
| OrderHandler | Added email extraction from conversation history | Use previously provided emails |
| LLMHandler | Added pending_state to system prompt | Keep LLM focused on order lookup |
| classification_schema | Added order_number field to ExtractedEntities | Support order number entity extraction |

### Check if metadata is loaded:
```python
# In widget_message_service.py after loading conversation
print(f"context.conversation_data: {context.conversation_data}")
print(f"context.metadata: {context.metadata}")
```

### Check routing:
```python
# In unified_conversation_service.py
if pending_lookup and email_match:
    print("✅ Routing to OrderHandler for email lookup")
```

## Known Limitations

1. **Consent Flow**: If user hasn't granted consent, conversation_data may not persist to database
2. **Session Storage**: Widget sessions don't have metadata field, so we rely on database conversation metadata
3. **Rate Limiting**: Multiple product image fetches may trigger Shopify API limits

## Future Improvements

1. ~~Add metadata field to WidgetSessionData for better state management~~ ✅ Done - using conversation_data
2. Cache product images to reduce Shopify API calls
3. Add pagination for customers with many orders
4. ~~Support order number input in any message (not just after prompt)~~ ✅ Done - added order_number extraction

## Remaining Improvements

1. Add LLM-based entity extraction for more robust order number/email detection
2. Add Shopify Admin API order lookup for real-time status
3. Cache product images to reduce Shopify API calls
4. Add pagination for customers with many orders

## Related Documentation

- `EMAIL_ORDER_LOOKUP_FIX.md` - Initial fix documentation
- `ORDER_STATUS_ENHANCEMENTS_COMPLETE.md` - Product images and delivery dates
- Story 4-13: Cross-device order lookup
- Story 5-13: Product images and estimated delivery

---

**Last Updated:** March 9, 2026
