"""Unit tests for sentiment analyzer."""

import pytest
from app.services.analytics.sentiment_analyzer import (
    analyze_sentiment,
    get_sentiment_score,
    Sentiment,
    SentimentScore,
)


class TestSentimentAnalyzer:
    """Tests for the enhanced sentiment analyzer."""

    def test_basic_positive(self):
        assert analyze_sentiment("This is great, thank you!") == "positive"
        assert analyze_sentiment("Love it! Works perfectly.") == "positive"
        assert analyze_sentiment("Amazing product, fast shipping!") == "positive"

    def test_basic_negative(self):
        assert analyze_sentiment("This is terrible, I hate it.") == "negative"
        assert analyze_sentiment("Not working, very disappointed.") == "negative"
        assert analyze_sentiment("Wrong item arrived, want a refund.") == "negative"

    def test_negation_handling(self):
        result = get_sentiment_score("not good at all.")
        assert result.sentiment == Sentiment.NEGATIVE

        result = get_sentiment_score("would not recommend.")
        assert result.sentiment == Sentiment.NEGATIVE

    def test_ecommerce_positive(self):
        assert analyze_sentiment("Fast delivery, great quality!") == "positive"
        assert analyze_sentiment("Fits perfectly, true to size!") == "positive"
        assert analyze_sentiment("Great price, worth it!") == "positive"
        assert analyze_sentiment("Arrived early, excellent!") == "positive"

    def test_ecommerce_negative(self):
        assert analyze_sentiment("Late delivery, poor packaging.") == "negative"
        assert analyze_sentiment("Damaged on arrival, want refund.") == "negative"
        assert analyze_sentiment("Not as described, misleading.") == "negative"
        assert analyze_sentiment("Too small, doesn't fit.") == "negative"

    def test_neutral(self):
        assert analyze_sentiment("What are your hours?") == "neutral"
        assert analyze_sentiment("Can you help me with this?") == "neutral"
        assert analyze_sentiment("Hello") == "neutral"

    def test_mixed_sentiment(self):
        result = get_sentiment_score("Great product but shipping was slow")
        assert result.sentiment in [Sentiment.POSITIVE, Sentiment.NEUTRAL]

    def test_confidence_score(self):
        result = get_sentiment_score("This is absolutely amazing and wonderful!")
        assert result.confidence >= 0.0
        result = get_sentiment_score("Hello")
        assert result.confidence >= 0.0

        result = get_sentiment_score("")
        assert result.sentiment == Sentiment.NEUTRAL
        assert result.confidence == 1.0

    def test_empty_content(self):
        result = get_sentiment_score("")
        assert result.sentiment == Sentiment.NEUTRAL
        assert result.confidence == 1.0

    def test_emoji_sentiment(self):
        assert analyze_sentiment("Thanks! 👍") == "positive"
        assert analyze_sentiment("Love it! ❤️") == "positive"
        assert analyze_sentiment("Not happy 😞") == "negative"
        assert analyze_sentiment("Terrible 👎") == "negative"

    def test_question_detection(self):
        result_question = get_sentiment_score("Can you tell me about your return policy?")
        result_statement = get_sentiment_score("Your return policy is great!")

        # Questions get dampened weight
        assert result_question.confidence <= result_statement.confidence

    def test_question_dampened_weight(self):
        result = get_sentiment_score("Can you help me with this?")
        result_greeting = get_sentiment_score("Hello there!")

        # Questions should have reduced weight
        assert result.confidence <= result_greeting.confidence
