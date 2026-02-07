from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
from app.schemas.conversation import ConversationListResponse
from app.services.conversation import ConversationService

router = APIRouter()
conversation_service = ConversationService()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("updated_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> ConversationListResponse:
    """
    List conversations for the authenticated merchant.

    Returns a paginated list of conversations.
    """
    # 1. Verify Authentication
    # Note: Authentication logic/middleware must populate request.state.merchant_id
    if not hasattr(request.state, "merchant_id") or not request.state.merchant_id:
        # Fallback if middleware fails or is missing (though 401 is usually handled there)
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )

    merchant_id = request.state.merchant_id

    # 2. Validate Params
    valid_sort_columns = ["updated_at", "status", "created_at"]
    if sort_by not in valid_sort_columns:
        raise ValidationError(
            "Invalid sort column",
            fields={"sort_by": f"Must be one of: {', '.join(valid_sort_columns)}"},
        )

    # 3. Call Service
    conversations, total = await conversation_service.get_conversations(
        db=db,
        merchant_id=merchant_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # 4. Construct Response
    total_pages = (total + per_page - 1) // per_page

    return ConversationListResponse(
        data=conversations,
        meta={
            "pagination": {
                "total": total,
                "page": page,
                "perPage": per_page,
                "totalPages": total_pages,
            },
            # request_id handled by middleware usually, but can be added here if needed in body
        },
    )
