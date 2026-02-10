"""Story 1-11: End-to-end integration tests for Business Info & FAQ Configuration.

Tests the complete flow for:
- Business info CRUD operations
- FAQ CRUD operations (create, read, update, delete, reorder)
- Authentication requirements
- Database persistence

Validates the acceptance criteria from Epic 1, Story 1.11.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_business_info_full_crud_flow(async_client, db_session: AsyncSession) -> None:
    """Test complete CRUD flow for business information.

    Acceptance Criteria: "Merchants can configure business information
    including business name, description, and hours"
    """
    # Create a merchant
    merchant = Merchant(
        merchant_key="test_merchant_1_11",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # 1. GET initial business info (should be empty/null)
    response = await async_client.get(
        "/api/v1/merchant/business-info",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "requestId" in data["meta"]

    # 2. PUT - Create business info
    update_data = {
        "business_name": "Test Athletic Gear",
        "business_description": "Premium athletic apparel and equipment",
        "business_hours": "9 AM - 6 PM PST, Mon-Sat",
    }
    response = await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers,
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["businessName"] == "Test Athletic Gear"
    assert data["businessDescription"] == "Premium athletic apparel and equipment"
    assert data["businessHours"] == "9 AM - 6 PM PST, Mon-Sat"

    # 3. GET - Verify business info was persisted
    response = await async_client.get(
        "/api/v1/merchant/business-info",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["businessName"] == "Test Athletic Gear"

    # 4. PUT - Partial update
    partial_update = {
        "business_hours": "8 AM - 8 PM PST, Daily",
    }
    response = await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers,
        json=partial_update,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["businessName"] == "Test Athletic Gear"  # Unchanged
    assert data["businessHours"] == "8 AM - 8 PM PST, Daily"


@pytest.mark.asyncio
async def test_business_info_validation_max_lengths(async_client, db_session: AsyncSession) -> None:
    """Test business info validation for max field lengths.

    Acceptance Criteria: "Business name max 100 chars, description max 500 chars"
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_valid",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # Test business name max length (100)
    response = await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers,
        json={
            "business_name": "A" * 101,  # Exceeds max
        },
    )
    assert response.status_code == 422  # Validation error

    # Test description max length (500)
    response = await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers,
        json={
            "business_name": "Valid Name",
            "business_description": "A" * 501,  # Exceeds max
        },
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_faq_full_crud_flow(async_client, db_session: AsyncSession) -> None:
    """Test complete CRUD flow for FAQ items.

    Acceptance Criteria: "Merchants can manage FAQ items with
    create, read, update, delete operations"
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_faq",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # 1. CREATE - Add multiple FAQ items
    faq_ids = []
    questions = [
        "What are your shipping options?",
        "Do you accept returns?",
        "What payment methods do you accept?",
    ]
    answers = [
        "We offer free shipping on orders over $50.",
        "Yes, we accept returns within 30 days of purchase.",
        "We accept Visa, MasterCard, and PayPal.",
    ]

    for i, (question, answer) in enumerate(zip(questions, answers)):
        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=headers,
            json={
                "question": question,
                "answer": answer,
                "keywords": f"keyword{i}",
            },
        )
        assert response.status_code == 201
        faq_ids.append(response.json()["data"]["id"])

    # 2. READ - List all FAQs
    response = await async_client.get(
        "/api/v1/merchant/faqs",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    # Verify order_index is sequential
    assert data[0]["orderIndex"] == 0
    assert data[1]["orderIndex"] == 1
    assert data[2]["orderIndex"] == 2

    # 3. UPDATE - Modify an FAQ
    response = await async_client.put(
        f"/api/v1/merchant/faqs/{faq_ids[0]}",
        headers=headers,
        json={
            "answer": "Updated shipping information: 2-3 day delivery available!",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"] == "Updated shipping information: 2-3 day delivery available!"
    assert data["question"] == questions[0]  # Unchanged

    # 4. REORDER - Change FAQ order
    response = await async_client.put(
        "/api/v1/merchant/faqs/reorder",
        headers=headers,
        json={
            "faq_ids": [faq_ids[2], faq_ids[0], faq_ids[1]],  # Reverse order
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data[0]["id"] == faq_ids[2]
    assert data[1]["id"] == faq_ids[0]
    assert data[2]["id"] == faq_ids[1]

    # 5. DELETE - Remove an FAQ
    response = await async_client.delete(
        f"/api/v1/merchant/faqs/{faq_ids[1]}",
        headers=headers,
    )
    assert response.status_code == 204

    # Verify deletion
    response = await async_client.get(
        "/api/v1/merchant/faqs",
        headers=headers,
    )
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["id"] == faq_ids[2]
    assert data[1]["id"] == faq_ids[0]


@pytest.mark.asyncio
async def test_faq_validation_and_constraints(async_client, db_session: AsyncSession) -> None:
    """Test FAQ validation for required fields and max lengths.

    Acceptance Criteria: "Question max 200 chars, Answer max 1000 chars,
    Keywords max 500 chars. Question and Answer are required."
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_faq_val",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # Test missing required fields
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "answer": "Only answer provided",
        },
    )
    assert response.status_code == 422  # Validation error

    # Test question max length (200)
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "question": "Q" * 201,  # Exceeds max
            "answer": "Valid answer",
        },
    )
    assert response.status_code == 422

    # Test answer max length (1000)
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "question": "Valid question?",
            "answer": "A" * 1001,  # Exceeds max
        },
    )
    assert response.status_code == 422

    # Test keywords max length (500) - should be valid at exactly 500
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "question": "Valid question?",
            "answer": "Valid answer",
            "keywords": "K" * 500,
        },
    )
    assert response.status_code == 201  # Should succeed


@pytest.mark.asyncio
async def test_faq_reorder_shifts_other_faqs(async_client, db_session: AsyncSession) -> None:
    """Test that reordering FAQs properly shifts order_index of other FAQs.

    Acceptance Criteria: "Reordering FAQs updates order_index for all affected items"
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_reorder",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # Create 5 FAQs
    faq_ids = []
    for i in range(5):
        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=headers,
            json={
                "question": f"Question {i}?",
                "answer": f"Answer {i}",
            },
        )
        faq_ids.append(response.json()["data"]["id"])

    # Move last FAQ to first position
    response = await async_client.put(
        "/api/v1/merchant/faqs/reorder",
        headers=headers,
        json={
            "faq_ids": [faq_ids[4], faq_ids[0], faq_ids[1], faq_ids[2], faq_ids[3]],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Verify order
    for i, faq_data in enumerate(data):
        assert faq_data["orderIndex"] == i
        assert faq_data["id"] == [faq_ids[4], faq_ids[0], faq_ids[1], faq_ids[2], faq_ids[3]][i]


@pytest.mark.asyncio
async def test_merchant_isolation(async_client, db_session: AsyncSession) -> None:
    """Test that merchants cannot access each other's business info and FAQs.

    Acceptance Criteria: "Each merchant can only access their own data"
    """
    # Create two merchants
    merchant1 = Merchant(
        merchant_key="test_merchant_1_11_isolation_1",
        platform="shopify",
        status="active",
    )
    merchant2 = Merchant(
        merchant_key="test_merchant_1_11_isolation_2",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant1)
    db_session.add(merchant2)
    await db_session.commit()
    merchant1_id = merchant1.id
    merchant2_id = merchant2.id

    headers1 = {"X-Merchant-Id": str(merchant1_id)}
    headers2 = {"X-Merchant-Id": str(merchant2_id)}

    # Merchant 1 creates business info and FAQs
    await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers1,
        json={
            "business_name": "Merchant 1 Store",
        },
    )
    faq_response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers1,
        json={
            "question": "Merchant 1 FAQ?",
            "answer": "Merchant 1 Answer",
        },
    )
    faq1_id = faq_response.json()["data"]["id"]

    # Merchant 2 should not see Merchant 1's data
    response = await async_client.get(
        "/api/v1/merchant/business-info",
        headers=headers2,
    )
    data = response.json()["data"]
    assert data.get("businessName") != "Merchant 1 Store"

    response = await async_client.get(
        "/api/v1/merchant/faqs",
        headers=headers2,
    )
    data = response.json()["data"]
    assert len(data) == 0  # Merchant 2 has no FAQs

    # Merchant 2 should not be able to update/delete Merchant 1's FAQ
    response = await async_client.put(
        f"/api/v1/merchant/faqs/{faq1_id}",
        headers=headers2,
        json={
            "answer": "Should not work",
        },
    )
    assert response.status_code == 403  # Forbidden (access denied)

    response = await async_client.delete(
        f"/api/v1/merchant/faqs/{faq1_id}",
        headers=headers2,
    )
    assert response.status_code == 403  # Forbidden (access denied)


@pytest.mark.asyncio
async def test_faq_keywords_optional(async_client, db_session: AsyncSession) -> None:
    """Test that keywords field is optional for FAQs.

    Acceptance Criteria: "Keywords are optional - helps with FAQ matching"
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_keywords",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # Create FAQ without keywords
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "question": "Do you have a physical store?",
            "answer": "We are online-only.",
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["keywords"] is None


@pytest.mark.asyncio
async def test_api_response_format(async_client, db_session: AsyncSession) -> None:
    """Test that all API responses follow MinimalEnvelope format.

    Acceptance Criteria: "All responses use MinimalEnvelope format
    with data and meta fields"
    """
    merchant = Merchant(
        merchant_key="test_merchant_1_11_envelope",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    headers = {"X-Merchant-Id": str(merchant_id)}

    # Test GET business-info response format
    response = await async_client.get(
        "/api/v1/merchant/business-info",
        headers=headers,
    )
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "requestId" in data["meta"]
    assert "timestamp" in data["meta"]

    # Test PUT business-info response format
    response = await async_client.put(
        "/api/v1/merchant/business-info",
        headers=headers,
        json={"business_name": "Test"},
    )
    data = response.json()
    assert "data" in data
    assert "meta" in data

    # Test GET faqs response format
    response = await async_client.get(
        "/api/v1/merchant/faqs",
        headers=headers,
    )
    data = response.json()
    assert "data" in data
    assert "meta" in data

    # Test POST faqs response format
    response = await async_client.post(
        "/api/v1/merchant/faqs",
        headers=headers,
        json={
            "question": "Test?",
            "answer": "Test",
        },
    )
    data = response.json()
    assert "data" in data
    assert "meta" in data


# Note: async_client fixture is provided by tests/conftest.py
# Note: db_session (alias for async_session) fixture is provided by tests/conftest.py
