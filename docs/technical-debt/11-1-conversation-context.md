# Technical Debt: Story 11-1 Conversation Context Memory

**Last Updated:** 2026-03-31
**Story:** 11-1 Conversation Context Memory
**Status:** Implementation Complete, Technical Debt Tracked

---

## Debt Items

### 1. Regex vs LLM Context Extraction ⚠️ MEDIUM Priority

**Current State:**
- `EcommerceContextExtractor` and `GeneralContextExtractor` use regex patterns
- Extraction is rule-based with limited context understanding
- Works for MVP but lacks nuance and flexibility

**Original Requirement (Dev Notes line 243):**
> "Use LLM to extract context from user messages with mode-specific prompts"

**Current Implementation:**
```python
# File: app/services/context/ecommerce_context.py
class EcommerceContextExtractor:
    def extract(self, message: str, existing_context: dict) -> dict:
        # Uses regex patterns like:
        # r'\$(\d+(?:\.\d{2})?)' for prices
        # r'product\s+(\d+)' for product IDs
        # Limited to predefined patterns
```

**Issues:**
- ❌ Cannot understand complex sentences: "I want something affordable that looks good"
- ❌ Misses implicit context: "in blue" refers back to previously mentioned products
- ❌ Cannot handle variations: "show me cheap stuff" vs "under $50"
- ❌ No sentiment or urgency detection
- ❌ Cannot extract multi-constraint queries: "red or blue under $100"

**Recommended Solution:**

```python
# File: app/services/context/llm_context_extractor.py
class LLMContextExtractor:
    """Extract context using LLM with mode-aware prompts."""

    def __init__(self, llm_service: BaseLLMService):
        self.llm = llm_service

    async def extract(self, message: str, mode: str, existing_context: dict) -> dict:
        """Extract context using LLM with mode-specific prompts."""

        if mode == "ecommerce":
            system_prompt = """
            You are a context extraction expert for e-commerce conversations.
            Extract the following from the user message:
            - product_ids: List of product IDs mentioned (integers)
            - price_constraints: Budget/price limits
            - size_preferences: Size requirements
            - color_preferences: Color requirements
            - categories: Product categories of interest
            - urgency: How urgent the request is (immediate/soon/eventual)

            Return ONLY valid JSON.
            """
        else:  # general mode
            system_prompt = """
            You are a context extraction expert for customer support.
            Extract the following from the user message:
            - topics: Main topics discussed
            - issues: Problems or complaints mentioned
            - escalation_needed: Whether this requires human intervention
            - sentiment: Customer sentiment (positive/neutral/negative)
            - urgency: How urgent the issue is

            Return ONLY valid JSON.
            """

        response = await self.llm.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Existing context: {existing_context}\n\nUser message: {message}"}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            response_format="json"
        )

        return self._parse_and_validate(response)
```

**Benefits:**
- ✅ Understands complex, multi-part queries
- ✅ Handles implicit references to previous context
- ✅ Extracts sentiment and urgency
- ✅ Adapts to conversation flow
- ✅ No need to maintain regex patterns

**Implementation Effort:** 2-3 days
- Create `LLMContextExtractor` class
- Add mode-specific system prompts
- Update `ConversationContextService` to use LLM extractor
- Add tests for LLM-based extraction
- Update documentation

---

### 2. Mode-Aware Prompts in LLMHandler ⚠️ LOW Priority

**Current State:**
- `ContextSummarizerService` has mode-aware prompts (ecommerce vs general)
- `LLMHandler` lacks mode-specific prompt variations for bot responses
- All conversations use same prompt template regardless of mode

**Current Implementation:**
```python
# File: app/services/conversation/handlers/llm_handler.py
class LLMHandler:
    async def generate_response(
        self,
        conversation: ConversationContext,
        merchant: Merchant,
        message: str,
        mode: str  # Mode is passed but not used for prompt customization
    ) -> str:
        # Mode is ignored, same prompt for both ecommerce and general
        system_prompt = self._build_system_prompt(merchant)  # No mode parameter
```

**Issue:**
- ❌ E-commerce conversations don't get product-aware prompts
- ❌ General conversations don't get support-aware prompts
- ❌ Missed opportunity for mode-specific personality and tone

**Recommended Solution:**

```python
# File: app/services/conversation/handlers/llm_handler.py
class LLMHandler:
    def _build_system_prompt(self, merchant: Merchant, mode: str) -> str:
        """Build mode-aware system prompt."""

        base_prompt = f"""You are {merchant.bot_name}, a helpful assistant for {merchant.business_name}.
        Your personality is {merchant.personality}."""

        if mode == "ecommerce":
            ecommerce_instructions = """
            You are helping a customer shop for products.

            Guidelines:
            - Be enthusiastic and product-focused
            - Use product names and details from context
            - Suggest alternatives if requested product unavailable
            - Ask clarifying questions about size, color, budget
            - Remember preferences mentioned earlier
            - Be helpful with comparisons and recommendations
            """
            return base_prompt + ecommerce_instructions

        else:  # general mode
            support_instructions = """
            You are helping a customer with support or general inquiries.

            Guidelines:
            - Be empathetic and patient
            - Focus on resolving their issue
            - Ask for order number/account info if needed
            - Escalate if issue is complex or customer is upset
            - Remember previous context in the conversation
            - Be clear and actionable in your responses
            """
            return base_prompt + support_instructions
```

**Benefits:**
- ✅ Better customer experience with mode-appropriate responses
- ✅ Higher conversion in e-commerce mode
- ✅ Better resolution rates in support mode
- ✅ Clearer separation of concerns

**Implementation Effort:** 1-2 days
- Update `_build_system_prompt()` to accept `mode` parameter
- Create mode-specific prompt templates
- Add tests for mode-aware prompts
- Update integration tests

---

## Priority Matrix

| Item | Priority | Effort | Impact | ROI |
|------|----------|--------|--------|-----|
| LLM Context Extraction | MEDIUM | 2-3 days | HIGH | HIGH |
| Mode-Aware LLM Prompts | LOW | 1-2 days | MEDIUM | MEDIUM |

**Recommendation:** Implement LLM Context Extraction first as it has higher impact and ROI.

---

## Testing Checklist for Debt Resolution

### LLM Context Extraction
- [ ] Test simple extraction: "Show me red shoes under $50"
- [ ] Test complex extraction: "I want something comfortable for running that looks professional"
- [ ] Test implicit references: "What about in blue?" (after showing shoes)
- [ ] Test multi-constraint: "red or blue under $100 in size 10"
- [ ] Test sentiment extraction: angry/happy/neutral messages
- [ ] Test edge cases: empty messages, gibberish, multiple languages
- [ ] Performance: < 500ms per extraction (with LLM caching)
- [ ] Cost: Monitor token usage, implement caching

### Mode-Aware LLM Prompts
- [ ] Test e-commerce mode prompt tone and style
- [ ] Test general mode prompt tone and style
- [ ] Verify mode switching works correctly
- [ ] Test personality consistency across modes
- [ ] Test escalation detection in general mode
- [ ] Test product recommendations in e-commerce mode

---

## Migration Strategy

### Phase 1: LLM Context Extraction (Week 1-2)
1. Create `LLMContextExtractor` class
2. Add feature flag: `USE_LLM_EXTRACTION=true`
3. Deploy with feature flag off
4. Run A/B test: regex vs LLM extraction
5. Measure: accuracy, customer satisfaction, token cost
6. Enable feature flag for 10% of traffic
7. Monitor and iterate
8. Roll out to 100%

### Phase 2: Mode-Aware Prompts (Week 3)
1. Update `_build_system_prompt()` with mode parameter
2. Add mode-aware prompt templates
3. Deploy behind feature flag: `USE_MODE_AWARE_PROMPTS=true`
4. A/B test with current prompts
5. Measure: conversion rate, resolution time, customer feedback
6. Roll out gradually

---

## Metrics to Track

### LLM Context Extraction
- **Accuracy:** % of correctly extracted context (manual sample review)
- **Customer Satisfaction:** Post-conversation surveys
- **Conversion Rate:** E-commerce mode purchase completion
- **Token Cost:** LLM API costs per 1000 conversations
- **Latency:** Average extraction time
- **Cache Hit Rate:** % of extractions served from cache

### Mode-Aware Prompts
- **Resolution Rate:** % of issues resolved in one interaction
- **Customer Effort Score:** How easy was the interaction?
- **Escalation Rate:** % of conversations escalated to human
- **Conversion Rate:** E-commerce mode purchase completion
- **Sentiment Score:** Average customer sentiment
- **Response Quality:** Human evaluation sample

---

## Rollback Plan

If issues arise:

1. **LLM Context Extraction:**
   - Feature flag off: Revert to regex extraction
   - Degrade gracefully: Use regex if LLM fails
   - Fallback: Hybrid approach (LLM for complex, regex for simple)

2. **Mode-Aware Prompts:**
   - Feature flag off: Use generic prompts
   - Rollback commit: Revert to previous prompt version
   - Quick fix: Adjust prompt templates without code change

---

## Related Documentation

- Story 11-1: Conversation Context Memory
- Dev Notes (line 243): LLM-based context extraction requirement
- Architecture: Context Extraction Strategy
- Performance: LLM Caching Strategy

---

## Questions?

Contact: @sherwing (Product Owner)
Tech Lead: @backend-team
Created: 2026-03-31
