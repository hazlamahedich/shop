# RAG Response Type Breakdown Fix

## Issue
The response type breakdown in the Response Time Widget was not updating - all values were showing as blank.

## Root Cause
Three issues were preventing the `response_type` field from being properly tracked:

1. **Variable name bug in `llm_cost_wrapper.py`** (line 121)
   - Used undefined variable `llm_response` instead of `response`
   - Used undefined variable `response_type` which was never set

2. **Missing response_type in LLM handler metadata** (`llm_handler.py`)
   - The handler wasn't setting `response_type` in the response metadata
   - This meant the cost tracker couldn't determine if the response was RAG or general

3. **Missing response_type in budget-aware wrapper** (`budget_aware_llm_wrapper.py`)
   - The wrapper wasn't passing `response_type` to the cost tracking function

## Changes Made

### 1. Fixed `llm_cost_wrapper.py` (lines 113-127)
```python
# Before:
await track_llm_request(
    db=self.db,
    llm_response=llm_response,  # ❌ undefined
    response_type=response_type,  # ❌ undefined
)

# After:
# Determine response type from metadata
response_type = "unknown"
if hasattr(response, "metadata") and response.metadata:
    response_type = response.metadata.get("response_type", "unknown")

await track_llm_request(
    db=self.db,
    llm_response=response,  # ✅ correct variable
    response_type=response_type,  # ✅ now defined
)
```

### 2. Updated `llm_handler.py` (lines 158-171)
```python
# Determine response type based on whether RAG context was used
response_type = "rag" if rag_context else "general"

return ConversationResponse(
    message=response_text,
    intent="general",
    confidence=1.0,
    products=products,
    quick_replies=quick_replies,
    metadata={
        "bot_name": bot_name,
        "business_name": business_name,
        "response_type": response_type,  # ✅ now included
    },
)
```

### 3. Updated `budget_aware_llm_wrapper.py` (lines 183-193)
```python
# Extract response_type from response metadata
response_type = "unknown"
if hasattr(response, "metadata") and response.metadata:
    response_type = response.metadata.get("response_type", "unknown")

if self.track_costs:
    try:
        await track_llm_request(
            db=self.db,
            llm_response=response,
            conversation_id=self.conversation_id,
            merchant_id=self.merchant_id,
            processing_time_ms=processing_time_ms,
            response_type=response_type,  # ✅ now passed
        )
```

## How It Works Now

1. **LLM Handler determines response type**: When generating a response, the handler checks if RAG context was used and sets `response_type` to "rag" or "general" in the metadata

2. **LLM Response carries metadata**: The `LLMResponse` object includes the `response_type` in its metadata

3. **Cost tracking extracts and stores**: The cost tracking wrappers extract the `response_type` from metadata and pass it to `track_llm_request()`

4. **Database stores response type**: The `LLMConversationCost` record is created with the correct `response_type` value

5. **Analytics query retrieves breakdown**: The response time distribution API queries the database and returns the breakdown by response type

## Testing

To verify the fix:

1. Send a message that triggers RAG (requires knowledge base)
2. Send a message that doesn't use RAG (greeting, general chat)
3. Check the Response Time Widget - should now show:
   - RAG: P50, P95, P99 values and count
   - General: P50, P95, P99 values and count

## Files Changed
- `/backend/app/services/cost_tracking/llm_cost_wrapper.py`
- `/backend/app/services/conversation/handlers/llm_handler.py`
- `/backend/app/services/cost_tracking/budget_aware_llm_wrapper.py`

## Related
- Story 10-9: Response Time Widget (AC5: Response type breakdown)
- `LLMConversationCost` model with `response_type` field
- Response time distribution API endpoint
