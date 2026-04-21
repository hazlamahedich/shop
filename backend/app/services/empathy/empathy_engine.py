"""Empathy Engine for emotionally intelligent bot responses.

Builds on existing sentiment analysis to provide truly empathetic responses
that detect and respond to user's emotional state appropriately.

Key features:
- Deep emotional state detection (beyond just positive/negative)
- Emotional journey tracking throughout conversation
- Appropriate empathy response generation
- Personality-aware empathetic responses
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog
from dataclasses import dataclass
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics.sentiment_analyzer import (
    Sentiment,
    SentimentScore,
    get_sentiment_score,
)
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class EmotionalState(str, Enum):
    """Deep emotional states beyond basic sentiment."""

    # Positive states
    EXCITED = "excited"
    GRATEFUL = "grateful"
    PLEASED = "pleased"
    RELIEVED = "relieved"
    HOPEFUL = "hopeful"
    CONFIDENT = "confident"

    # Negative states
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    DISAPPOINTED = "disappointed"
    WORRIED = "worried"
    CONFUSED = "confused"
    OVERWHELMED = "overwhelmed"
    SAD = "sad"
    ANNOYED = "annoyed"

    # Neutral states
    CURIOUS = "curious"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class EmpathyLevel(str, Enum):
    """Levels of empathy required."""

    NONE = "none"  # No empathy needed
    LOW = "low"  # Acknowledge emotion
    MEDIUM = "medium"  # Validate emotion
    HIGH = "high"  # Deep empathy and support


@dataclass
class EmotionalProfile:
    """Complete emotional profile of user's current state."""

    primary_emotion: EmotionalState
    secondary_emotions: list[EmotionalState]
    empathy_level: EmpathyLevel
    intensity: float  # 0.0 to 1.0
    triggers: list[str]  # What caused this emotion
    suggested_responses: list[str]
    confidence: float  # 0.0 to 1.0


class EmpathyEngine:
    """
    Empathy engine for emotionally intelligent responses.

    Detects user's emotional state and generates appropriate empathetic responses.
    """

    # Emotional trigger patterns
    EMOTIONAL_PATTERNS = {
        # Frustration patterns
        EmotionalState.FRUSTRATED: {
            "keywords": ["frustrated", "stuck", "nowhere", "can't", "won't", "doesn't work"],
            "intensity_keywords": ["very", "really", "so", "extremely", "totally"],
            "emoji_indicators": ["😤", "😠", "😡"],
            "context_clues": ["tried everything", "nothing works", "gave up"],
        },
        # Anger patterns
        EmotionalState.ANGRY: {
            "keywords": ["angry", "furious", "outraged", "unacceptable", "ridiculous"],
            "intensity_keywords": ["very", "really", "absolutely", "completely"],
            "emoji_indicators": ["😡", "🤬", "😠"],
            "context_clues": ["demand", "refund", "manager", "complaint"],
        },
        # Disappointment patterns
        EmotionalState.DISAPPOINTED: {
            "keywords": ["disappointed", "let down", "expected better", "not what expected"],
            "intensity_keywords": ["very", "really", "so", "bitterly"],
            "emoji_indicators": ["😞", "😔", "😕"],
            "context_clues": ["hoped for", "wanted", "looked forward to"],
        },
        # Worry patterns
        EmotionalState.WORRIED: {
            "keywords": ["worried", "concerned", "anxious", "nervous", "scared"],
            "intensity_keywords": ["very", "really", "so", "extremely"],
            "emoji_indicators": ["😟", "😰", "😨"],
            "context_clues": ["what if", "not sure", "might not", "afraid"],
        },
        # Confusion patterns
        EmotionalState.CONFUSED: {
            "keywords": ["confused", "don't understand", "not clear", "unsure", "uncertain"],
            "intensity_keywords": ["very", "really", "so", "totally"],
            "emoji_indicators": ["😕", "🤔", "❓"],
            "context_clues": ["how do I", "what do you mean", "not sure how"],
        },
        # Gratitude patterns
        EmotionalState.GRATEFUL: {
            "keywords": ["thank", "appreciate", "grateful", "thanks so much"],
            "intensity_keywords": ["very", "really", "so", "extremely"],
            "emoji_indicators": ["😊", "🙏", "❤️", "🥰"],
            "context_clues": ["you're amazing", "so helpful", "saved me"],
        },
        # Excitement patterns
        EmotionalState.EXCITED: {
            "keywords": ["excited", "amazing", "can't wait", "love it", "finally"],
            "intensity_keywords": ["so", "very", "really", "absolutely", "totally"],
            "emoji_indicators": ["🎉", "😃", "🤩", "✨"],
            "context_clues": ["just got", "finally found", "perfect for"],
        },
    }

    # Empathy response templates by emotion and personality
    EMPATHY_RESPONSES = {
        # Frustration responses
        EmotionalState.FRUSTRATED: {
            PersonalityType.FRIENDLY: [
                "Oh no, I can hear how frustrating that is! 😕 Let me help you fix this.",
                "That sounds really frustrating! I'm so sorry you're dealing with this.",
                "Ugh, that's so annoying! Let me see what I can do to help.",
                "I totally get why you're frustrated! Let's work through this together.",
            ],
            PersonalityType.PROFESSIONAL: [
                "I understand your frustration. Let me assist you in resolving this.",
                "I apologize for the inconvenience. Let me help you address this issue.",
                "I can see this is frustrating. Let me work to resolve this for you.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "Oh no!!! That's so frustrating!!! Let me help you fix it right away!!!",
                "That sounds terrible! Let's get this sorted out for you!!!",
                "Ugh, I hate when that happens!!! Let me help you!!!",
            ],
        },
        # Anger responses
        EmotionalState.ANGRY: {
            PersonalityType.FRIENDLY: [
                "I completely understand why you're angry, and I'm so sorry about this.",
                "You have every right to be upset. Let me make this right for you.",
                "I hear your frustration, and I want to fix this immediately.",
            ],
            PersonalityType.PROFESSIONAL: [
                "I understand your anger. Let me take immediate action to resolve this.",
                "I apologize for this experience. Let me rectify the situation.",
                "I can see why you're upset. Let me address this right away.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "Oh no!!! I'm so sorry you're angry!!! Let me fix this right now!!!",
                "That's totally unacceptable!!! Let me make it up to you!!!",
            ],
        },
        # Disappointment responses
        EmotionalState.DISAPPOINTED: {
            PersonalityType.FRIENDLY: [
                "I'm so sorry it didn't meet your expectations! Let me see what we can do.",
                "I can hear the disappointment in your message. Let me help make this better.",
                "That's really disappointing, I understand. Let's find a solution together.",
            ],
            PersonalityType.PROFESSIONAL: [
                "I understand your disappointment. Let me work to improve this situation.",
                "I apologize that this didn't meet expectations. Let me assist you.",
                "I can see this is disappointing. Let me help address your concerns.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "Oh no! That's so disappointing!!! Let me help make it better!!!",
                "I'm so sorry it didn't work out!!! Let's find something great instead!!!",
            ],
        },
        # Worry responses
        EmotionalState.WORRIED: {
            PersonalityType.FRIENDLY: [
                "I can hear the concern in your message. Don't worry, I'm here to help!",
                "That sounds worrying! Let me reassure you - we'll get this sorted out.",
                "I understand your concern. Let me put your mind at ease.",
            ],
            PersonalityType.PROFESSIONAL: [
                "I understand your concern. Let me provide the information you need.",
                "I can see you're worried. Let me address your concerns directly.",
                "I appreciate you sharing your concern. Let me help clarify this.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "Don't worry!!! I'm here to help you figure this out!!!",
                "I can help with that! No need to worry - we've got this!!!",
            ],
        },
        # Confusion responses
        EmotionalState.CONFUSED: {
            PersonalityType.FRIENDLY: [
                "No worries! Let me clarify that for you step by step.",
                "I can see how that might be confusing! Let me break it down for you.",
                "That's a great question! Let me explain that more clearly.",
            ],
            PersonalityType.PROFESSIONAL: [
                "I understand your confusion. Let me provide clearer information.",
                "I can see how this might be unclear. Let me explain it more thoroughly.",
                "Thank you for asking. Let me clarify this for you.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "Great question!!! Let me explain that super clearly for you!!!",
                "No problem! Let me break that down so it's totally clear!!!",
            ],
        },
        # Gratitude responses
        EmotionalState.GRATEFUL: {
            PersonalityType.FRIENDLY: [
                "You're so welcome! 😊 It makes my day to hear that!",
                "Aww, thank YOU so much! I'm so glad I could help!",
                "That's so kind of you to say! I really appreciate it!",
            ],
            PersonalityType.PROFESSIONAL: [
                "You're very welcome. I'm glad I could be of assistance.",
                "Thank you for your kind words. It's my pleasure to help.",
                "I appreciate your feedback. Thank you for choosing us.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "OMG YAY!!! That makes me so happy!!! You're the best!!!",
                "You're AMAZING!!! Thank you so much for saying that!!!",
                "WOOHOO!!! I'm so glad I could help!!! You made my day!!!",
            ],
        },
        # Excitement responses
        EmotionalState.EXCITED: {
            PersonalityType.FRIENDLY: [
                "Yay! I'm so excited for you! That sounds amazing!",
                "That's fantastic! I can hear the excitement in your message!",
                "How wonderful! I'm so happy this worked out for you!",
            ],
            PersonalityType.PROFESSIONAL: [
                "That's excellent news. I'm pleased this worked out well.",
                "Wonderful! I'm glad to hear this positive outcome.",
                "That's great to hear! I'm happy this was successful.",
            ],
            PersonalityType.ENTHUSIASTIC: [
                "YAY!!! That's AMAZING!!! I'm so excited for you!!!",
                "WOOHOO!!! That's fantastic news!!! Let's celebrate!!!",
                "OMG!!! That's so great!!! I'm so happy for you!!!",
            ],
        },
    }

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def analyze_emotional_state(
        self,
        message: str,
        conversation_id: int,
        personality: PersonalityType = PersonalityType.FRIENDLY,
    ) -> EmotionalProfile:
        """Analyze user's emotional state from their message.

        Args:
            message: User's message
            conversation_id: Conversation ID
            personality: Bot's personality type

        Returns:
            Complete emotional profile
        """
        # Get base sentiment
        sentiment_score = get_sentiment_score(message)

        # Detect deeper emotional state
        primary_emotion = self._detect_primary_emotion(message, sentiment_score)

        # Calculate intensity
        intensity = self._calculate_emotional_intensity(message, primary_emotion)

        # Determine empathy level needed
        empathy_level = self._determine_empathy_level(primary_emotion, intensity)

        # Identify triggers
        triggers = self._identify_emotional_triggers(message, primary_emotion)

        # Generate suggested responses
        suggested_responses = self._generate_empathetic_responses(
            primary_emotion, personality, empathy_level
        )

        # Calculate confidence
        confidence = self._calculate_confidence(sentiment_score, triggers)

        return EmotionalProfile(
            primary_emotion=primary_emotion,
            secondary_emotions=self._detect_secondary_emotions(message),
            empathy_level=empathy_level,
            intensity=intensity,
            triggers=triggers,
            suggested_responses=suggested_responses,
            confidence=confidence,
        )

    def _detect_primary_emotion(
        self,
        message: str,
        sentiment_score: SentimentScore,
    ) -> EmotionalState:
        """Detect primary emotional state from message.

        Args:
            message: User's message
            sentiment_score: Sentiment analysis result

        Returns:
            Detected primary emotional state
        """
        message_lower = message.lower()

        # Check each emotional state's patterns
        for emotion, patterns in self.EMOTIONAL_PATTERNS.items():
            score = 0.0

            # Check keyword matches
            for keyword in patterns["keywords"]:
                if keyword in message_lower:
                    score += 1.0

            # Check intensity keywords
            for int_kw in patterns["intensity_keywords"]:
                if int_kw in message_lower:
                    score += 0.5

            # Check emoji indicators
            for emoji_char in patterns["emoji_indicators"]:
                if emoji_char in message:
                    score += 1.5

            # Check context clues
            for clue in patterns["context_clues"]:
                if clue in message_lower:
                    score += 1.0

            # If we have strong matches, return this emotion
            if score >= 2.0:
                return emotion

        # Fall back to basic sentiment
        if sentiment_score.sentiment == Sentiment.POSITIVE:
            if sentiment_score.confidence > 0.5:
                return EmotionalState.EXCITED
            return EmotionalState.PLEASED
        elif sentiment_score.sentiment == Sentiment.NEGATIVE:
            if sentiment_score.confidence > 0.5:
                return EmotionalState.FRUSTRATED
            return EmotionalState.ANNOYED
        else:
            return EmotionalState.NEUTRAL

    def _calculate_emotional_intensity(
        self,
        message: str,
        emotion: EmotionalState,
    ) -> float:
        """Calculate the intensity of the emotion (0.0 to 1.0).

        Args:
            message: User's message
            emotion: Detected emotion

        Returns:
            Intensity score from 0.0 to 1.0
        """
        message_lower = message.lower()
        intensity = 0.0

        # Check for intensity indicators
        intense_indicators = [
            "very", "really", "so", "extremely", "totally", "absolutely",
            "completely", "utterly", "incredibly", "remarkably"
        ]

        for indicator in intense_indicators:
            if indicator in message_lower:
                intensity += 0.2

        # Check for capitalization (all caps = high intensity)
        if message.isupper():
            intensity += 0.3

        # Check for exclamation marks (more ! = higher intensity)
        exclamations = message.count("!")
        intensity += min(exclamations * 0.1, 0.3)

        # Check for repeated punctuation (??? or !!!)
        if "!!!" in message or "???" in message:
            intensity += 0.2

        return min(intensity, 1.0)

    def _determine_empathy_level(
        self,
        emotion: EmotionalState,
        intensity: float,
    ) -> EmpathyLevel:
        """Determine how much empathy is needed.

        Args:
            emotion: Primary emotional state
            intensity: Emotional intensity

        Returns:
            Required empathy level
        """
        # Negative emotions require more empathy
        if emotion in [
            EmotionalState.ANGRY,
            EmotionalState.FRUSTRATED,
            EmotionalState.DISAPPOINTED,
            EmotionalState.SAD,
        ]:
            if intensity > 0.7:
                return EmpathyLevel.HIGH
            elif intensity > 0.4:
                return EmpathyLevel.MEDIUM
            else:
                return EmpathyLevel.LOW

        # Worry and confusion need medium empathy
        elif emotion in [EmotionalState.WORRIED, EmotionalState.CONFUSED]:
            return EmpathyLevel.MEDIUM

        # Positive emotions need acknowledgment
        elif emotion in [EmotionalState.EXCITED, EmotionalState.GRATEFUL]:
            return EmpathyLevel.LOW

        # Neutral needs minimal empathy
        return EmpathyLevel.NONE

    def _identify_emotional_triggers(
        self,
        message: str,
        emotion: EmotionalState,
    ) -> list[str]:
        """Identify what triggered this emotion.

        Args:
            message: User's message
            emotion: Detected emotion

        Returns:
            List of trigger phrases
        """
        triggers = []

        # Common trigger patterns
        if emotion == EmotionalState.FRUSTRATED:
            frustration_triggers = [
                "doesn't work", "can't", "won't", "stuck", "broken",
                "not working", "failed", "error", "problem"
            ]
            for trigger in frustration_triggers:
                if trigger in message.lower():
                    triggers.append(trigger)

        elif emotion == EmotionalState.ANGRY:
            anger_triggers = [
                "late", "delayed", "didn't arrive", "wrong item", "poor quality",
                "terrible service", "unacceptable", "ridiculous"
            ]
            for trigger in anger_triggers:
                if trigger in message.lower():
                    triggers.append(trigger)

        elif emotion == EmotionalState.WORRIED:
            worry_triggers = [
                "will it", "what if", "not sure", "might not", "could be",
                "afraid", "concerned about", "nervous about"
            ]
            for trigger in worry_triggers:
                if trigger in message.lower():
                    triggers.append(trigger)

        return triggers

    def _generate_empathetic_responses(
        self,
        emotion: EmotionalState,
        personality: PersonalityType,
        empathy_level: EmpathyLevel,
    ) -> list[str]:
        """Generate empathetic responses based on emotion and personality.

        Args:
            emotion: User's emotional state
            personality: Bot's personality type
            empathy_level: Required empathy level

        Returns:
            List of suggested empathetic responses
        """
        # Get base responses for this emotion
        base_responses = self.EMPATHY_RESPONSES.get(
            emotion,
            self.EMPATHY_RESPONSES[EmotionalState.FRUSTRATED]  # Fallback
        )

        # Get personality-specific responses
        personality_responses = base_responses.get(
            personality,
            base_responses[PersonalityType.FRIENDLY]  # Fallback
        )

        return personality_responses

    def _detect_secondary_emotions(
        self,
        message: str,
    ) -> list[EmotionalState]:
        """Detect secondary emotions present in the message.

        Args:
            message: User's message

        Returns:
            List of secondary emotional states
        """
        secondary = []
        message_lower = message.lower()

        # Check for multiple emotions
        for emotion, patterns in self.EMOTIONAL_PATTERNS.items():
            for keyword in patterns["keywords"]:
                if keyword in message_lower and emotion not in secondary:
                    secondary.append(emotion)
                    break

        return secondary

    def _calculate_confidence(
        self,
        sentiment_score: SentimentScore,
        triggers: list[str],
    ) -> float:
        """Calculate confidence in emotional analysis.

        Args:
            sentiment_score: Sentiment analysis result
            triggers: Identified triggers

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Base confidence from sentiment analysis
        confidence = sentiment_score.confidence

        # Boost confidence if we found clear triggers
        if len(triggers) >= 2:
            confidence = min(confidence + 0.2, 1.0)
        elif len(triggers) == 1:
            confidence = min(confidence + 0.1, 1.0)

        return confidence

    async def track_emotional_journey(
        self,
        conversation_id: int,
        emotional_profile: EmotionalProfile,
    ) -> dict[str, Any]:
        """Track emotional journey throughout conversation.

        Args:
            conversation_id: Conversation ID
            emotional_profile: Current emotional profile

        Returns:
            Emotional journey data
        """
        # Get existing journey from Redis
        journey = await self._get_emotional_journey(conversation_id)

        # Add current emotional state
        journey["emotional_states"].append({
            "emotion": emotional_profile.primary_emotion.value,
            "intensity": emotional_profile.intensity,
            "empathy_level": emotional_profile.empathy_level.value,
            "triggers": emotional_profile.triggers,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Calculate emotional trends
        journey["emotional_trends"] = self._analyze_emotional_trends(
            journey["emotional_states"]
        )

        # Persist to Redis
        if self.redis:
            try:
                self.redis.setex(
                    f"emotional_journey:{conversation_id}",
                    86400,  # 24 hours
                    json.dumps(journey),
                )
            except Exception as e:
                self.logger.warning("Redis set failed", error=str(e))

        return journey

    async def _get_emotional_journey(
        self,
        conversation_id: int,
    ) -> dict[str, Any]:
        """Get existing emotional journey from Redis.

        Args:
            conversation_id: Conversation ID

        Returns:
            Emotional journey data
        """
        # Try Redis first
        if self.redis:
            try:
                journey_json = self.redis.get(f"emotional_journey:{conversation_id}")
                if journey_json:
                    return json.loads(journey_json)
            except Exception as e:
                self.logger.warning("Redis get failed", error=str(e))

        # Return new journey structure
        return {
            "conversation_id": conversation_id,
            "emotional_states": [],
            "emotional_trends": {
                "primary_emotion": EmotionalState.NEUTRAL.value,
                "emotion_stability": 1.0,  # How stable emotion is
                "emotional_progress": 0.0,  # Are emotions improving?
            },
        }

    def _analyze_emotional_trends(
        self,
        emotional_states: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze trends in emotional states.

        Args:
            emotional_states: List of emotional states

        Returns:
            Trend analysis
        """
        if not emotional_states:
            return {
                "primary_emotion": EmotionalState.NEUTRAL.value,
                "emotion_stability": 1.0,
                "emotional_progress": 0.0,
            }

        # Find most common emotion
        emotion_counts = {}
        for state in emotional_states:
            emotion = state["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        primary_emotion = max(emotion_counts, key=emotion_counts.get)

        # Calculate emotional stability (how much emotion changes)
        if len(emotional_states) >= 3:
            recent_states = emotional_states[-3:]
            emotions = [s["emotion"] for s in recent_states]
            unique_emotions = len(set(emotions))
            stability = 1.0 - (unique_emotions - 1) / 2.0
        else:
            stability = 1.0

        # Calculate emotional progress (are negative emotions decreasing?)
        if len(emotional_states) >= 2:
            recent_states = emotional_states[-3:]
            negative_count = sum(
                1 for s in recent_states
                if s["emotion"] in ["angry", "frustrated", "disappointed", "sad"]
            )
            # Progress = reducing negative emotions
            progress = max(0.0, 1.0 - (negative_count / len(recent_states)))
        else:
            progress = 0.0

        return {
            "primary_emotion": primary_emotion,
            "emotion_stability": round(stability, 2),
            "emotional_progress": round(progress, 2),
        }


# Convenience function for quick emotional analysis
async def analyze_and_respond_with_empathy(
    message: str,
    conversation_id: int,
    personality: PersonalityType = PersonalityType.FRIENDLY,
    db: AsyncSession | None = None,
    redis_client: Redis | None = None,
) -> dict[str, Any]:
    """
    Quick function to analyze emotion and get empathetic response suggestions.

    Args:
        message: User's message
        conversation_id: Conversation ID
        personality: Bot's personality
        db: Database session
        redis_client: Redis client

    Returns:
        Emotional profile with response suggestions
    """
    empathy_engine = EmpathyEngine(db, redis_client)

    emotional_profile = await empathy_engine.analyze_emotional_state(
        message, conversation_id, personality
    )

    # Track emotional journey
    await empathy_engine.track_emotional_journey(
        conversation_id, emotional_profile
    )

    return {
        "emotional_profile": emotional_profile,
        "suggested_responses": emotional_profile.suggested_responses,
        "empathy_level": emotional_profile.empathy_level.value,
        "intensity": emotional_profile.intensity,
        "confidence": emotional_profile.confidence,
    }
