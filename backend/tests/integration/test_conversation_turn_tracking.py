"""Integration tests for Story 11-12a: Conversation Turn Tracking Pipeline.

Verifies service + DB interaction for conversation turn recording,
including unique constraint enforcement, sentiment capture,
multi-turn sequence incrementing, and the full tracking pipeline.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.conversation_context import ConversationTurn
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdaptation,
    SentimentStrategy,
)
from app.services.analytics.sentiment_analyzer import Sentiment, SentimentScore
from app.services.conversation.unified_conversation_service import UnifiedConversationService


@pytest.fixture(autouse=True)
def _reset_turn_write_metrics():
    saved = dict(UnifiedConversationService._turn_write_metrics)
    yield
    UnifiedConversationService._turn_write_metrics.update(saved)


def _make_context(
    merchant_id: int,
    conversation_history: list | None = None,
    metadata: dict | None = None,
) -> ConversationContext:
    return ConversationContext(
        session_id="sess_turn_test",
        merchant_id=merchant_id,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(),
        metadata=metadata or {},
        conversation_history=conversation_history or [],
    )


class TestConversationTurnTracking:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-001")
    @pytest.mark.asyncio
    async def test_turn_record_created_on_message_processing(
        self, db_session, test_merchant, test_conversation
    ):
        given_merchant_id = test_merchant
        given_conversation_id = test_conversation.id
        given_context = _make_context(given_merchant_id)

        service = UnifiedConversationService(db=db_session)
        given_snapshot = service._build_turn_context_snapshot(
            confidence=0.92,
            processing_time_ms=150.0,
            context=given_context,
            mode="ecommerce",
        )

        when_turn_number = 1
        async with db_session.begin_nested():
            await service._write_conversation_turn(
                db=db_session,
                conversation_id=given_conversation_id,
                turn_number=when_turn_number,
                intent_detected="product_search",
                sentiment="EMPATHETIC",
                context_snapshot=given_snapshot,
            )

        result = await db_session.execute(
            text(
                "SELECT turn_number, intent_detected, context_snapshot, sentiment "
                "FROM conversation_turns "
                "WHERE conversation_id = :cid AND turn_number = :tn"
            ),
            {"cid": given_conversation_id, "tn": when_turn_number},
        )
        row = result.fetchone()

        assert row is not None
        assert row[0] == 1
        assert row[1] == "product_search"
        assert row[2]["confidence"] == 0.92
        assert row[2]["processing_time_ms"] == 150
        assert row[3] == "EMPATHETIC"

        await db_session.rollback()

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-002")
    @pytest.mark.asyncio
    async def test_unique_constraint_enforced_at_db_level(
        self, db_session, test_merchant, test_conversation
    ):
        given_conversation_id = test_conversation.id
        given_turn_number = 1

        turn_a = ConversationTurn(
            conversation_id=given_conversation_id,
            turn_number=given_turn_number,
            intent_detected="greeting",
            context_snapshot={"confidence": 0.9},
        )
        db_session.add(turn_a)
        await db_session.flush()

        turn_b = ConversationTurn(
            conversation_id=given_conversation_id,
            turn_number=given_turn_number,
            intent_detected="product_search",
            context_snapshot={"confidence": 0.8},
        )
        db_session.add(turn_b)

        with pytest.raises(IntegrityError):
            await db_session.flush()

        await db_session.rollback()

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-003")
    @pytest.mark.asyncio
    async def test_sentiment_data_captured_in_turn_record(
        self, db_session, test_merchant, test_conversation
    ):
        given_merchant_id = test_merchant
        given_conversation_id = test_conversation.id
        given_context = _make_context(given_merchant_id)

        service = UnifiedConversationService(db=db_session)
        when_snapshot = service._build_turn_context_snapshot(
            confidence=0.85,
            processing_time_ms=200.0,
            context=given_context,
            sentiment_confidence=0.78,
            mode="general",
        )

        async with db_session.begin_nested():
            await service._write_conversation_turn(
                db=db_session,
                conversation_id=given_conversation_id,
                turn_number=1,
                intent_detected="general",
                sentiment="EMPATHETIC",
                context_snapshot=when_snapshot,
            )

        result = await db_session.execute(
            text(
                "SELECT context_snapshot, sentiment FROM conversation_turns "
                "WHERE conversation_id = :cid"
            ),
            {"cid": given_conversation_id},
        )
        row = result.fetchone()

        assert row is not None
        assert row[0]["sentiment_score"] == 0.78
        assert row[0]["mode"] == "general"
        assert row[1] == "EMPATHETIC"

        await db_session.rollback()

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-004")
    @pytest.mark.asyncio
    async def test_multi_turn_sequence_incrementing_turn_number(
        self, db_session, test_merchant, test_conversation
    ):
        given_merchant_id = test_merchant
        given_conversation_id = test_conversation.id

        intents = ["greeting", "product_search", "cart_add"]
        history: list[dict] = []

        for idx, intent in enumerate(intents, start=1):
            ctx = _make_context(given_merchant_id, conversation_history=history.copy())
            service = UnifiedConversationService(db=db_session)
            snapshot = service._build_turn_context_snapshot(
                confidence=0.8 + idx * 0.05,
                processing_time_ms=100.0 * idx,
                context=ctx,
                mode="ecommerce",
            )
            async with db_session.begin_nested():
                await service._write_conversation_turn(
                    db=db_session,
                    conversation_id=given_conversation_id,
                    turn_number=idx,
                    intent_detected=intent,
                    sentiment=None,
                    context_snapshot=snapshot,
                )
            history.append({"role": "user", "content": f"turn {idx}"})

        result = await db_session.execute(
            text(
                "SELECT turn_number, intent_detected FROM conversation_turns "
                "WHERE conversation_id = :cid ORDER BY turn_number"
            ),
            {"cid": given_conversation_id},
        )
        rows = result.fetchall()

        assert len(rows) == 3
        assert rows[0][0] == 1
        assert rows[0][1] == "greeting"
        assert rows[1][0] == 2
        assert rows[1][1] == "product_search"
        assert rows[2][0] == 3
        assert rows[2][1] == "cart_add"

        await db_session.rollback()


class TestConversationTurnTrackingEndToEnd:
    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-023")
    @pytest.mark.asyncio
    async def test_track_conversation_turn_writes_to_db(
        self, db_session, test_merchant, test_conversation
    ):
        given_merchant_id = test_merchant
        given_conversation_id = test_conversation.id
        given_context = _make_context(given_merchant_id)

        service = UnifiedConversationService(db=db_session)

        await service._track_conversation_turn(
            db=db_session,
            conversation_id=given_conversation_id,
            context=given_context,
            confidence=0.91,
            processing_time_ms=180.0,
            intent_name="product_search",
            mode="ecommerce",
        )

        result = await db_session.execute(
            text(
                "SELECT turn_number, intent_detected, context_snapshot, sentiment "
                "FROM conversation_turns "
                "WHERE conversation_id = :cid"
            ),
            {"cid": given_conversation_id},
        )
        row = result.fetchone()

        assert row is not None
        assert row[0] == 1
        assert row[1] == "product_search"
        assert row[2]["confidence"] == 0.91
        assert row[2]["processing_time_ms"] == 180
        assert row[2]["mode"] == "ecommerce"
        assert row[3] is None

        await db_session.rollback()

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-024")
    @pytest.mark.asyncio
    async def test_track_conversation_turn_with_sentiment_obj(
        self, db_session, test_merchant, test_conversation
    ):
        given_merchant_id = test_merchant
        given_conversation_id = test_conversation.id
        sentiment_obj = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=SentimentScore(
                sentiment=Sentiment.NEGATIVE,
                positive_score=0.1,
                negative_score=0.8,
                confidence=0.75,
                matched_terms=["frustrated"],
            ),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
            mode="ecommerce",
        )
        given_context = _make_context(
            given_merchant_id,
            metadata={"_sentiment_adaptation_obj": sentiment_obj},
        )

        service = UnifiedConversationService(db=db_session)

        await service._track_conversation_turn(
            db=db_session,
            conversation_id=given_conversation_id,
            context=given_context,
            confidence=0.85,
            processing_time_ms=220.0,
            intent_name="general",
            mode="ecommerce",
        )

        result = await db_session.execute(
            text(
                "SELECT context_snapshot, sentiment FROM conversation_turns "
                "WHERE conversation_id = :cid"
            ),
            {"cid": given_conversation_id},
        )
        row = result.fetchone()

        assert row is not None
        assert row[0]["sentiment_score"] == 0.75
        assert row[0]["mode"] == "ecommerce"
        assert row[1] == "empathetic"

        await db_session.rollback()

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-025")
    @pytest.mark.asyncio
    async def test_track_conversation_turn_with_none_conversation_id_does_nothing(
        self, db_session, test_merchant, test_conversation
    ):
        given_context = _make_context(test_merchant)

        service = UnifiedConversationService(db=db_session)

        await service._track_conversation_turn(
            db=db_session,
            conversation_id=None,
            context=given_context,
            confidence=0.9,
            processing_time_ms=100.0,
            intent_name="greeting",
            mode="ecommerce",
        )

        result = await db_session.execute(text("SELECT COUNT(*) FROM conversation_turns"))
        count = result.scalar()

        assert count == 0
