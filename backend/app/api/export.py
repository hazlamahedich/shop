"""Export API endpoint for conversation CSV export.

Provides POST /api/conversations/export endpoint with authentication,
filter support, and streaming CSV response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.schemas.export import ConversationExportRequest
from app.services.export.csv_export_service import CSVExportService


router = APIRouter(prefix="/api/conversations", tags=["export"])


@router.post("/export")
async def export_conversations(
    filters: ConversationExportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    merchant_id: int = Header(..., alias="X-Merchant-ID"),
) -> StreamingResponse:
    """Export conversations to CSV format.

    Generates a CSV file with all conversations matching the specified filters.
    The CSV is formatted for Excel compatibility with UTF-8 BOM and CRLF line endings.

    Args:
        filters: Export filter parameters (date range, search, status, etc.)
        db: Database session
        merchant_id: Merchant ID from X-Merchant-ID header (authenticated)

    Returns:
        Streaming CSV response with proper headers for file download

    Raises:
        APIError: If export exceeds limit (10,000 conversations)
        APIError: If merchant authentication fails

    Example:
        POST /api/conversations/export
        X-Merchant-ID: 123
        {
            "dateFrom": "2026-02-01",
            "dateTo": "2026-02-28",
            "status": ["active"]
        }
    """
    # Verify merchant_id is valid
    if not merchant_id or merchant_id <= 0:
        raise APIError(
            ErrorCode.UNAUTHORIZED,
            "Invalid merchant ID",
        )

    # Create export service
    export_service = CSVExportService()

    # Generate CSV content
    csv_content, export_count = await export_service.generate_conversations_csv(
        db=db,
        merchant_id=merchant_id,
        date_from=filters.date_from,
        date_to=filters.date_to,
        search=filters.search,
        status=filters.status,
        sentiment=filters.sentiment,
        has_handoff=filters.has_handoff,
    )

    # Generate filename with date
    export_date = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"conversations-{export_date}.csv"

    # Create streaming response
    def generate():
        """Generator function for streaming CSV content."""
        yield csv_content

    return StreamingResponse(
        generate(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "X-Export-Count": str(export_count),
            "X-Export-Date": datetime.utcnow().isoformat() + "Z",
        },
    )
