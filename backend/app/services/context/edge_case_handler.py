"""Edge case handling system for improved conversational quality.

Addresses the 4 critical edge case weaknesses:
1. Extreme Context Switching (48% → 85% target)
2. Personality Adaptation (55% → 80% target)
3. Reference Resolution (58% → 85% target)
4. Context Contradiction (68% → 85% target)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import ConversationContext
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class EdgeCaseHandler:
    """Handles difficult edge cases in conversations.

    Key improvements:
    - Extreme context switching (multiple rapid topic changes)
    - Personality adaptation requests (user demands tone change)
    - Reference resolution (ambiguous pronouns)
    - Context contradictions (conflicting user information)
    """

    REDIS_KEY_PREFIX = "edge_case_context"
    REDIS_TTL_SECONDS = 86400  # 24 hours

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def handle_extreme_context_switching(
        self,
        conversation_id: int,
        merchant_id: int,
        topic_history: list[dict[str, str]],
        current_personality: str = "friendly",
    ) -> dict[str, Any]:
        """Handle extreme context switching (6+ rapid topic changes).

        Strategy:
        1. Maintain topic stack (last 5 topics)
        2. Create topic clusters (group related topics)
        3. Provide summaries for each cluster
        4. Enable quick context restoration

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            topic_history: List of topic switches
            current_personality: Current personality type

        Returns:
            Enhanced context with topic management
        """
        # Maintain topic stack (last 5)
        topic_stack = topic_history[-5:] if len(topic_history) > 5 else topic_history

        # Create topic clusters
        topic_clusters = self._cluster_topics(topic_stack)

        # Generate summaries for each cluster
        cluster_summaries = {}
        for cluster_name, topics in topic_clusters.items():
            cluster_summaries[cluster_name] = {
                "topics": [t["to"] for t in topics],
                "count": len(topics),
                "last_discussed": topics[-1]["timestamp"],
                "summary": self._generate_cluster_summary(cluster_name, topics, current_personality),
            }

        # Store for quick restoration
        enhanced_context = {
            "conversation_id": conversation_id,
            "topic_stack": topic_stack,
            "topic_clusters": topic_clusters,
            "cluster_summaries": cluster_summaries,
            "context_restoration_phrases": self._generate_restoration_phrases(
                topic_clusters, current_personality
            ),
        }

        # Persist to Redis for fast access
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(enhanced_context),
                )
            except Exception as e:
                self.logger.warning("Redis set failed", error=str(e))

        return enhanced_context

    async def handle_personality_adaptation(
        self,
        conversation_id: int,
        merchant_id: int,
        current_personality: PersonalityType,
        adaptation_request: str,
    ) -> dict[str, Any]:
        """Handle personality adaptation requests.

        Strategy:
        1. Detect if request is legitimate (not just frustration)
        2. Gradually transition personality (not abrupt switch)
        3. Maintain core bot identity
        4. Provide smooth transition phrases

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            current_personality: Current personality type
            adaptation_request: User's request for tone change

        Returns:
            Adaptation strategy and transition phrases
        """
        # Detect legitimate adaptation vs frustration
        is_frustration = self._detect_frustration_vs_adaptation(adaptation_request)

        if is_frustration:
            # Don't change personality, show empathy instead
            return {
                "should_adapt": False,
                "reason": "user_frustration",
                "response_strategy": "empathy",
                "suggested_responses": [
                    "I understand your frustration. Let me help you better.",
                    "I hear you, and I want to make this right. How can I improve?",
                ],
            }

        # Determine target personality
        target_personality = self._determine_target_personality(
            adaptation_request, current_personality
        )

        if target_personality == current_personality:
            return {
                "should_adapt": False,
                "reason": "already_matches",
                "response_strategy": "acknowledge",
            }

        # Create gradual transition strategy
        transition_phrases = self._generate_personality_transition_phrases(
            current_personality, target_personality
        )

        return {
            "should_adapt": True,
            "current_personality": current_personality.value,
            "target_personality": target_personality.value,
            "transition_strategy": "gradual",
            "transition_phrases": transition_phrases,
            "response_strategy": "adapt_and_acknowledge",
        }

    async def handle_reference_resolution(
        self,
        conversation_id: int,
        message: str,
        conversation_history: list[dict[str, str]],
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Handle ambiguous pronoun references.

        Strategy:
        1. Identify ambiguous pronouns (it, they, that, this)
        2. Find all possible antecedents from recent conversation
        2. Score antecedents by recency and relevance
        3. Request clarification if confidence < 70%
        4. Provide disambiguation options

        Args:
            conversation_id: Conversation ID
            message: User's message with ambiguous reference
            conversation_history: Recent conversation turns
            personality: Personality type

        Returns:
            Reference resolution with clarification if needed
        """
        # Identify ambiguous pronouns
        ambiguous_pronouns = self._identify_ambiguous_pronouns(message)

        if not ambiguous_pronouns:
            return {"needs_clarification": False}

        # Find antecedents from conversation history
        antecedents = self._find_antecedents(conversation_history)

        if not antecedents:
            return {
                "needs_clarification": True,
                "reason": "no_antecedents",
                "clarification_question": self._generate_clarification_question(
                    message, None, personality
                ),
            }

        # Score antecedents
        scored_antecedents = self._score_antecedents(
            antecedents, ambiguous_pronouns, conversation_history
        )

        # Check if top score is confident enough
        top_score = scored_antecedents[0]["score"] if scored_antecedents else 0.0

        if top_score >= 0.70:
            # Confident resolution
            return {
                "needs_clarification": False,
                "resolved_reference": scored_antecedents[0]["reference"],
                "confidence": top_score,
            }
        else:
            # Needs clarification
            return {
                "needs_clarification": True,
                "reason": "low_confidence",
                "confidence": top_score,
                "possible_references": scored_antecedents[:3],  # Top 3 options
                "clarification_question": self._generate_clarification_question(
                    message, scored_antecedents[:3], personality
                ),
            }

    async def handle_context_contradiction(
        self,
        conversation_id: int,
        old_context: dict[str, Any],
        new_information: dict[str, Any],
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Handle contradictory user information.

        Strategy:
        1. Detect contradictions between old and new information
        2. Determine if this is a correction or genuine contradiction
        3. Request confirmation for contradictions
        4. Apply "last mentioned wins" with confirmation

        Args:
            conversation_id: Conversation ID
            old_context: Previous context
            new_information: New (potentially contradictory) information
            personality: Personality type

        Returns:
            Contradiction handling strategy
        """
        contradictions = self._detect_contradictions(old_context, new_information)

        if not contradictions:
            return {"has_contradictions": False}

        # Determine if correction or contradiction
        correction_patterns = [
            r"(actually|wait|sorry|i mean|no,|correction)",
            r"(forget what i said|ignore that|scratch that)",
        ]

        message = str(new_information)
        is_correction = any(re.search(pattern, message.lower()) for pattern in correction_patterns)

        if is_correction:
            # User is explicitly correcting themselves
            return {
                "has_contradictions": True,
                "is_correction": True,
                "strategy": "accept_correction",
                "confirmation_phrase": f"Got it, I've updated that.",
            }
        else:
            # Potential contradiction - request confirmation
            return {
                "has_contradictions": True,
                "is_correction": False,
                "strategy": "request_confirmation",
                "contradictions": contradictions,
                "confirmation_phrase": self._generate_confirmation_phrase(
                    contradictions, personality
                ),
            }

    def _cluster_topics(
        self,
        topic_history: list[dict[str, str]]
    ) -> dict[str, list[dict[str, str]]]:
        """Cluster related topics together.

        Args:
            topic_history: List of topic switches

        Returns:
            Dictionary of topic clusters
        """
        # Topic clusters based on semantic similarity
        cluster_keywords = {
            "products": ["product", "necklace", "bracelet", "item", "search"],
            "shipping": ["shipping", "delivery", "arrive", "track", "package"],
            "returns": ["return", "refund", "exchange", "policy"],
            "checkout": ["checkout", "cart", "payment", "buy"],
            "general": ["hours", "location", "contact", "about"],
        }

        clusters = {name: [] for name in cluster_keywords}

        for topic_switch in topic_history:
            topic = topic_switch.get("to", "").lower()

            # Find matching cluster
            matched = False
            for cluster_name, keywords in cluster_keywords.items():
                if any(keyword in topic for keyword in keywords):
                    clusters[cluster_name].append(topic_switch)
                    matched = True
                    break

            if not matched:
                clusters["general"].append(topic_switch)

        # Remove empty clusters
        return {k: v for k, v in clusters.items() if v}

    def _generate_cluster_summary(
        self,
        cluster_name: str,
        topics: list[dict[str, str]],
        personality: str,
    ) -> str:
        """Generate summary for a topic cluster.

        Args:
            cluster_name: Name of the cluster
            topics: Topics in the cluster
            personality: Personality type

        Returns:
            Summary string
        """
        cluster_descriptions = {
            "products": "product browsing",
            "shipping": "shipping and delivery",
            "returns": "returns and exchanges",
            "checkout": "checkout process",
            "general": "general information",
        }

        activity = cluster_descriptions.get(cluster_name, "various topics")

        if personality == "professional":
            return f"Regarding {activity}"
        elif personality == "enthusiastic":
            return f"About the {activity}!!!"
        else:  # friendly
            return f"For the {activity}"

    def _generate_restoration_phrases(
        self,
        topic_clusters: dict[str, list[dict[str, str]]],
        personality: str,
    ) -> list[str]:
        """Generate phrases for restoring context.

        Args:
            topic_clusters: Topic clusters
            personality: Personality type

        Returns:
            List of restoration phrases
        """
        phrases = []

        for cluster_name, topics in topic_clusters.items():
            if not topics:
                continue

            last_topic = topics[-1].get("to", "")
            count = len(topics)

            if personality == "friendly":
                if count == 1:
                    phrases.append(f"Getting back to {last_topic}...")
                else:
                    phrases.append(f"Returning to {last_topic} (we discussed this earlier)...")
            elif personality == "professional":
                if count == 1:
                    phrases.append(f"Resuming our discussion about {last_topic}.")
                else:
                    phrases.append(f"Returning to {last_topic}, as previously discussed.")
            elif personality == "enthusiastic":
                if count == 1:
                    phrases.append(f"Back to {last_topic}!!!")
                else:
                    phrases.append(f"Let's get back to {last_topic}!!! We talked about this earlier!!!")

        return phrases

    def _detect_frustration_vs_adaptation(self, message: str) -> bool:
        """Detect if message is frustration or legitimate adaptation request.

        Args:
            message: User's message

        Returns:
            True if frustration detected
        """
        frustration_patterns = [
            r"(stop|quit|don't|can't you|useless|stupid|annoying)",
            r"(whatever|never mind|forget it|nevermind)",
        ]

        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in frustration_patterns)

    def _determine_target_personality(
        self,
        adaptation_request: str,
        current_personality: PersonalityType,
    ) -> PersonalityType:
        """Determine target personality from adaptation request.

        Args:
            adaptation_request: User's adaptation request
            current_personality: Current personality

        Returns:
            Target personality type
        """
        request_lower = adaptation_request.lower()

        # Professional requests
        professional_patterns = [
            r"(professional|formal|serious|business)",
            r"(stop being|don't be|less casual|not so friendly)",
        ]

        # Enthusiastic requests
        enthusiastic_patterns = [
            r"(enthusiastic|excited|energetic|happy)",
            r"(more energy|be excited|show enthusiasm)",
        ]

        # Friendly requests
        friendly_patterns = [
            r"(friendly|casual|relaxed|informal)",
            r"(less formal|more casual|chill out)",
        ]

        if any(re.search(pattern, request_lower) for pattern in professional_patterns):
            return PersonalityType.PROFESSIONAL
        elif any(re.search(pattern, request_lower) for pattern in enthusiastic_patterns):
            return PersonalityType.ENTHUSIASTIC
        elif any(re.search(pattern, request_lower) for pattern in friendly_patterns):
            return PersonalityType.FRIENDLY
        else:
            return current_personality

    def _generate_personality_transition_phrases(
        self,
        current: PersonalityType,
        target: PersonalityType,
    ) -> list[str]:
        """Generate smooth personality transition phrases.

        Args:
            current: Current personality
            target: Target personality

        Returns:
            List of transition phrases
        """
        transitions = {
            PersonalityType.FRIENDLY: {
                PersonalityType.PROFESSIONAL: [
                    "I'll switch to a more professional tone.",
                    "Let me adjust my communication style.",
                    "I understand - I'll be more formal now.",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "I'll bring more energy to our conversation!",
                    "Let me match your excitement!",
                    "Great! I'll be more enthusiastic!",
                ],
            },
            PersonalityType.PROFESSIONAL: {
                PersonalityType.FRIENDLY: [
                    "I'll adjust to a more conversational tone.",
                    "Let me be more casual in our communication.",
                    "I'll switch to a friendlier style.",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "I'll add more energy while staying professional.",
                    "Let me match your enthusiasm appropriately.",
                ],
            },
            PersonalityType.ENTHUSIASTIC: {
                PersonalityType.FRIENDLY: [
                    "I'll tone it down a bit and be more relaxed.",
                    "Let me adjust to a calmer conversation style.",
                ],
                PersonalityType.PROFESSIONAL: [
                    "I'll be more professional while staying helpful.",
                    "Let me switch to a more formal tone.",
                ],
            },
        }

        return transitions.get(current, {}).get(target, [])

    def _identify_ambiguous_pronouns(self, message: str) -> list[str]:
        """Identify ambiguous pronouns in message.

        Args:
            message: User's message

        Returns:
            List of ambiguous pronouns
        """
        ambiguous_patterns = [
            r"\b(it|this|that|these|those|they|them|one|ones)\b",
        ]

        pronouns = []
        message_lower = message.lower()

        for pattern in ambiguous_patterns:
            matches = re.findall(pattern, message_lower)
            pronouns.extend(matches)

        return list(set(pronouns))

    def _find_antecedents(
        self,
        conversation_history: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        """Find potential antecedents from conversation history.

        Args:
            conversation_history: Recent conversation turns

        Returns:
            List of potential antecedents
        """
        antecedents = []

        # Look for nouns and noun phrases in recent turns
        for turn in conversation_history[-5:]:  # Last 5 turns
            user_message = turn.get("user_message", "")

            # Simple noun extraction (in production, use NLP)
            noun_patterns = [
                r"\b(necklace|bracelet|ring|earring|product|item|gift)\b",
                r"\b(red|blue|green|gold|silver)\b",
                r"\b(\$?\d+)\b",  # Prices
            ]

            for pattern in noun_patterns:
                matches = re.findall(pattern, user_message, re.IGNORECASE)
                for match in matches:
                    antecedents.append({
                        "reference": match,
                        "turn_distance": len(conversation_history) - conversation_history.index(turn),
                        "context": user_message,
                    })

        return antecedents

    def _score_antecedents(
        self,
        antecedents: list[dict[str, Any]],
        pronouns: list[str],
        conversation_history: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Score antecedents by relevance.

        Args:
            antecedents: Potential antecedents
            pronouns: Ambiguous pronouns
            conversation_history: Conversation history

        Returns:
            Scored antecedents
        """
        scored = []

        for ant in antecedents:
            score = 0.0

            # Recency score (more recent = higher score)
            recency = ant.get("turn_distance", 1)
            score += max(0.0, 1.0 - (recency * 0.15))

            # Frequency score (mentioned multiple times)
            reference = ant.get("reference", "").lower()
            frequency = sum(
                1 for turn in conversation_history
                if reference in turn.get("user_message", "").lower()
            )
            score += min(frequency * 0.10, 0.30)

            # Context relevance
            context = ant.get("context", "")
            if any(word in context.lower() for word in ["looking", "want", "need", "like"]):
                score += 0.20

            scored.append({
                **ant,
                "score": min(score, 1.0),
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored

    def _generate_clarification_question(
        self,
        message: str,
        possible_references: list[dict[str, Any]] | None,
        personality: str,
    ) -> str:
        """Generate clarification question for ambiguous reference.

        Args:
            message: User's message
            possible_references: Possible antecedents
            personality: Personality type

        Returns:
            Clarification question
        """
        if personality == "professional":
            if possible_references:
                options = ", ".join([r["reference"] for r in possible_references[:2]])
                return f"Could you clarify which item you're referring to: {options}?"
            else:
                return "Could you specify which item you're referring to?"
        elif personality == "enthusiastic":
            if possible_references:
                options = " or ".join([r["reference"] for r in possible_references[:2]])
                return f"Which one?! {options}?!"
            else:
                return "Which item are you talking about?!"
        else:  # friendly
            if possible_references:
                options = " or ".join([r["reference"] for r in possible_references[:2]])
                return f"Which one did you mean - {options}?"
            else:
                return "Which item were you referring to?"

    def _detect_contradictions(
        self,
        old_context: dict[str, Any],
        new_information: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect contradictions between old and new information.

        Args:
            old_context: Previous context
            new_information: New information

        Returns:
            List of contradictions detected
        """
        contradictions = []

        # Check budget contradictions
        if "budget" in old_context and "budget" in new_information:
            old_budget = old_context.get("budget", {})
            new_budget = new_information.get("budget", {})

            if old_budget != new_budget:
                contradictions.append({
                    "field": "budget",
                    "old_value": old_budget,
                    "new_value": new_budget,
                    "type": "numeric_contradiction",
                })

        # Check preference contradictions
        preference_fields = ["color", "style", "size", "brand"]
        for field in preference_fields:
            if field in old_context and field in new_information:
                old_val = old_context.get(field)
                new_val = new_information.get(field)

                if old_val != new_val:
                    contradictions.append({
                        "field": field,
                        "old_value": old_val,
                        "new_value": new_val,
                        "type": "preference_contradiction",
                    })

        return contradictions

    def _generate_confirmation_phrase(
        self,
        contradictions: list[dict[str, Any]],
        personality: str,
    ) -> str:
        """Generate confirmation phrase for contradictions.

        Args:
            contradictions: List of contradictions
            personality: Personality type

        Returns:
            Confirmation phrase
        """
        if len(contradictions) == 1:
            c = contradictions[0]
            field = c["field"]
            old_val = c["old_value"]
            new_val = c["new_value"]

            if personality == "professional":
                return f"I noticed you mentioned {old_val} before, but now {new_val}. Would you like me to use {new_val}?"
            elif personality == "enthusiastic":
                return f"Wait! Before you said {old_val}, but now {new_val}! Which one do you prefer?!"
            else:  # friendly
                return f"Just to confirm - you mentioned {old_val} earlier, but now {new_val}. Should I go with {new_val}?"
        else:
            # Multiple contradictions
            if personality == "professional":
                return "I noticed some changes from what you mentioned earlier. Should I update with the new information?"
            elif personality == "enthusiastic":
                return "I noticed you changed a few things! Should I use the new info?!"
            else:  # friendly
                return "I noticed you changed a few things from earlier. Want me to use the new info?"
