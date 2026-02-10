"""Tests for FAQ ORM model.

Story 1.11: Business Info & FAQ Configuration

Tests model validation, relationships, and CRUD operations.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import Faq
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_faq_creation(db_session: AsyncSession) -> None:
    """Test creating an FAQ item with all fields (Story 1.11 AC 3)."""

    # Create a merchant first
    merchant = Merchant(
        merchant_key="test-merchant-for-faq",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create FAQ
    faq = Faq(
        merchant_id=merchant.id,
        question="What are your shipping options?",
        answer="We offer free shipping on orders over $50. Standard shipping takes 3-5 business days.",
        keywords="shipping, delivery, how long",
        order_index=1,
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert faq.id is not None
    assert faq.merchant_id == merchant.id
    assert faq.question == "What are your shipping options?"
    assert faq.answer == "We offer free shipping on orders over $50. Standard shipping takes 3-5 business days."
    assert faq.keywords == "shipping, delivery, how long"
    assert faq.order_index == 1


@pytest.mark.asyncio
async def test_faq_with_minimal_fields(db_session: AsyncSession) -> None:
    """Test creating an FAQ with only required fields (Story 1.11 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-minimal-faq",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    faq = Faq(
        merchant_id=merchant.id,
        question="Do you accept returns?",
        answer="Yes! Returns accepted within 30 days of purchase.",
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert faq.question == "Do you accept returns?"
    assert faq.answer == "Yes! Returns accepted within 30 days of purchase."
    assert faq.keywords is None
    assert faq.order_index == 0  # Default value


@pytest.mark.asyncio
async def test_faq_question_max_length(db_session: AsyncSession) -> None:
    """Test that question respects 200 character limit (Story 1.11 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-question-max",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create a question with exactly 200 characters
    long_question = "Q" * 200

    faq = Faq(
        merchant_id=merchant.id,
        question=long_question,
        answer="Test answer",
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert len(faq.question) == 200


@pytest.mark.asyncio
async def test_faq_answer_max_length(db_session: AsyncSession) -> None:
    """Test that answer respects 1000 character limit (Story 1.11 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-answer-max",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create an answer with exactly 1000 characters
    long_answer = "A" * 1000

    faq = Faq(
        merchant_id=merchant.id,
        question="Test question?",
        answer=long_answer,
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert len(faq.answer) == 1000


@pytest.mark.asyncio
async def test_faq_keywords_max_length(db_session: AsyncSession) -> None:
    """Test that keywords respects 500 character limit (Story 1.11 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-keywords-max",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create keywords with exactly 500 characters
    long_keywords = "k" * 500

    faq = Faq(
        merchant_id=merchant.id,
        question="Test question?",
        answer="Test answer",
        keywords=long_keywords,
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert len(faq.keywords) == 500


@pytest.mark.asyncio
async def test_faq_update(db_session: AsyncSession) -> None:
    """Test updating an FAQ item (Story 1.11 AC 4)."""

    merchant = Merchant(
        merchant_key="test-merchant-update-faq",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    faq = Faq(
        merchant_id=merchant.id,
        question="Original question?",
        answer="Original answer",
        keywords="original",
        order_index=1,
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    original_updated_at = faq.updated_at

    # Update FAQ
    faq.question = "Updated question?"
    faq.answer = "Updated answer with more details"
    faq.keywords = "updated, new"
    faq.order_index = 2
    await db_session.commit()
    await db_session.refresh(faq)

    assert faq.question == "Updated question?"
    assert faq.answer == "Updated answer with more details"
    assert faq.keywords == "updated, new"
    assert faq.order_index == 2
    assert faq.updated_at > original_updated_at


@pytest.mark.asyncio
async def test_faq_merchant_relationship(db_session: AsyncSession) -> None:
    """Test the FAQ-Merchant relationship (Story 1.11 AC 7)."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-relationship",
        platform="fly.io",
        status="active",
        business_name="Test Store",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    faq = Faq(
        merchant_id=merchant.id,
        question="Where are you located?",
        answer="We're online-only.",
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    # Test relationship from FAQ to Merchant
    assert faq.merchant.id == merchant.id
    assert faq.merchant.business_name == "Test Store"


@pytest.mark.asyncio
async def test_merchant_faq_relationship(db_session: AsyncSession) -> None:
    """Test the Merchant-FAQ relationship (Story 1.11 AC 7)."""

    merchant = Merchant(
        merchant_key="test-merchant-multiple-faqs-relationship",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create multiple FAQs for the merchant with distinct questions
    faqs = [
        Faq(
            merchant_id=merchant.id,
            question=f"Relationship Test Question {i}?",
            answer=f"Relationship Test Answer {i}",
            order_index=i,
        )
        for i in range(3)
    ]

    for faq in faqs:
        db_session.add(faq)
    await db_session.commit()

    # Query merchant with FAQs explicitly loaded using selectinload
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(
        select(Merchant)
        .options(selectinload(Merchant.faqs))
        .where(Merchant.merchant_key == "test-merchant-multiple-faqs-relationship")
    )
    merchant_with_faqs = result.scalars().first()

    # Test relationship from Merchant to FAQs
    assert merchant_with_faqs is not None

    # Filter to only the FAQs we created in this test (by prefix)
    our_faqs = [faq for faq in merchant_with_faqs.faqs if "Relationship Test" in faq.question]
    assert len(our_faqs) == 3

    # Verify these are the FAQs we just created (by question content)
    questions = [faq.question for faq in our_faqs]
    assert "Relationship Test Question 0?" in questions
    assert "Relationship Test Question 1?" in questions
    assert "Relationship Test Question 2?" in questions

    # FAQs should be ordered by order_index
    assert [faq.order_index for faq in our_faqs] == [0, 1, 2]


@pytest.mark.asyncio
async def test_faq_query_by_merchant(db_session: AsyncSession) -> None:
    """Test querying FAQs by merchant_id (Story 1.11 AC 7)."""

    # Create two merchants with unique keys
    merchant1 = Merchant(
        merchant_key="test-merchant-faq-query-by-merchant-1",
        platform="fly.io",
        status="active",
    )
    merchant2 = Merchant(
        merchant_key="test-merchant-faq-query-by-merchant-2",
        platform="fly.io",
        status="active",
    )
    db_session.add_all([merchant1, merchant2])
    await db_session.commit()

    # Create FAQs for merchant1
    for i in range(3):
        faq = Faq(
            merchant_id=merchant1.id,
            question=f"QueryTest1 Question {i}?",
            answer=f"QueryTest1 Answer {i}",
            order_index=i,
        )
        db_session.add(faq)

    # Create FAQs for merchant2
    for i in range(2):
        faq = Faq(
            merchant_id=merchant2.id,
            question=f"QueryTest2 Question {i}?",
            answer=f"QueryTest2 Answer {i}",
            order_index=i,
        )
        db_session.add(faq)

    await db_session.commit()

    # Query FAQs for merchant1
    result = await db_session.execute(
        select(Faq)
        .join(Merchant)
        .where(Merchant.merchant_key == "test-merchant-faq-query-by-merchant-1")
        .order_by(Faq.order_index)
    )
    all_merchant1_faqs = result.scalars().all()

    # Filter to only the FAQs we created in this test (by prefix)
    our_faqs = [faq for faq in all_merchant1_faqs if "QueryTest1" in faq.question]

    assert len(our_faqs) == 3
    # Verify these are the FAQs we created for merchant1
    assert all("QueryTest1" in faq.question for faq in our_faqs)


@pytest.mark.asyncio
async def test_faq_delete_cascade(db_session: AsyncSession) -> None:
    """Test that deleting a merchant cascades to their FAQs (Story 1.11 AC 7)."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-cascade",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create FAQs for the merchant
    faq = Faq(
        merchant_id=merchant.id,
        question="Test question?",
        answer="Test answer",
    )
    db_session.add(faq)
    await db_session.commit()

    faq_id = faq.id

    # Delete the merchant
    await db_session.delete(merchant)
    await db_session.commit()

    # Verify FAQ is also deleted (cascade)
    result = await db_session.execute(select(Faq).where(Faq.id == faq_id))
    deleted_faq = result.scalars().first()

    assert deleted_faq is None


@pytest.mark.asyncio
async def test_faq_repr(db_session: AsyncSession) -> None:
    """Test that FAQ repr includes key information."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-repr",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    faq = Faq(
        merchant_id=merchant.id,
        question="What are your hours?",
        answer="9 AM - 6 PM PST",
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    repr_str = repr(faq)
    assert str(faq.id) in repr_str
    assert "What are your hours" in repr_str
    assert str(merchant.id) in repr_str


@pytest.mark.asyncio
async def test_faq_created_at_timestamp(db_session: AsyncSession) -> None:
    """Test that FAQ has created_at timestamp set automatically."""

    merchant = Merchant(
        merchant_key="test-merchant-faq-timestamps",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    before_create = datetime.now(timezone.utc)

    faq = Faq(
        merchant_id=merchant.id,
        question="Timestamp test?",
        answer="Timestamp answer",
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)

    assert faq.created_at is not None
    assert faq.created_at >= before_create
    assert faq.created_at <= datetime.now(timezone.utc)
