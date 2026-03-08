# FAQ Personality Rephrasing Feature

## Summary
Added personality-aware rephrasing to FAQ answers to the bot, Provides consistent, friendly, professional, and enthusiastic responses that maintaining the bot's personality tone.

## Implementation

### 1. New Function: `rephrase_faq_with_personality()` in `app/services/faq.py`

Rephrases FAQ answers through LLM with personality-appropriate prompts:
 Does so the answer can sound natural and conversational.

### 2. Updated Services

| Service | Changes |
|-------|------|
| `message_processor.py` (Messenger) | Added `_get_llm_service_for_faq()` and personality rephrasing |
| `preview_service.py` | Added personality rephrasing for FAQ matches |
| `faq_preprocessor.py` | Added `llm_service` and `merchant` parameters for personality |
| `unified_conversation_service.py` | Added `_check_faq_match()` method with personality rephrasing |

### 3. Flow
```
User Message → FAQ Match Check → Personality Rephrase → Return Response
```

```python
async def rephrase_faq_with_personality(
    llm_service: BaseLLMService,
    faq_answer: str,
    personality_type: PersonalityType
    business_name: str,
    bot_name: str = "Shopping Assistant",
    timeout_seconds: float = 3.0,
) -> str:
    ...
```
</docstring>
<rephrase_prompt>
Rewrite this FAQ answer in your personality tone. Keep the same information but make it sound natural and conversational.
Do NOT add new information or change the meaning.
- Only rephrase what is explicitly stated in the original answer
- Output ONLY the rephrased answer,- Do NOT mention pages or resources not in the original answer
- Do NOT add placeholders like [text](url)

</prompt>
```

### Test Coverage
- Unit tests for `tests/services/test_faq_personality.py`
- All existing FAQ tests continue to pass

### Error Handling
- LLM timeout (>3s): Falls back to raw answer
- LLM error: Falls back to raw answer
- Missing LLM config: Falls back to raw answer

### Files Modified
- `backend/app/services/faq.py` - Added `rephrase_faq_with_personality()` function
- `backend/app/services/messaging/message_processor.py` - Updated `_check_faq_match()` 
- `backend/app/services/preview/preview_service.py` - Updated FAQ handling
- `backend/app/services/conversation/preprocessors/faq_preprocessor.py` - Added personality rephrasing support
- `backend/app/services/conversation/unified_conversation_service.py` - Added `_check_faq_match()` method

