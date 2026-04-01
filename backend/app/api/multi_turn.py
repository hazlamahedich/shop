"""Multi-turn query handling debug API endpoints.

Story 11-2: Debug API for inspecting and resetting multi-turn conversation state.
These endpoints are for admin/dashboard debugging only — the widget does NOT call these.
"""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.conversation import Conversation
from app.schemas.base import MetaData, MinimalEnvelope

router = APIRouter()
logger = structlog.get_logger(__name__)


class MultiTurnStateData(BaseModel):
    conversation_id: int
    state: str = "IDLE"
    turn_count: int = 0
    accumulated_constraints: dict[str, Any] = Field(default_factory=dict)
    questions_asked: list[str] = Field(default_factory=list)
    pending_questions: list[str] = Field(default_factory=list)
    original_query: str | None = None
    invalid_response_count: int = 0
    mode: str = "ecommerce"

    class Config:
        populate_by_name = True


class MultiTurnResetResponse(BaseModel):
    conversation_id: int
    reset: bool = True
    previous_state: str

    class Config:
        populate_by_name = True


async def _get_merchant_id(request: Request) -> int:
    merchant_id = getattr(request.state, "merchant_id", None)
    if merchant_id is None:
        header_id = request.headers.get("X-Merchant-Id")
        if header_id:
            try:
                merchant_id = int(header_id)
            except ValueError:
                pass
    if merchant_id is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.auth import validate_jwt

                payload = validate_jwt(auth_header[7:])
                merchant_id = payload.merchant_id
            except Exception:
                pass
    if merchant_id is None:
        raise APIError(ErrorCode.AUTH_FAILED, "Merchant ID required")
    return merchant_id


async def _get_conversation(
    db: AsyncSession,
    conversation_id: int,
    merchant_id: int,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            f"Conversation {conversation_id} not found for merchant {merchant_id}",
        )
    return conversation


@router.get(
    "/{conversation_id}/multi-turn-state",
    response_model=MinimalEnvelope,
)
async def get_multi_turn_state(
    conversation_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MinimalEnvelope:
    merchant_id = await _get_merchant_id(request)
    conversation = await _get_conversation(db, conversation_id, merchant_id)

    context_data = {}
    if hasattr(conversation, "context") and conversation.context:
        context_data = conversation.context if isinstance(conversation.context, dict) else {}

    clarification_state = context_data.get("clarification_state", {})
    if isinstance(clarification_state, str):
        clarification_state = {}

    state_data = MultiTurnStateData(
        conversation_id=conversation_id,
        state=clarification_state.get("multi_turn_state", "IDLE"),
        turn_count=clarification_state.get("turn_count", 0),
        accumulated_constraints=clarification_state.get("accumulated_constraints", {}),
        questions_asked=clarification_state.get("questions_asked", []),
        pending_questions=clarification_state.get("pending_questions", []),
        original_query=clarification_state.get("original_query"),
        invalid_response_count=clarification_state.get("invalid_response_count", 0),
        mode=clarification_state.get("mode", "ecommerce"),
    )

    return MinimalEnvelope(
        data=state_data.model_dump(),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
        ),
    )


@router.post(
    "/{conversation_id}/multi-turn-reset",
    response_model=MinimalEnvelope,
)
async def reset_multi_turn_state(
    conversation_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MinimalEnvelope:
    merchant_id = await _get_merchant_id(request)
    conversation = await _get_conversation(db, conversation_id, merchant_id)

    context_data = {}
    if hasattr(conversation, "context") and conversation.context:
        context_data = conversation.context if isinstance(conversation.context, dict) else {}

    clarification_state = context_data.get("clarification_state", {})
    if isinstance(clarification_state, str):
        clarification_state = {}

    previous_state = clarification_state.get("multi_turn_state", "IDLE")

    clarification_state["multi_turn_state"] = "IDLE"
    clarification_state["turn_count"] = 0
    clarification_state["accumulated_constraints"] = {}
    clarification_state["questions_asked"] = []
    clarification_state["pending_questions"] = []
    clarification_state["original_query"] = None
    clarification_state["invalid_response_count"] = 0
    clarification_state["resolved_questions"] = []

    context_data["clarification_state"] = clarification_state
    if hasattr(conversation, "context"):
        conversation.context = context_data
        await db.commit()

    reset_response = MultiTurnResetResponse(
        conversation_id=conversation_id,
        reset=True,
        previous_state=previous_state,
    )

    logger.info(
        "multi_turn_state_reset",
        conversation_id=conversation_id,
        previous_state=previous_state,
    )

    return MinimalEnvelope(
        data=reset_response.model_dump(),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
        ),
    )
