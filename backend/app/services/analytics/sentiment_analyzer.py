"""
Enhanced sentiment analyzer with better text matching.

Supports:
- Negation handling (not good, wasn't helpful)
- Intensifiers (very good, really bad)
- Multi-word phrases (not working, great service)
- Ecommerce-specific terms (shipping, refund, quality)
- Emoji sentiment detection
- Weighted scoring system
"""

import re
from dataclasses import dataclass
from enum import Enum


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentScore:
    sentiment: Sentiment
    positive_score: float
    negative_score: float
    confidence: float
    matched_terms: list[str]


# Positive patterns with weights
POSITIVE_PATTERNS = {
    # Strong positive (weight: 2.0)
    "love it": 2.0,
    "love this": 2.0,
    "amazing": 2.0,
    "excellent": 2.0,
    "fantastic": 2.0,
    "outstanding": 2.0,
    "perfect": 2.0,
    "brilliant": 2.0,
    "superb": 2.0,
    "incredible": 2.0,
    "wonderful": 2.0,
    "exceptional": 2.0,
    "flawless": 2.0,
    "impeccable": 2.0,
    # Moderate positive (weight: 1.5)
    "great": 1.5,
    "awesome": 1.5,
    "very helpful": 1.5,
    "really helpful": 1.5,
    "so helpful": 1.5,
    "super helpful": 1.5,
    "very good": 1.5,
    "really good": 1.5,
    "works great": 1.5,
    "works perfectly": 1.5,
    "highly recommend": 1.5,
    "definitely recommend": 1.5,
    "would recommend": 1.5,
    "very satisfied": 1.5,
    "really satisfied": 1.5,
    "exactly what": 1.5,
    "just what": 1.5,
    "solved my": 1.5,
    "fixed my": 1.5,
    "resolved my": 1.5,
    "thank you so much": 1.5,
    "thanks so much": 1.5,
    "appreciate it": 1.5,
    "really appreciate": 1.5,
    # Standard positive (weight: 1.0)
    "good": 1.0,
    "nice": 1.0,
    "helpful": 1.0,
    "thank": 1.0,
    "thanks": 1.0,
    "happy": 1.0,
    "satisfied": 1.0,
    "pleased": 1.0,
    "recommend": 1.0,
    "easy": 1.0,
    "fast": 1.0,
    "quick": 1.0,
    "efficient": 1.0,
    "smooth": 1.0,
    "reliable": 1.0,
    "resolved": 1.0,
    "fixed": 1.0,
    "worked": 1.0,
    "best": 1.0,
    "solid": 1.0,
    "impressed": 1.0,
    "delighted": 1.0,
    "thrilled": 1.0,
    # Ecommerce positive
    "fast shipping": 1.8,
    "quick delivery": 1.8,
    "fast delivery": 1.8,
    "arrived early": 1.8,
    "on time": 1.3,
    "as described": 1.5,
    "as pictured": 1.5,
    "great quality": 1.8,
    "good quality": 1.5,
    "high quality": 1.8,
    "excellent quality": 2.0,
    "great price": 1.5,
    "good value": 1.5,
    "worth it": 1.5,
    "fits perfectly": 1.8,
    "fits great": 1.5,
    "true to size": 1.5,
    "looks great": 1.5,
    "looks amazing": 1.8,
    "beautiful": 1.5,
    "stunning": 1.8,
    "exactly as": 1.5,
    "well made": 1.5,
    "well packaged": 1.3,
    "carefully packaged": 1.3,
    "no issues": 1.0,
    "no problem": 1.0,
}

# Negative patterns with weights
NEGATIVE_PATTERNS = {
    # Strong negative (weight: 2.0)
    "hate it": 2.0,
    "hate this": 2.0,
    "terrible": 2.0,
    "horrible": 2.0,
    "awful": 2.0,
    "worst": 2.0,
    "disgusting": 2.0,
    "pathetic": 2.0,
    "ridiculous": 2.0,
    "unacceptable": 2.0,
    "useless": 2.0,
    "worthless": 2.0,
    "garbage": 2.0,
    "trash": 2.0,
    "junk": 2.0,
    "scam": 2.0,
    "fraud": 2.0,
    "never again": 2.0,
    "waste of money": 2.0,
    "waste of time": 2.0,
    # Moderate negative (weight: 1.5)
    "very bad": 1.5,
    "really bad": 1.5,
    "so bad": 1.5,
    "not working": 1.5,
    "doesn't work": 1.5,
    "does not work": 1.5,
    "stopped working": 1.5,
    "very disappointed": 1.5,
    "really disappointed": 1.5,
    "so disappointed": 1.5,
    "extremely disappointed": 1.5,
    "very frustrated": 1.5,
    "really frustrated": 1.5,
    "so frustrated": 1.5,
    "poor quality": 1.8,
    "bad quality": 1.8,
    "low quality": 1.8,
    "cheap quality": 1.8,
    "not happy": 1.5,
    "not satisfied": 1.5,
    "not impressed": 1.5,
    "would not recommend": 1.5,
    "wouldn't recommend": 1.5,
    "do not recommend": 1.5,
    "don't recommend": 1.5,
    "total waste": 1.5,
    # Standard negative (weight: 1.0)
    "bad": 1.0,
    "wrong": 1.0,
    "problem": 1.0,
    "issue": 1.0,
    "error": 1.0,
    "failed": 1.0,
    "fail": 1.0,
    "broken": 1.0,
    "slow": 1.0,
    "difficult": 1.0,
    "confusing": 1.0,
    "confused": 1.0,
    "stuck": 1.0,
    "frustrated": 1.0,
    "disappointed": 1.0,
    "angry": 1.0,
    "upset": 1.0,
    "annoyed": 1.0,
    "complaint": 1.0,
    "never": 1.0,
    "unable": 1.0,
    "cannot": 1.0,
    "can't": 1.0,
    "unfortunately": 1.0,
    # Ecommerce negative
    "late delivery": 1.8,
    "delayed shipping": 1.8,
    "still waiting": 1.5,
    "never arrived": 2.0,
    "didn't arrive": 1.8,
    "not delivered": 1.8,
    "missing item": 1.8,
    "wrong item": 1.8,
    "wrong size": 1.5,
    "doesn't fit": 1.5,
    "too small": 1.3,
    "too large": 1.3,
    "too big": 1.3,
    "too tight": 1.3,
    "too loose": 1.3,
    "not as described": 1.8,
    "not as pictured": 1.8,
    "misleading": 1.5,
    "deceptive": 1.5,
    "false advertising": 2.0,
    "return it": 1.3,
    "want a refund": 1.5,
    "need a refund": 1.5,
    "requesting refund": 1.5,
    "demand refund": 1.8,
    "refund my": 1.5,
    "exchange it": 1.0,
    "damaged": 1.5,
    "defective": 1.8,
    "defect": 1.5,
    "broken on arrival": 2.0,
    "arrived broken": 2.0,
    "arrived damaged": 2.0,
    "poor packaging": 1.5,
    "bad packaging": 1.5,
    "overpriced": 1.3,
    "ripoff": 1.8,
    "rip-off": 1.8,
    "not worth": 1.5,
}

# Negation words that flip sentiment
NEGATION_WORDS = {
    "not",
    "no",
    "never",
    "neither",
    "nobody",
    "nothing",
    "nowhere",
    "hardly",
    "barely",
    "scarcely",
    "seldom",
    "rarely",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
    "hasn't",
    "haven't",
    "hadn't",
    "doesn't",
    "don't",
    "didn't",
    "won't",
    "wouldn't",
    "couldn't",
    "shouldn't",
    "can't",
    "cannot",
    "mustn't",
}

# Phrases that indicate the negation applies to sentiment
NEGATION_SENTIMENT_PATTERNS = [
    r"not\s+(?:so\s+)?(?:good|great|helpful|satisfied|happy|impressed)",
    r"not\s+(?:very|really|that)\s+(?:good|great|helpful|satisfied|happy)",
    r"(?:isn't|wasn't|doesn't|didn't)\s+(?:good|great|helpful|working)",
    r"not\s+what\s+I\s+(?:expected|wanted|needed)",
    r"not\s+worth",
    r"wouldn't\s+recommend",
    r"can't\s+recommend",
    r"don't\s+(?:buy|order|recommend)",
]

# Positive emoji patterns
POSITIVE_EMOJIS = {
    "😀",
    "😃",
    "😄",
    "😁",
    "😊",
    "☺️",
    "🙂",
    "😉",
    "😍",
    "🥰",
    "😘",
    "😗",
    "😙",
    "😚",
    "😋",
    "😛",
    "😜",
    "🤗",
    "🤩",
    "🥳",
    "😎",
    "🤠",
    "👍",
    "👍🏻",
    "👍🏼",
    "👍🏽",
    "👍🏾",
    "👍🏿",
    "👏",
    "🙌",
    "💯",
    "✨",
    "🌟",
    "⭐",
    "❤️",
    "💕",
    "💖",
    "💗",
    "💓",
    "💞",
    "💕",
    "💟",
    "🙏",
    "🔥",
    "💪",
    "🏆",
}

# Negative emoji patterns
NEGATIVE_EMOJIS = {
    "😞",
    "😔",
    "😟",
    "😕",
    "🙁",
    "☹️",
    "😣",
    "😖",
    "😫",
    "😩",
    "🥺",
    "😢",
    "😭",
    "😤",
    "😠",
    "😡",
    "🤬",
    "😒",
    "🙄",
    "👎",
    "👎🏻",
    "👎🏼",
    "👎🏽",
    "👎🏾",
    "👎🏿",
    "💔",
    "🤦",
    "🤦🏻",
    "🤦🏼",
    "🤦🏽",
    "🤦🏾",
    "🤦🏿",
    "🤷",
    "🤷🏻",
    "🤷🏼",
    "🤷🏽",
    "🤷🏾",
    "🤷🏿",
    "👿",
    "💀",
    "☠️",
}

# Question words that reduce sentiment weight (customer asking for help)
QUESTION_INDICATORS = {
    "how",
    "what",
    "where",
    "when",
    "why",
    "who",
    "which",
    "can you",
    "could you",
    "would you",
    "will you",
    "is there",
    "do you",
    "does it",
    "did you",
    "has anyone",
    "help me",
    "i need",
    "i want",
    "looking for",
    "trying to",
}


class SentimentAnalyzer:
    """
    Enhanced sentiment analyzer with weighted scoring and context awareness.
    """

    def __init__(self) -> None:
        self._positive_patterns = self._compile_patterns(POSITIVE_PATTERNS)
        self._negative_patterns = self._compile_patterns(NEGATIVE_PATTERNS)
        self._negation_pattern = re.compile(
            r"(?:" + "|".join(re.escape(p) for p in NEGATION_SENTIMENT_PATTERNS) + r")",
            re.IGNORECASE,
        )

    def _compile_patterns(self, patterns: dict[str, float]) -> list[tuple[re.Pattern, float]]:
        """Compile regex patterns for efficient matching."""
        compiled = []
        for phrase, weight in sorted(patterns.items(), key=lambda x: -len(x[0])):
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            compiled.append((pattern, weight))
        return compiled

    def analyze(self, content: str) -> SentimentScore:
        """
        Analyze sentiment of text content.

        Returns SentimentScore with:
        - sentiment: positive/negative/neutral
        - positive_score: weighted positive score
        - negative_score: weighted negative score
        - confidence: 0.0 to 1.0
        - matched_terms: list of matched sentiment terms
        """
        if not content or not content.strip():
            return SentimentScore(
                sentiment=Sentiment.NEUTRAL,
                positive_score=0.0,
                negative_score=0.0,
                confidence=1.0,
                matched_terms=[],
            )

        content_lower = content.lower()
        matched_terms = []

        # Check for explicit negation-sentiment patterns first
        negation_matches = self._negation_pattern.findall(content_lower)
        negation_negative_score = len(negation_matches) * 1.5

        # Match positive patterns
        positive_score = 0.0
        for pattern, weight in self._positive_patterns:
            matches = pattern.findall(content_lower)
            if matches:
                positive_score += len(matches) * weight
                matched_terms.extend(matches)

        # Match negative patterns
        negative_score = 0.0
        for pattern, weight in self._negative_patterns:
            matches = pattern.findall(content_lower)
            if matches:
                negative_score += len(matches) * weight
                matched_terms.extend(matches)

        # Add negation patterns to negative score
        negative_score += negation_negative_score
        if negation_matches:
            matched_terms.extend(negation_matches)

        # Check for emoji sentiment
        positive_score += sum(1 for emoji in POSITIVE_EMOJIS if emoji in content)
        negative_score += sum(1 for emoji in NEGATIVE_EMOJIS if emoji in content)

        # Check for negation context that might flip sentiment
        # If we find a negation word within 3 words before a positive term, flip to negative
        words = content_lower.split()
        for i, word in enumerate(words):
            clean_word = word.strip(".,!?;:")
            if clean_word in NEGATION_WORDS:
                # Look ahead up to 3 words for sentiment words
                for j in range(i + 1, min(i + 4, len(words))):
                    next_word = words[j].strip(".,!?;:")
                    if next_word in {
                        "good",
                        "great",
                        "helpful",
                        "satisfied",
                        "happy",
                        "impressed",
                        "nice",
                    }:
                        positive_score *= 0.2
                        negative_score += 1.5
                        break

        # Reduce weight if this looks like a question/help request
        is_question = any(indicator in content_lower for indicator in QUESTION_INDICATORS)
        if is_question:
            positive_score *= 0.7
            negative_score *= 0.7

        # Calculate total and determine sentiment
        total_score = positive_score + negative_score

        if total_score == 0:
            return SentimentScore(
                sentiment=Sentiment.NEUTRAL,
                positive_score=0.0,
                negative_score=0.0,
                confidence=0.5,
                matched_terms=[],
            )

        # Determine sentiment based on relative scores
        positive_ratio = positive_score / total_score

        if positive_ratio >= 0.6:
            sentiment = Sentiment.POSITIVE
        elif positive_ratio <= 0.4:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL

        # Confidence is based on how far from neutral (0.5) the ratio is
        confidence = abs(positive_ratio - 0.5) * 2

        return SentimentScore(
            sentiment=sentiment,
            positive_score=round(positive_score, 2),
            negative_score=round(negative_score, 2),
            confidence=round(confidence, 2),
            matched_terms=list(set(matched_terms)),
        )

    def get_sentiment(self, content: str) -> str:
        """Simple interface that returns just the sentiment string."""
        return self.analyze(content).sentiment.value


# Singleton instance
_analyzer = SentimentAnalyzer()


def analyze_sentiment(content: str) -> str:
    """Convenience function for backward compatibility."""
    return _analyzer.get_sentiment(content)


def get_sentiment_score(content: str) -> SentimentScore:
    """Get full sentiment analysis with scores."""
    return _analyzer.analyze(content)
