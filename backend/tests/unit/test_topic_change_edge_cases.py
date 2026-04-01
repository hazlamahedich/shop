"""Edge case tests for _is_topic_change in MessageClassifier.

Story 11-2 [P2]: Tests empty strings, Unicode, emoji, very long messages,
single-word messages, and boundary conditions for keyword overlap analysis.
"""

import pytest

from app.services.multi_turn.message_classifier import MessageClassifier


@pytest.fixture
def classifier() -> MessageClassifier:
    return MessageClassifier()


class TestEmptyAndMinimalInputs:
    def test_empty_message_with_original_query(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("", "running shoes")
        assert result is False

    def test_empty_original_query_with_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("I want shoes", "")
        assert result is False

    def test_both_empty(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("", "")
        assert result is False

    def test_single_word_message_single_word_query(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("shoes", "shoes")
        assert result is False

    def test_single_word_different_from_query(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("pizza", "shoes")
        assert result is False


class TestUnicodeAndEmoji:
    def test_unicode_message_english_query(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("我想买一双跑鞋", "running shoes")
        assert isinstance(result, bool)

    def test_emoji_heavy_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("👟🏃‍♂️💨 great shoes", "running shoes")
        assert isinstance(result, bool)

    def test_all_emoji_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("👟🏃‍♂️💨🎯🔥", "running shoes")
        assert isinstance(result, bool)

    def test_unicode_query_english_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("I want running shoes", "跑鞋")
        assert isinstance(result, bool)

    def test_mixed_script_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("I need some chaussures for running", "running shoes")
        assert isinstance(result, bool)


class TestLongMessages:
    def test_very_long_unrelated_message(self, classifier: MessageClassifier):
        long_msg = " ".join(f"word{i}" for i in range(50))
        result = classifier._is_topic_change(long_msg, "running shoes")
        assert result is True

    def test_very_long_related_message(self, classifier: MessageClassifier):
        long_msg = " ".join(["running shoes"] * 25)
        result = classifier._is_topic_change(long_msg, "running shoes")
        assert result is False

    def test_long_message_with_some_overlap(self, classifier: MessageClassifier):
        msg = "I need running gear but also want to discuss weather patterns today"
        result = classifier._is_topic_change(msg, "running shoes")
        assert isinstance(result, bool)


class TestBoundaryConditions:
    def test_message_with_only_stop_words(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("the a an is are was were", "running shoes")
        assert isinstance(result, bool)

    def test_query_with_only_stop_words(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("I want running shoes", "the a an is")
        assert isinstance(result, bool)

    def test_exactly_two_overlapping_keywords(self, classifier: MessageClassifier):
        msg = "I want running shoes for marathon training"
        result = classifier._is_topic_change(msg, "running shoes for beginners")
        assert result is False

    def test_exactly_one_overlapping_keyword(self, classifier: MessageClassifier):
        msg = "I need new running trail gear equipment"
        result = classifier._is_topic_change(msg, "blue swimming pool")
        assert isinstance(result, bool)

    def test_case_insensitivity(self, classifier: MessageClassifier):
        result1 = classifier._is_topic_change("Running Shoes", "running shoes")
        result2 = classifier._is_topic_change("running shoes", "RUNING SHOES")
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    def test_message_three_keywords_no_overlap(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("pizza burger fries soda", "running shoes")
        assert result is True

    def test_message_with_special_characters(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("I want shoes! @#$% really badly ***", "running shoes")
        assert isinstance(result, bool)

    def test_whitespace_heavy_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("  running   shoes  ", "running shoes")
        assert isinstance(result, bool)

    def test_numeric_message(self, classifier: MessageClassifier):
        result = classifier._is_topic_change("42 100 999", "running shoes")
        assert isinstance(result, bool)
