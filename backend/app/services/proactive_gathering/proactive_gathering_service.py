from __future__ import annotations

import re
from typing import Any

import structlog

from app.models.merchant import PersonalityType
from app.services.conversation.schemas import ConversationContext
from app.services.intent.classification_schema import ExtractedEntities, IntentType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import TransitionCategory
from app.services.personality.transition_selector import get_transition_selector
from app.services.proactive_gathering.intent_requirements import INTENT_REQUIREMENTS, _SKIP_INTENTS
from app.services.proactive_gathering.schemas import GatheringState, MissingField

logger = structlog.get_logger(__name__)

_BUDGET_PATTERN = re.compile(
    r"(?:under|below|around|about|\$|usd?)\s*(\d+(?:\.\d{2})?)"
    r"|(\d+(?:\.\d{2})?)\s*(?:dollars?|bucks?|usd?)",
    re.IGNORECASE,
)

_SIZE_PATTERN = re.compile(
    r"\b(xs|s|m|l|xl|xxl|2xl|3xl|4xl|5xl|one\s*size|extra\s*small|small|"
    r"medium|large|extra\s*large)\b"
    r"|(\d+(?:\.\d+)?\s*(?:cm|mm|inch|in|eu|uk|us))",
    re.IGNORECASE,
)

_COLOR_PATTERN = re.compile(
    r"\b(red|blue|green|black|white|yellow|orange|pink|purple|brown|gray|grey|"
    r"navy|teal|coral|burgundy|beige|tan|ivory|maroon|lime|turquoise|"
    r"olive|magenta|gold|silver|bronze|copper|charcoal|aqua|"
    r"crimson|khaki|salmon|cerise|plum|lavender|indigo)\b",
    re.IGNORECASE,
)

_ORDER_NUMBER_PATTERN = re.compile(
    r"#?\d{4,}|ord-?\d+",
    re.IGNORECASE,
)

_BRAND_KNOWN = {
    "nike",
    "adidas",
    "puma",
    "reebok",
    "under armour",
    "underarmour",
    "new balance",
    "converse",
    "vans",
    "asics",
    "hoka",
    "brooks",
    "saucony",
    "on running",
    "onrunning",
    "salomon",
    "nordstrom",
    "zara",
    "h&m",
    "uniqlo",
    "gap",
    "old navy",
    "levis",
    "apple",
    "samsung",
    "sony",
}


class ProactiveGatheringService:
    def detect_missing_info(
        self,
        intent: IntentType,
        entities: ExtractedEntities,
        context: ConversationContext,
        mode: str,
        user_message: str = "",
    ) -> list[MissingField]:
        if intent in _SKIP_INTENTS:
            return []

        requirements = INTENT_REQUIREMENTS.get(intent, [])
        if not requirements:
            return []

        missing: list[MissingField] = []
        for req in requirements:
            if not self._is_mode_compatible(req.mode, mode):
                continue
            if self._field_already_known(req.field_name, entities, context, user_message):
                continue
            missing.append(
                MissingField(
                    field_name=req.field_name,
                    display_name=req.display_name,
                    priority=req.priority,
                    required=req.required,
                    mode=req.mode,
                    example_values=req.example_values,
                )
            )

        missing.sort(key=lambda f: f.priority)
        logger.info(
            "proactive_gathering_detected",
            intent=intent.value if hasattr(intent, "value") else str(intent),
            missing_count=len(missing),
            fields=[f.field_name for f in missing],
        )
        return missing

    def generate_gathering_message(
        self,
        missing_fields: list[MissingField],
        personality: str,
        bot_name: str,
        mode: str,
        context: ConversationContext,
        conversation_id: str,
    ) -> str:
        if not missing_fields:
            return ""

        personality_type = self._resolve_personality(personality)
        sorted_fields = sorted(missing_fields, key=lambda f: f.priority)
        field_names = [f.display_name for f in sorted_fields]
        combined_fields = self._combine_related_fields(sorted_fields)
        context_prefix = self._build_context_prefix(context, mode)

        try:
            if len(combined_fields) == 1:
                question_text = combined_fields[0]
            else:
                critical = [f for f in sorted_fields if f.priority == 1]
                nice_to_have = [f for f in sorted_fields if f.priority > 1]
                parts = []
                if critical:
                    parts.append(self._format_field_group(critical))
                if nice_to_have:
                    parts.append(self._format_field_group(nice_to_have))
                question_text = " Also, ".join(parts)
        except Exception:
            if len(combined_fields) == 1:
                question_text = combined_fields[0]
            else:
                question_text = f"I'd love to help! Could you share: {', '.join(field_names)}?"

        if context_prefix:
            question_text = f"{context_prefix} {question_text}"

        try:
            selector = get_transition_selector()
            transition = selector.select(
                TransitionCategory.CLARIFYING,
                personality_type,
                conversation_id,
                mode,
            )
            result = f"{transition} {question_text}"
        except Exception:
            result = question_text

        logger.info(
            "proactive_gathering_message_generated",
            field_count=len(missing_fields),
            fields=[f.field_name for f in missing_fields],
        )
        return result

    def extract_partial_answer(
        self,
        response: str,
        missing_fields: list[MissingField],
        mode: str,
    ) -> dict[str, Any]:
        extracted: dict[str, Any] = {}
        for field in missing_fields:
            value = self._extract_field_value(field.field_name, response)
            if value is not None:
                extracted[field.field_name] = value

        if not extracted and missing_fields:
            highest_priority = min(missing_fields, key=lambda f: f.priority)
            extracted[highest_priority.field_name] = response.strip()

        logger.info(
            "proactive_gathering_partial_extract",
            extracted_fields=list(extracted.keys()),
            remaining=[f.field_name for f in missing_fields if f.field_name not in extracted],
        )
        return extracted

    def _is_mode_compatible(self, field_mode: str, current_mode: str) -> bool:
        if field_mode == "both":
            return True
        return field_mode == current_mode

    def _field_already_known(
        self,
        field_name: str,
        entities: ExtractedEntities,
        context: ConversationContext,
        user_message: str = "",
    ) -> bool:
        entity_fields = {
            "budget": entities.budget,
            "size": entities.size,
            "color": entities.color,
            "brand": entities.brand,
            "order_number": entities.order_number,
            "category": entities.category,
            "product_identifier": entities.product_reference,
            "product_identifiers": entities.product_reference,
        }
        if field_name in entity_fields and entity_fields[field_name] is not None:
            return True
        if entities.constraints:
            if field_name in entities.constraints and entities.constraints[field_name] is not None:
                return True
        ctx_state = context.shopping_state
        ctx_constraints = context.metadata.get("constraints", {})
        if field_name == "budget" and ctx_constraints.get("budget"):
            return True
        if field_name == "size" and ctx_constraints.get("size"):
            return True
        if field_name == "color" and ctx_constraints.get("color"):
            return True
        if field_name == "brand" and ctx_constraints.get("brand"):
            return True
        if field_name == "category" and (
            ctx_state.last_search_category or ctx_constraints.get("category")
        ):
            return True
        if field_name == "order_number" and user_message:
            email = self._extract_email_from_text(user_message)
            if email:
                return True
        return False

    @staticmethod
    def _extract_email_from_text(text: str) -> str | None:
        import re

        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        return match.group(0) if match else None

    def _resolve_personality(self, personality: str | None) -> PersonalityType:
        personality_lower = personality.lower() if personality else "friendly"
        for pt in PersonalityType:
            if pt.value == personality_lower:
                return pt
        return PersonalityType.FRIENDLY

    def _build_context_prefix(self, context: ConversationContext, mode: str) -> str:
        parts: list[str] = []
        constraints = context.metadata.get("constraints", {})
        if constraints.get("budget"):
            parts.append(f"You mentioned a budget under ${constraints['budget']}, so")
        if constraints.get("brand"):
            parts.append(f"You mentioned {constraints['brand']}, so")
        if constraints.get("color"):
            parts.append(f"You mentioned {constraints['color']}, so")
        if constraints.get("size"):
            parts.append(f"You mentioned size {constraints['size']}, so")
        if parts:
            return " ".join(parts)
        return ""

    def _combine_related_fields(self, fields: list[MissingField]) -> list[str]:
        groups: list[str] = []
        constraint_fields = {"budget", "size", "color", "brand"}
        constraint_group = [f for f in fields if f.field_name in constraint_fields]
        other_fields = [f for f in fields if f.field_name not in constraint_fields]
        if constraint_group:
            examples = " or ".join(
                f"{f.display_name} ({', '.join(f.example_values[:2])})" for f in constraint_group
            )
            groups.append(f"Could you tell me: {examples}?")
        for f in other_fields:
            examples_str = ""
            if f.example_values:
                examples_str = f" (e.g., {', '.join(f.example_values[:2])})"
            groups.append(f"What {f.display_name} are you looking for?{examples_str}")
        return groups if groups else ["Could you tell me more?"]

    def _format_field_group(self, fields: list[MissingField]) -> str:
        names = [f.display_name for f in fields]
        if len(names) == 1:
            examples = fields[0].example_values[:2] if fields[0].example_values else []
            if examples:
                return f"Could you tell me the {names[0]}? (e.g., {', '.join(examples)})"
            return f"Could you tell me the {names[0]}?"
        return f"Could you share: {' and '.join(names)}?"

    def _extract_field_value(self, field_name: str, response: str) -> Any | None:
        if field_name == "order_number":
            match = _ORDER_NUMBER_PATTERN.search(response)
            return match.group(0) if match else None
        if field_name == "budget":
            match = _BUDGET_PATTERN.search(response)
            if match:
                val = match.group(1) or match.group(2)
                return float(val.replace("$", "").replace("usd", "").strip())
            return None
        if field_name == "size":
            match = _SIZE_PATTERN.search(response)
            return match.group(0).strip() if match else None
        if field_name == "color":
            match = _COLOR_PATTERN.search(response)
            return match.group(0).lower() if match else None
        if field_name in ("product_identifier", "product_identifiers"):
            stripped = response.strip()
            if len(stripped) <= 150 and stripped:
                return stripped
            return None
        if field_name == "brand":
            response_lower = response.lower()
            for brand in _BRAND_KNOWN:
                if brand in response_lower:
                    return brand.title()
            words = response.split()
            if len(words) <= 3:
                return words[0].strip(".,!?").title()
        return None
