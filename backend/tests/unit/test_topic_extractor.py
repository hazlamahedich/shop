"""Unit tests for TopicExtractor service.

Story 10-8: Top Topics Widget

Tests topic extraction, trend calculation, and stop word filtering.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.analytics.topic_extractor import (
    TopicExtractor,
    calculate_trend,
    is_valid_topic,
    STOP_WORDS,
)


class TestCalculateTrend:
    """Tests for calculate_trend function."""

    def test_new_topic_when_previous_is_none(self):
        assert calculate_trend(10, None) == "new"

    def test_new_topic_when_previous_is_zero(self):
        assert calculate_trend(10, 0) == "new"

    def test_up_trend_when_increase_over_10_percent(self):
        assert calculate_trend(112, 100) == "up"
        assert calculate_trend(15, 10) == "up"
        assert calculate_trend(1000, 500) == "up"

    def test_down_trend_when_decrease_over_10_percent(self):
        assert calculate_trend(89, 100) == "down"
        assert calculate_trend(5, 10) == "down"
        assert calculate_trend(100, 500) == "down"

    def test_stable_trend_when_change_within_10_percent(self):
        assert calculate_trend(105, 100) == "stable"
        assert calculate_trend(95, 100) == "stable"
        assert calculate_trend(108, 100) == "stable"
        assert calculate_trend(92, 100) == "stable"

    def test_stable_trend_when_counts_are_equal(self):
        assert calculate_trend(100, 100) == "stable"

    def test_edge_case_very_small_previous(self):
        assert calculate_trend(2, 1) == "up"
        assert calculate_trend(1, 2) == "down"


class TestIsValidTopic:
    """Tests for is_valid_topic function."""

    def test_valid_topic_with_meaningful_words(self):
        assert is_valid_topic("shipping cost") is True
        assert is_valid_topic("return policy") is True
        assert is_valid_topic("how do I track my order") is True

    def test_invalid_topic_only_stop_words(self):
        assert is_valid_topic("the a an") is False
        assert is_valid_topic("is it") is False
        assert is_valid_topic("I want to") is False

    def test_invalid_topic_empty_string(self):
        assert is_valid_topic("") is False
        assert is_valid_topic("   ") is False

    def test_invalid_topic_single_stop_word(self):
        assert is_valid_topic("the") is False
        assert is_valid_topic("a") is False
        assert is_valid_topic("is") is False

    def test_valid_topic_mixed_stop_and_meaningful(self):
        assert is_valid_topic("what is shipping") is True
        assert is_valid_topic("how to return") is True

    def test_invalid_topic_single_character_words(self):
        assert is_valid_topic("a b c") is False

    def test_valid_topic_case_insensitive(self):
        assert is_valid_topic("SHIPPING COST") is True
        assert is_valid_topic("Return Policy") is True


class TestStopWords:
    """Tests for STOP_WORDS constant."""

    def test_common_stop_words_included(self):
        assert "the" in STOP_WORDS
        assert "a" in STOP_WORDS
        assert "is" in STOP_WORDS
        assert "to" in STOP_WORDS
        assert "and" in STOP_WORDS

    def test_greeting_words_included(self):
        assert "hi" in STOP_WORDS
        assert "hello" in STOP_WORDS
        assert "hey" in STOP_WORDS
        assert "thanks" in STOP_WORDS

    def test_meaningful_words_not_in_stop_words(self):
        assert "shipping" not in STOP_WORDS
        assert "return" not in STOP_WORDS
        assert "order" not in STOP_WORDS
        assert "price" not in STOP_WORDS


class TestTopicExtractor:
    """Tests for TopicExtractor class."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def extractor(self, mock_db):
        return TopicExtractor(mock_db)

    def test_init(self, mock_db):
        extractor = TopicExtractor(mock_db)
        assert extractor.db == mock_db

    @pytest.mark.asyncio
    async def test_extract_topics_returns_list(self, extractor, mock_db):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await extractor.extract_topics(merchant_id=1, days=7, limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_topics_filters_invalid_queries(self, extractor, mock_db):
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(query="shipping cost", query_count=10),
            MagicMock(query="the a an", query_count=5),
        ]
        mock_db.execute.return_value = mock_result

        result = await extractor.extract_topics(merchant_id=1, days=7, limit=10)

        assert len(result) == 1
        assert result[0]["name"] == "shipping cost"

    @pytest.mark.asyncio
    async def test_extract_topics_respects_limit(self, extractor, mock_db):
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(query=f"topic {i}", query_count=10 - i) for i in range(20)
        ]
        mock_db.execute.return_value = mock_result

        result = await extractor.extract_topics(merchant_id=1, days=7, limit=5)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_topic_counts_returns_dict(self, extractor, mock_db):
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(query="shipping", query_count=10),
            MagicMock(query="returns", query_count=5),
        ]
        mock_db.execute.return_value = mock_result

        result = await extractor.get_topic_counts(merchant_id=1, days=7)

        assert isinstance(result, dict)
        assert result["shipping"] == 10
        assert result["returns"] == 5
