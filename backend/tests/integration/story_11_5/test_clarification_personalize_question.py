from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.clarification_handler import ClarificationHandler

from .fixtures import make_llm_service, make_merchant


class TestClarificationHandlerPersonalizeQuestion:
    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-022")
    async def test_personalize_adds_transition_prefix(self):
        handler = ClarificationHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY)
        llm_svc = make_llm_service()

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
    @pytest.mark.test_id("11-5-INT-023")
    async def test_budget_constraint_adds_business_name_prefix(self):
        handler = ClarificationHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY, business_name="Shoe Palace")
        llm_svc = make_llm_service()

        result = await handler._personalize_question(
            question="What is your budget?",
            constraint="budget",
            merchant=merchant,
            llm_service=llm_svc,
        )

        assert "Shoe Palace" in result
        assert "every budget" in result

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-024")
    async def test_non_budget_constraint_no_business_name_prefix(self):
        handler = ClarificationHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL, business_name="Shoe Palace")
        llm_svc = make_llm_service()

        result = await handler._personalize_question(
            question="What color do you prefer?",
            constraint="color",
            merchant=merchant,
            llm_service=llm_svc,
        )

        assert "every budget" not in result
