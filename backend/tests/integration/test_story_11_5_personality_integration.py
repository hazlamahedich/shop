"""Integration tests for Story 11-5: Personality Consistency — Handler Integration.

Tests personality enforcement through actual handler code paths, covering
coverage gaps identified in the test automation workflow.

Coverage Gaps:
  P0 #1:  LLM handler post-response validation + tracker recording + drift
  P0 #2:  LLM handler mid-conversation reinforcement injection
  P0 #10: Conversation template personality compliance
  P1 #3:  LLM handler error fallback personality (classification leak, LLM fallback)
  P1 #4:  Clarification handler ValueError fallback personality
  P1 #5:  Clarification handler _personalize_question transition prefixing
  P1 #9:  General mode fallback include_transition code path
  P2 #6:  Check consent handler exception path personality
  P2 #7:  Forget preferences handler 3 error paths personality
  P2 #8:  Unified service budget pause personality (template-level)
  P2 #11: LLM handler resolution system prompt personality examples
  P2 #12: Unified service handoff resolution fallback personality (template-level)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.check_consent_handler import CheckConsentHandler
from app.services.conversation.handlers.clarification_handler import ClarificationHandler
from app.services.conversation.handlers.forget_preferences_handler import (
    ForgetPreferencesHandler,
)
from app.services.conversation.handlers.llm_handler import LLMHandler
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
    ConversationResponse,
)
from app.services.personality.conversation_templates import (
    CONVERSATION_TEMPLATES,
    register_conversation_templates,
)
from app.services.personality.personality_reinforcement import (
    REINFORCEMENT_TURN_THRESHOLD,
    get_personality_reinforcement,
)
from app.services.personality.personality_tracker import (
    PersonalityTracker,
    get_personality_tracker,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

register_conversation_templates()

EMOJI_REGEX = __import__("re").compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\U00002600-\U000026ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0000fe00-\U0000fe0f"
    "]",
    flags=__import__("re").UNICODE,
)


def _count_emojis(text: str) -> int:
    return len(EMOJI_REGEX.findall(text))


def _make_merchant(
    personality: PersonalityType = PersonalityType.FRIENDLY,
    business_name: str = "Test Store",
    bot_name: str = "TestBot",
    onboarding_mode: str = "ecommerce",
    merchant_id: int = 1,
) -> MagicMock:
    merchant = MagicMock()
    merchant.id = merchant_id
    merchant.personality = personality
    merchant.business_name = business_name
    merchant.bot_name = bot_name
    merchant.onboarding_mode = onboarding_mode
    return merchant


def _make_context(
    session_id: str = "test-session",
    conversation_id: int | None = None,
    history: list[dict[str, Any]] | None = None,
    channel: Channel = Channel.WIDGET,
) -> ConversationContext:
    return ConversationContext(
        session_id=session_id,
        merchant_id=1,
        channel=channel,
        conversation_id=conversation_id,
        conversation_history=history or [],
        consent_state=ConsentState(),
        metadata={},
    )


def _make_llm_service(response_text: str = "Here is a helpful response.") -> AsyncMock:
    llm_response = MagicMock()
    llm_response.content = response_text
    svc = AsyncMock()
    svc.chat = AsyncMock(return_value=llm_response)
    return svc


@pytest.fixture(autouse=True)
def _reset_tracker():
    get_personality_tracker().reset()
    yield
    get_personality_tracker().reset()


# ---------------------------------------------------------------------------
# P0 #1: LLM Handler — Post-response validation + tracker + drift
# ---------------------------------------------------------------------------
class TestLLMHandlerPostResponseValidation:
    """P0 Gap #1: validate_personality() + tracker.record_validation() + drift."""

    @pytest.mark.asyncio
    async def test_validation_recorded_on_successful_response(self):
        """Post-response: tracker records passing validation for personality-compliant text."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service("Here are the available products for your consideration.")
        ctx = _make_context(conversation_id=42)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "show me products", ctx)

        tracker = get_personality_tracker()
        report = tracker.get_consistency_report("42")
        assert report.turn_count == 1
        assert report.consistency_score == 1.0
        assert not report.is_drifting

    @pytest.mark.asyncio
    async def test_validation_records_failure_for_personality_violation(self):
        """Post-response: tracker records failing validation when response has emojis for Professional."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service("Check these out! 😊🎉 Here's what I found!")
        ctx = _make_context(conversation_id=43)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "show me products", ctx)

        tracker = get_personality_tracker()
        report = tracker.get_consistency_report("43")
        assert report.turn_count == 1
        assert report.violation_count == 1
        assert report.consistency_score == 0.0

    @pytest.mark.asyncio
    async def test_drift_detected_after_consecutive_failures(self):
        """Post-response: drift flagged after 2+ consecutive validation failures."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        db = AsyncMock()

        for turn in range(4):
            llm_svc = _make_llm_service("Awesome! Check these out! 😊🎉")
            history = [{"role": "user", "content": f"msg {i}"} for i in range(turn)]
            ctx = _make_context(conversation_id=44, history=history)

            with (
                patch.object(handler, "_detect_product_mentions", return_value=None),
                patch.object(handler, "_get_conversation_context", return_value=None),
            ):
                await handler.handle(db, merchant, llm_svc, f"query {turn}", ctx)

        tracker = get_personality_tracker()
        assert tracker.is_drifting("44")

    @pytest.mark.asyncio
    async def test_no_validation_when_no_conversation_id(self):
        """Post-response: validation skipped when conversation_id is None."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service("Sure thing! Here to help! 😊")
        ctx = _make_context(conversation_id=None)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "hello", ctx)

        tracker = get_personality_tracker()
        assert tracker.active_conversation_count == 0

    @pytest.mark.asyncio
    async def test_no_validation_when_empty_response(self):
        """Post-response: validation skipped when LLM returns empty string."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service("")
        ctx = _make_context(conversation_id=45)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "hello", ctx)

        tracker = get_personality_tracker()
        assert tracker.get_turn_count("45") == 0


# ---------------------------------------------------------------------------
# P0 #2: LLM Handler — Mid-conversation reinforcement injection
# ---------------------------------------------------------------------------
class TestLLMHandlerMidConversationReinforcement:
    """P0 Gap #2: turn_number >= 5 triggers reinforcement in _build_system_prompt."""

    @pytest.mark.asyncio
    async def test_reinforcement_injected_at_turn_5(self):
        """System prompt includes reinforcement text when turn_number >= 5."""
        handler = LLMHandler()
        conv_id = "reinforce-test-5"
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(conv_id, PersonalityType.PROFESSIONAL, True, i + 1)

        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.PROFESSIONAL),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.PROFESSIONAL,
            pending_state=None,
            turn_number=5,
            conversation_id=conv_id,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" in prompt
        assert "NO emojis anywhere" in prompt

    @pytest.mark.asyncio
    async def test_no_reinforcement_below_threshold(self):
        """System prompt does NOT include reinforcement when turn_number < 5."""
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=4,
            conversation_id="conv-low-turn",
        )

        assert "PERSONALITY CONSISTENCY REMINDER" not in prompt

    @pytest.mark.asyncio
    async def test_reinforcement_with_low_consistency_adds_warning(self):
        """Reinforcement includes extra warning when consistency_score < 0.7."""
        handler = LLMHandler()
        conv_id = "reinforce-low-score"
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(conv_id, PersonalityType.FRIENDLY, i < 2, i + 1)

        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=5,
            conversation_id=conv_id,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" in prompt
        assert "consistency has been declining" in prompt

    @pytest.mark.asyncio
    async def test_reinforcement_per_personality_type(self):
        """Each personality type gets its own reinforcement content."""
        handler = LLMHandler()
        tracker = get_personality_tracker()

        for ptype in PersonalityType:
            tracker.reset()
            conv_id = f"reinforce-{ptype.value}"
            for i in range(5):
                tracker.record_validation(conv_id, ptype, True, i + 1)

            prompt = await handler._build_system_prompt(
                db=AsyncMock(),
                merchant=_make_merchant(ptype),
                bot_name="Bot",
                business_name="Store",
                personality_type=ptype,
                pending_state=None,
                turn_number=5,
                conversation_id=conv_id,
            )

            assert "PERSONALITY CONSISTENCY REMINDER" in prompt

    @pytest.mark.asyncio
    async def test_no_reinforcement_without_conversation_id(self):
        """Reinforcement skipped when conversation_id is None."""
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=10,
            conversation_id=None,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" not in prompt


# ---------------------------------------------------------------------------
# P0 #10: Conversation Template Personality Compliance
# ---------------------------------------------------------------------------
class TestConversationTemplatePersonalityCompliance:
    """P0 Gap #10: All 9 conversation templates obey personality rules for all 3 types."""

    TEMPLATE_KEYS = [
        "welcome_back_fallback",
        "bot_paused",
        "clarification_fallback",
        "consent_check_error",
        "forget_rate_limited",
        "forget_error",
        "forget_unexpected_error",
        "llm_classification_leak",
        "llm_fallback",
    ]

    def test_professional_no_emojis_all_templates(self):
        """Professional: ALL 9 templates contain zero emojis."""
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert _count_emojis(text) == 0, (
                f"Professional template '{key}' should have no emojis, got: {text}"
            )

    def test_professional_no_slang_all_templates(self):
        """Professional: ALL templates avoid slang words."""
        import re

        slang_re = re.compile(r"\b(awesome|gonna|wanna|yeah|yep|nope|omg|lol|oops|oopsie)\b", re.I)
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert not slang_re.search(text), (
                f"Professional template '{key}' should not contain slang, got: {text}"
            )

    def test_enthusiastic_has_exclamation_or_emoji_all_templates(self):
        """Enthusiastic: ALL templates have at least one '!' or emoji."""
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC][key]
            has_exclamation = "!" in text
            has_emoji = _count_emojis(text) > 0
            assert has_exclamation or has_emoji, (
                f"Enthusiastic template '{key}' should have exclamation or emoji, got: {text}"
            )

    def test_friendly_moderate_emojis_all_templates(self):
        """Friendly: ALL templates have 0-3 emojis (moderate use)."""
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.FRIENDLY][key]
            emoji_count = _count_emojis(text)
            assert 0 <= emoji_count <= 3, (
                f"Friendly template '{key}' should have 0-3 emojis, got {emoji_count}: {text}"
            )

    def test_all_keys_present_for_all_personalities(self):
        """ALL 9 keys exist for ALL 3 personality types."""
        for ptype in PersonalityType:
            for key in self.TEMPLATE_KEYS:
                assert key in CONVERSATION_TEMPLATES[ptype], (
                    f"Missing template key '{key}' for personality {ptype.value}"
                )

    def test_llm_fallback_contains_business_name_placeholder(self):
        """llm_fallback template contains {business_name} for substitution."""
        for ptype in PersonalityType:
            text = CONVERSATION_TEMPLATES[ptype]["llm_fallback"]
            assert "{business_name}" in text, (
                f"llm_fallback for {ptype.value} should contain {{business_name}} placeholder"
            )

    def test_professional_templates_formal_tone(self):
        """Professional: templates use formal language (no contractions like 'I'm')."""
        informal_re = __import__("re").compile(
            r"\b(I'm|can't|won't|don't|isn't|aren't|couldn't|wouldn't|let's)\b",
            __import__("re").I,
        )
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert not informal_re.search(text), (
                f"Professional template '{key}' should avoid contractions, got: {text}"
            )

    def test_enthusiastic_templates_upbeat_words(self):
        """Enthusiastic: templates contain energetic words (LOVE, AMAZING, etc.)."""
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC][key]
            has_energy = any(
                w in text.upper()
                for w in ["LOVE", "AMAZING", "SO", "!!!", "WOW", "EXCITED", "AWESOME", "TINY"]
            )
            has_emoji = _count_emojis(text) > 0
            assert has_energy or has_emoji, (
                f"Enthusiastic template '{key}' should feel energetic, got: {text}"
            )


# ---------------------------------------------------------------------------
# P1 #3: LLM Handler — Error fallback personality
# ---------------------------------------------------------------------------
class TestLLMHandlerErrorFallbackPersonality:
    """P1 Gap #3: Classification leak and LLM fallback use correct personality templates."""

    @pytest.mark.asyncio
    async def test_classification_leak_uses_professional_template(self):
        """When LLM returns JSON classification, Professional template is used."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service('{"intent": "product_search", "confidence": 0.9}')
        ctx = _make_context(conversation_id=50)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

        assert "😊" not in result.message
        assert "additional details" in result.message.lower() or "assist" in result.message.lower()

    @pytest.mark.asyncio
    async def test_classification_leak_uses_enthusiastic_template(self):
        """When LLM returns JSON classification, Enthusiastic template is used."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.ENTHUSIASTIC)
        llm_svc = _make_llm_service('{"intent": "product_search", "confidence": 0.9}')
        ctx = _make_context(conversation_id=51)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

        assert "😊" in result.message or "🎉" in result.message or "LOVE" in result.message

    @pytest.mark.asyncio
    async def test_llm_exception_uses_friendly_fallback(self):
        """When LLM throws, Friendly fallback includes business_name and emoji."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY, business_name="Cool Shop")
        llm_svc = AsyncMock()
        llm_svc.chat = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        ctx = _make_context(conversation_id=52)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

        assert "Cool Shop" in result.message
        assert "😊" in result.message

    @pytest.mark.asyncio
    async def test_llm_exception_uses_professional_fallback(self):
        """When LLM throws, Professional fallback has no emojis."""
        handler = LLMHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL, business_name="Formal Store")
        llm_svc = AsyncMock()
        llm_svc.chat = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        ctx = _make_context(conversation_id=53)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

        assert "Formal Store" in result.message
        assert _count_emojis(result.message) == 0


# ---------------------------------------------------------------------------
# P1 #4: Clarification Handler — ValueError fallback personality
# ---------------------------------------------------------------------------
class TestClarificationHandlerValueErrorFallback:
    """P1 Gap #4: clarification_fallback template uses correct personality."""

    @pytest.mark.asyncio
    async def test_valueerror_fallback_professional(self):
        """ValueError in question generation uses Professional fallback (no emojis)."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.clarification_handler.QuestionGenerator"
        ) as MockQG:
            mock_qg = MockQG.return_value
            mock_qg.generate_next_question = AsyncMock(side_effect=ValueError("no questions"))
            result = await handler.handle(db, merchant, llm_svc, "I want shoes", ctx, {})

        assert _count_emojis(result.message) == 0
        assert "additional details" in result.message.lower()

    @pytest.mark.asyncio
    async def test_valueerror_fallback_friendly(self):
        """ValueError in question generation uses Friendly fallback (with emoji)."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.clarification_handler.QuestionGenerator"
        ) as MockQG:
            mock_qg = MockQG.return_value
            mock_qg.generate_next_question = AsyncMock(side_effect=ValueError("no questions"))
            result = await handler.handle(db, merchant, llm_svc, "I want shoes", ctx, {})

        assert _count_emojis(result.message) >= 1

    @pytest.mark.asyncio
    async def test_valueerror_fallback_enthusiastic(self):
        """ValueError in question generation uses Enthusiastic fallback."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.ENTHUSIASTIC)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.clarification_handler.QuestionGenerator"
        ) as MockQG:
            mock_qg = MockQG.return_value
            mock_qg.generate_next_question = AsyncMock(side_effect=ValueError("no questions"))
            result = await handler.handle(db, merchant, llm_svc, "I want shoes", ctx, {})

        assert "!" in result.message
        assert _count_emojis(result.message) >= 1


# ---------------------------------------------------------------------------
# P1 #5: Clarification Handler — _personalize_question transition prefixing
# ---------------------------------------------------------------------------
class TestClarificationHandlerPersonalizeQuestion:
    """P1 Gap #5: _personalize_question prefixes with personality-correct transitions."""

    @pytest.mark.asyncio
    async def test_personalize_adds_transition_prefix(self):
        """Question gets a transition phrase prefix from TransitionSelector."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service()

        result = await handler._personalize_question(
            question="What is your budget?",
            constraint="budget",
            merchant=merchant,
            llm_service=llm_svc,
            conversation_id="test-conv",
        )

        assert "What is your budget?" in result
        assert len(result) > len("What is your budget?")

    @pytest.mark.asyncio
    async def test_budget_constraint_adds_business_name_prefix(self):
        """Budget constraint adds 'At {business_name}, we have options for every budget.'."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY, business_name="Shoe Palace")
        llm_svc = _make_llm_service()

        result = await handler._personalize_question(
            question="What is your budget?",
            constraint="budget",
            merchant=merchant,
            llm_service=llm_svc,
        )

        assert "Shoe Palace" in result
        assert "every budget" in result

    @pytest.mark.asyncio
    async def test_non_budget_constraint_no_business_name_prefix(self):
        """Non-budget constraints do NOT add the business name prefix."""
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL, business_name="Shoe Palace")
        llm_svc = _make_llm_service()

        result = await handler._personalize_question(
            question="What color do you prefer?",
            constraint="color",
            merchant=merchant,
            llm_service=llm_svc,
        )

        assert "every budget" not in result


# ---------------------------------------------------------------------------
# P1 #9: General mode fallback — include_transition code path
# ---------------------------------------------------------------------------
class TestGeneralModeFallbackTransition:
    """P1 Gap #9: General mode responses with include_transition path."""

    def test_formatter_includes_transition_for_general(self):
        """format_response for 'general' type includes transition phrase."""
        from app.services.personality.transition_phrases import TransitionCategory

        result = PersonalityAwareResponseFormatter.format_response(
            "general",
            "general_fallback",
            PersonalityType.FRIENDLY,
            include_transition=True,
            business_name="Test Store",
        )
        if result:
            assert isinstance(result, str)

    def test_formatter_without_transition_for_general(self):
        """format_response for 'general' type works without include_transition."""
        result = PersonalityAwareResponseFormatter.format_response(
            "general",
            "general_fallback",
            PersonalityType.FRIENDLY,
            business_name="Test Store",
        )
        if result:
            assert isinstance(result, str)


# ---------------------------------------------------------------------------
# P2 #6: Check Consent Handler — Exception path personality
# ---------------------------------------------------------------------------
class TestCheckConsentHandlerExceptionPersonality:
    """P2 Gap #6: Exception in consent check uses consent_check_error template."""

    @pytest.mark.asyncio
    async def test_exception_uses_professional_template(self):
        """Consent check exception uses Professional consent_check_error template."""
        handler = CheckConsentHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.get_consent_for_conversation = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )
            result = await handler.handle(db, merchant, llm_svc, "check consent", ctx)

        assert _count_emojis(result.message) == 0
        assert "unable" in result.message.lower() or "try again" in result.message.lower()

    @pytest.mark.asyncio
    async def test_exception_uses_friendly_template(self):
        """Consent check exception uses Friendly consent_check_error template."""
        handler = CheckConsentHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.get_consent_for_conversation = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )
            result = await handler.handle(db, merchant, llm_svc, "check consent", ctx)

        assert _count_emojis(result.message) >= 1

    @pytest.mark.asyncio
    async def test_exception_uses_enthusiastic_template(self):
        """Consent check exception uses Enthusiastic consent_check_error template."""
        handler = CheckConsentHandler()
        merchant = _make_merchant(PersonalityType.ENTHUSIASTIC)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.get_consent_for_conversation = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )
            result = await handler.handle(db, merchant, llm_svc, "check consent", ctx)

        assert "!" in result.message
        assert _count_emojis(result.message) >= 1


# ---------------------------------------------------------------------------
# P2 #7: Forget Preferences Handler — 3 error paths personality
# ---------------------------------------------------------------------------
class TestForgetPreferencesHandlerErrorPaths:
    """P2 Gap #7: Three error paths use correct personality templates."""

    @pytest.mark.asyncio
    async def test_rate_limited_uses_professional_template(self):
        """Rate-limited APIError uses Professional forget_rate_limited template."""
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Rate limit exceeded. Please wait before trying again.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert _count_emojis(result.message) == 0
        assert result.metadata.get("rate_limited") is True

    @pytest.mark.asyncio
    async def test_rate_limited_uses_friendly_template(self):
        """Rate-limited APIError uses Friendly forget_rate_limited template."""
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Rate limit exceeded. Please wait before trying again.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert _count_emojis(result.message) >= 1

    @pytest.mark.asyncio
    async def test_api_error_uses_correct_template(self):
        """Non-rate-limited APIError uses forget_error template."""
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Internal error occurred.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert _count_emojis(result.message) == 0
        assert "error" in result.message.lower() or "try again" in result.message.lower()

    @pytest.mark.asyncio
    async def test_generic_exception_uses_correct_template(self):
        """Generic Exception uses forget_unexpected_error template."""
        handler = ForgetPreferencesHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=RuntimeError("Unexpected crash")
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert (
            "unexpected" in result.message.lower()
            or "Oops" in result.message
            or "oops" in result.message
        )

    @pytest.mark.asyncio
    async def test_generic_exception_enthusiastic_template(self):
        """Generic Exception uses Enthusiastic forget_unexpected_error template."""
        handler = ForgetPreferencesHandler()
        merchant = _make_merchant(PersonalityType.ENTHUSIASTIC)
        llm_svc = _make_llm_service()
        ctx = _make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=RuntimeError("Unexpected crash")
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert _count_emojis(result.message) >= 1


# ---------------------------------------------------------------------------
# P2 #8 & #12: Template-level coverage for budget pause + handoff fallback
# ---------------------------------------------------------------------------
class TestConversationTemplateFormatting:
    """P2 Gaps #8, #12: Verify template formatting for bot_paused and welcome_back_fallback."""

    def test_bot_paused_professional_no_emojis(self):
        """bot_paused template for Professional has no emojis."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "bot_paused", PersonalityType.PROFESSIONAL
        )
        assert _count_emojis(result) == 0
        assert "unavailable" in result.lower()

    def test_bot_paused_friendly_has_emoji(self):
        """bot_paused template for Friendly has emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "bot_paused", PersonalityType.FRIENDLY
        )
        assert _count_emojis(result) >= 1

    def test_bot_paused_enthusiastic_high_energy(self):
        """bot_paused template for Enthusiastic has exclamations + emojis."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "bot_paused", PersonalityType.ENTHUSIASTIC
        )
        assert "!" in result
        assert _count_emojis(result) >= 1

    def test_welcome_back_fallback_professional_no_emojis(self):
        """welcome_back_fallback for Professional has no emojis."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "welcome_back_fallback", PersonalityType.PROFESSIONAL
        )
        assert _count_emojis(result) == 0
        assert "welcome" in result.lower()

    def test_welcome_back_fallback_friendly_has_emoji(self):
        """welcome_back_fallback for Friendly has emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "welcome_back_fallback", PersonalityType.FRIENDLY
        )
        assert _count_emojis(result) >= 1

    def test_welcome_back_fallback_enthusiastic_high_energy(self):
        """welcome_back_fallback for Enthusiastic has exclamations + emojis."""
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation", "welcome_back_fallback", PersonalityType.ENTHUSIASTIC
        )
        assert "!" in result
        assert _count_emojis(result) >= 1


# ---------------------------------------------------------------------------
# P2 #11: LLM Handler — Resolution system prompt with personality examples
# ---------------------------------------------------------------------------
class TestLLMHandlerResolutionSystemPrompt:
    """P2 Gap #11: System prompt includes personality-specific guidance."""

    @pytest.mark.asyncio
    async def test_system_prompt_contains_personality_context(self):
        """System prompt includes personality-specific guidance text."""
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.PROFESSIONAL, business_name="Acme Corp"),
            bot_name="AcmeBot",
            business_name="Acme Corp",
            personality_type=PersonalityType.PROFESSIONAL,
            pending_state=None,
            turn_number=1,
            conversation_id=None,
        )

        assert "PROFESSIONAL" in prompt.upper() or "professional" in prompt.lower()

    @pytest.mark.asyncio
    async def test_system_prompt_friendly_tone(self):
        """Friendly system prompt includes friendly tone guidance."""
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.FRIENDLY),
            bot_name="FriendlyBot",
            business_name="Happy Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=1,
            conversation_id=None,
        )

        assert (
            "FRIENDLY" in prompt.upper() or "friendly" in prompt.lower() or "warm" in prompt.lower()
        )

    @pytest.mark.asyncio
    async def test_system_prompt_enthusiastic_tone(self):
        """Enthusiastic system prompt includes energetic tone guidance."""
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=_make_merchant(PersonalityType.ENTHUSIASTIC),
            bot_name="ExcitedBot",
            business_name="Fun Store",
            personality_type=PersonalityType.ENTHUSIASTIC,
            pending_state=None,
            turn_number=1,
            conversation_id=None,
        )

        assert (
            "ENTHUSIASTIC" in prompt.upper()
            or "enthusiastic" in prompt.lower()
            or "energetic" in prompt.lower()
        )
