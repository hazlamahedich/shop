"""FAQ Management API endpoints.

Story 1.11: Business Info & FAQ Configuration

Provides endpoints for:
- Listing all FAQs for a merchant
- Creating new FAQ items
- Updating existing FAQ items
- Deleting FAQ items
- Reordering FAQ items
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.faq import Faq
from app.schemas.faq import (
    FaqRequest,
    FaqUpdateRequest,
    FaqResponse,
    FaqListEnvelope,
    FaqEnvelope,
    FaqReorderRequest,
)
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists


logger = structlog.get_logger(__name__)

router = APIRouter()


def _faq_to_response(faq: Faq) -> FaqResponse:
    """Convert FAQ model to FAQ response.

    Args:
        faq: FAQ ORM model

    Returns:
        FaqResponse object
    """
    return FaqResponse(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        keywords=faq.keywords,
        order_index=faq.order_index,
        created_at=faq.created_at,
        updated_at=faq.updated_at,
    )


@router.get(
    "/faqs",
    response_model=FaqListEnvelope,
)
async def list_faqs(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FaqListEnvelope:
    """
    List all FAQ items for the authenticated merchant.

    Returns FAQs ordered by their order_index field.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        FaqListEnvelope with list of FAQ items

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)

    # Verify merchant exists
    await verify_merchant_exists(merchant_id, db)

    # Get FAQs ordered by order_index
    result = await db.execute(
        select(Faq)
        .where(Faq.merchant_id == merchant_id)
        .order_by(Faq.order_index, Faq.id)
    )
    faqs = result.scalars().all()

    logger.info(
        "faqs_listed",
        merchant_id=merchant_id,
        faq_count=len(faqs),
    )

    return FaqListEnvelope(
        data=[_faq_to_response(faq) for faq in faqs],
        meta=create_meta(),
    )


@router.post(
    "/faqs",
    response_model=FaqEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_faq(
    request: Request,
    faq_data: FaqRequest,
    db: AsyncSession = Depends(get_db),
) -> FaqEnvelope:
    """
    Create a new FAQ item.

    Creates a new FAQ for the authenticated merchant.
    The FAQ will be added at the end of the list.

    Args:
        request: FastAPI request with merchant authentication
        faq_data: FAQ creation data
        db: Database session

    Returns:
        FaqEnvelope with created FAQ

    Raises:
        APIError: If authentication fails or merchant not found
    """
    try:
        merchant_id = get_merchant_id(request)

        # Verify merchant exists
        await verify_merchant_exists(merchant_id, db)

        # Get the highest order_index for this merchant
        result = await db.execute(
            select(Faq.order_index)
            .where(Faq.merchant_id == merchant_id)
            .order_by(Faq.order_index.desc())
            .limit(1)
        )
        max_order = result.scalar_one_or_none()

        # If order_index not provided, append to end
        order_index = faq_data.order_index
        if order_index is None:
            order_index = (max_order or -1) + 1
        else:
            # If order_index provided, shift existing FAQs down
            # Update FAQs with order_index >= new FAQ's order_index
            await db.execute(
                update(Faq)
                .where(Faq.merchant_id == merchant_id)
                .where(Faq.order_index >= order_index)
                .values(order_index=Faq.order_index + 1)
            )

        logger.info(
            "creating_faq",
            merchant_id=merchant_id,
            question=faq_data.question[:50] if faq_data.question else None,
            order_index=order_index,
        )

        # Create new FAQ
        faq = Faq(
            merchant_id=merchant_id,
            question=faq_data.question,
            answer=faq_data.answer,
            keywords=faq_data.keywords,
            order_index=order_index,
        )

        db.add(faq)
        await db.commit()
        await db.refresh(faq)

        logger.info(
            "faq_created",
            merchant_id=merchant_id,
            faq_id=faq.id,
        )

        return FaqEnvelope(
            data=_faq_to_response(faq),
            meta=create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "create_faq_failed",
            error=str(e),
            error_type=type(e).__name__,
            merchant_id=getattr(request.state, "merchant_id", None),
        )
        await db.rollback()
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to create FAQ: {str(e)}",
        )


@router.put(
    "/faqs/reorder",
    response_model=FaqListEnvelope,
)
async def reorder_faqs(
    request: Request,
    reorder_data: FaqReorderRequest,
    db: AsyncSession = Depends(get_db),
) -> FaqListEnvelope:
    """
    Reorder FAQ items.

    Allows merchants to specify the exact order of their FAQs
    by providing an ordered list of FAQ IDs.

    Args:
        request: FastAPI request with merchant authentication
        reorder_data: Reorder data with ordered list of FAQ IDs
        db: Database session

    Returns:
        FaqListEnvelope with reordered FAQs

    Raises:
        APIError: If authentication fails, FAQ not found, or access denied
    """
    try:
        merchant_id = get_merchant_id(request)

        # Verify merchant exists
        await verify_merchant_exists(merchant_id, db)

        # Get all FAQs for this merchant
        result = await db.execute(
            select(Faq)
            .where(Faq.merchant_id == merchant_id)
            .options(selectinload(Faq.merchant))
        )
        faqs = result.scalars().all()

        # Create a map of FAQ ID to FAQ object
        faq_map = {faq.id: faq for faq in faqs}

        # Validate all FAQ IDs belong to this merchant
        provided_ids = set(reorder_data.faq_ids)
        merchant_ids = set(faq_map.keys())

        if not provided_ids.issubset(merchant_ids):
            invalid_ids = provided_ids - merchant_ids
            raise APIError(
                ErrorCode.NOT_FOUND,
                f"FAQ IDs {invalid_ids} do not belong to this merchant",
            )

        logger.info(
            "reordering_faqs",
            merchant_id=merchant_id,
            faq_count=len(reorder_data.faq_ids),
        )

        # Update order_index for each FAQ
        for new_index, faq_id in enumerate(reorder_data.faq_ids):
            faq = faq_map[faq_id]
            faq.order_index = new_index

        await db.commit()

        # Refresh all FAQs to get updated data
        for faq in faqs:
            await db.refresh(faq)

        # Return FAQs in new order
        result = await db.execute(
            select(Faq)
            .where(Faq.merchant_id == merchant_id)
            .order_by(Faq.order_index)
        )
        reordered_faqs = result.scalars().all()

        logger.info(
            "faqs_reordered",
            merchant_id=merchant_id,
            faq_count=len(reordered_faqs),
        )

        return FaqListEnvelope(
            data=[_faq_to_response(faq) for faq in reordered_faqs],
            meta=create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "reorder_faqs_failed",
            error=str(e),
            error_type=type(e).__name__,
            merchant_id=merchant_id,
        )
        await db.rollback()
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to reorder FAQs: {str(e)}",
        )


@router.put(
    "/faqs/{faq_id}",
    response_model=FaqEnvelope,
)
async def update_faq(
    request: Request,
    faq_id: int,
    faq_data: FaqUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> FaqEnvelope:
    """
    Update an existing FAQ item.

    Allows merchants to update question, answer, keywords, and order.
    Only the fields that are provided (non-None) will be updated.

    Args:
        request: FastAPI request with merchant authentication
        faq_id: ID of the FAQ to update
        faq_data: FAQ update data
        db: Database session

    Returns:
        FaqEnvelope with updated FAQ

    Raises:
        APIError: If authentication fails, FAQ not found, or access denied
    """
    try:
        merchant_id = get_merchant_id(request)

        # Get FAQ and verify ownership
        result = await db.execute(
            select(Faq).where(Faq.id == faq_id)
        )
        faq = result.scalars().first()

        if not faq:
            raise APIError(
                ErrorCode.NOT_FOUND,
                f"FAQ with ID {faq_id} not found",
            )

        if faq.merchant_id != merchant_id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                "You do not have permission to modify this FAQ",
            )

        logger.info(
            "updating_faq",
            merchant_id=merchant_id,
            faq_id=faq_id,
            has_question=faq_data.question is not None,
            has_answer=faq_data.answer is not None,
            has_keywords=faq_data.keywords is not None,
            has_order_index=faq_data.order_index is not None,
        )

        # Update fields that were provided
        if faq_data.question is not None:
            faq.question = faq_data.question
        if faq_data.answer is not None:
            faq.answer = faq_data.answer
        if faq_data.keywords is not None:
            faq.keywords = faq_data.keywords
        if faq_data.order_index is not None and faq_data.order_index != faq.order_index:
            # Handle reordering
            old_index = faq.order_index
            new_index = faq_data.order_index

            if new_index < old_index:
                # Moving up: shift FAQs in [new_index, old_index) down
                await db.execute(
                    update(Faq)
                    .where(Faq.merchant_id == merchant_id)
                    .where(Faq.id != faq_id)
                    .where(Faq.order_index >= new_index)
                    .where(Faq.order_index < old_index)
                    .values(order_index=Faq.order_index + 1)
                )
            else:
                # Moving down: shift FAQs in (old_index, new_index] up
                await db.execute(
                    update(Faq)
                    .where(Faq.merchant_id == merchant_id)
                    .where(Faq.id != faq_id)
                    .where(Faq.order_index > old_index)
                    .where(Faq.order_index <= new_index)
                    .values(order_index=Faq.order_index - 1)
                )

            faq.order_index = new_index

        await db.commit()
        await db.refresh(faq)

        logger.info(
            "faq_updated",
            merchant_id=merchant_id,
            faq_id=faq_id,
        )

        return FaqEnvelope(
            data=_faq_to_response(faq),
            meta=create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "update_faq_failed",
            error=str(e),
            error_type=type(e).__name__,
            merchant_id=merchant_id,
            faq_id=faq_id,
        )
        await db.rollback()
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update FAQ: {str(e)}",
        )


@router.delete(
    "/faqs/{faq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_faq(
    request: Request,
    faq_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an FAQ item.

    Permanently deletes the specified FAQ. After deletion,
    remaining FAQs will have their order_index values adjusted.

    Args:
        request: FastAPI request with merchant authentication
        faq_id: ID of the FAQ to delete
        db: Database session

    Raises:
        APIError: If authentication fails, FAQ not found, or access denied
    """
    merchant_id = get_merchant_id(request)
    try:
        # Get FAQ and verify ownership
        result = await db.execute(
            select(Faq).where(Faq.id == faq_id)
        )
        faq = result.scalars().first()

        if not faq:
            raise APIError(
                ErrorCode.NOT_FOUND,
                f"FAQ with ID {faq_id} not found",
            )

        if faq.merchant_id != merchant_id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                "You do not have permission to delete this FAQ",
            )

        logger.info(
            "deleting_faq",
            merchant_id=merchant_id,
            faq_id=faq_id,
        )

        # Store the order_index before deletion
        deleted_order_index = faq.order_index

        # Delete the FAQ
        await db.execute(
            delete(Faq).where(Faq.id == faq_id)
        )

        # Shift remaining FAQs down to fill the gap
        await db.execute(
            update(Faq)
            .where(Faq.merchant_id == merchant_id)
            .where(Faq.order_index > deleted_order_index)
            .values(order_index=Faq.order_index - 1)
        )

        await db.commit()

        logger.info(
            "faq_deleted",
            merchant_id=merchant_id,
            faq_id=faq_id,
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "delete_faq_failed",
            error=str(e),
            error_type=type(e).__name__,
            merchant_id=merchant_id,
            faq_id=faq_id,
        )
        await db.rollback()
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to delete FAQ: {str(e)}",
        )
