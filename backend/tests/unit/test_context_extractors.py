import pytest

from app.services.context.base import BaseContextExtractor
from app.services.context.ecommerce_extractor import EcommerceContextExtractor
from app.services.context.general_extractor import GeneralContextExtractor


class ConcreteExtractor(BaseContextExtractor):
    async def extract(self, message: str, context: dict) -> dict:
        return {}


# ─── EcommerceContextExtractor ────────────────────────────────────────────────


class TestEcommerceExtractProductIds:
    @pytest.mark.asyncio
    async def test_extract_product_ids_hash_format(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "I'm interested in #123"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["viewed_products"] == [123]

    @pytest.mark.asyncio
    async def test_extract_product_ids_product_prefix_format(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Tell me about product-456"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["viewed_products"] == [456]

    @pytest.mark.asyncio
    async def test_extract_multiple_product_ids(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Compare #123 and product-456 with #789"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["viewed_products"] == [123, 456, 789]


class TestEcommerceExtractPriceConstraints:
    @pytest.mark.asyncio
    async def test_extract_budget_max_under(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "I need something under $100"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["budget_max"] == 100.0

    @pytest.mark.asyncio
    async def test_extract_budget_min_over(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "I want quality stuff, over $50"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["budget_min"] == 50.0

    @pytest.mark.asyncio
    async def test_extract_price_range_around(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Looking for something around $100"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["budget_min"] == 80.0
        assert result["constraints"]["budget_max"] == 120.0

    @pytest.mark.asyncio
    async def test_extract_budget_min_and_max_both(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "I need something over $50 and under $200"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["budget_min"] == 50.0
        assert result["constraints"]["budget_max"] == 200.0


class TestEcommerceExtractPreferences:
    @pytest.mark.asyncio
    async def test_extract_size_and_color(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "I want size M in red"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["size"] == "M"
        assert result["constraints"]["color"] == "red"

    @pytest.mark.asyncio
    async def test_extract_brand(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Looking for nike shoes"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["constraints"]["brand"] == "Nike"


class TestEcommerceExtractCart:
    @pytest.mark.asyncio
    async def test_extract_cart_mentions(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Add #123 to my cart"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["cart_items"] == [123]


class TestEcommerceMisc:
    @pytest.mark.asyncio
    async def test_no_extraction_for_irrelevant_message(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Hello, how are you?"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert "viewed_products" not in result
        assert "constraints" not in result
        assert "cart_items" not in result
        assert result["search_history"] == [message]
        assert result["turn_count"] == 1

    @pytest.mark.asyncio
    async def test_always_includes_search_history_and_turn_count(self):
        # Given
        extractor = EcommerceContextExtractor()
        message = "Show me #999"

        # When
        result = await extractor.extract(message, {"turn_count": 3})

        # Then
        assert result["search_history"] == [message]
        assert result["turn_count"] == 4


# ─── GeneralContextExtractor ──────────────────────────────────────────────────


class TestGeneralExtractTopics:
    @pytest.mark.asyncio
    async def test_extract_topic_login(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I can't login to my account"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert "login" in result["topics_discussed"]

    @pytest.mark.asyncio
    async def test_extract_multiple_topics(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I have a billing issue with my order and need a refund"

        # When
        result = await extractor.extract(message, {})

        # Then
        topics = result["topics_discussed"]
        assert "billing" in topics
        assert "order" in topics
        assert "refund" in topics


class TestGeneralSupportIssues:
    @pytest.mark.asyncio
    async def test_no_duplicate_support_issues_for_same_type(self):
        # Given
        extractor = GeneralContextExtractor()
        existing = {"support_issues": [{"type": "billing", "status": "pending", "message": "old"}]}
        message = "I have another billing problem"

        # When
        result = await extractor.extract(message, existing)

        # Then
        assert "support_issues" not in result


class TestGeneralEscalation:
    @pytest.mark.asyncio
    async def test_detect_high_escalation(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I want to speak to a human right now!"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["escalation_status"] == "high"

    @pytest.mark.asyncio
    async def test_detect_medium_escalation(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I'm very frustrated with this service"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["escalation_status"] == "medium"

    @pytest.mark.asyncio
    async def test_detect_low_escalation(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I'm confused about how this works"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["escalation_status"] == "low"


class TestGeneralDocumentReferences:
    @pytest.mark.asyncio
    async def test_extract_document_references_kb(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "I read kb-123 and it didn't help"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert 123 in result["documents_referenced"]

    @pytest.mark.asyncio
    async def test_extract_document_references_all_patterns(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "Check kb-123, article-456, doc-789, and faq-100"

        # When
        result = await extractor.extract(message, {})

        # Then
        assert result["documents_referenced"] == [123, 456, 789, 100]


class TestGeneralMisc:
    @pytest.mark.asyncio
    async def test_always_increments_turn_count(self):
        # Given
        extractor = GeneralContextExtractor()
        message = "Hello"

        # When
        result = await extractor.extract(message, {"turn_count": 5})

        # Then
        assert result["turn_count"] == 6


# ─── BaseContextExtractor._merge_context ──────────────────────────────────────


class TestMergeContext:
    def test_merge_dict_values_recursively(self):
        # Given
        extractor = ConcreteExtractor()
        base = {"user": {"name": "Alice", "age": 30}}
        updates = {"user": {"age": 31, "email": "alice@example.com"}}

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert result["user"] == {"name": "Alice", "age": 31, "email": "alice@example.com"}

    def test_merge_list_values_no_duplicates(self):
        # Given
        extractor = ConcreteExtractor()
        base = {"tags": ["a", "b", "c"]}
        updates = {"tags": ["c", "d"]}

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert result["tags"] == ["a", "b", "c", "d"]

    def test_merge_list_of_dicts_deduplicate_by_type(self):
        # Given
        extractor = ConcreteExtractor()
        base = {"issues": [{"type": "billing", "status": "pending"}]}
        updates = {
            "issues": [
                {"type": "billing", "status": "resolved"},
                {"type": "login", "status": "pending"},
            ]
        }

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert len(result["issues"]) == 2
        assert result["issues"][0] == {"type": "billing", "status": "pending"}
        assert result["issues"][1] == {"type": "login", "status": "pending"}

    def test_override_non_dict_non_list_values(self):
        # Given
        extractor = ConcreteExtractor()
        base = {"count": 5, "name": "old"}
        updates = {"count": 10, "name": "new"}

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert result["count"] == 10
        assert result["name"] == "new"

    def test_merge_with_empty_base(self):
        # Given
        extractor = ConcreteExtractor()
        base = {}
        updates = {"tags": ["a"], "count": 1, "meta": {"key": "val"}}

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert result == {"tags": ["a"], "count": 1, "meta": {"key": "val"}}

    def test_merge_returns_new_dict(self):
        # Given
        extractor = ConcreteExtractor()
        base = {"items": [1, 2], "nested": {"a": 1}}
        updates = {"items": [3], "nested": {"b": 2}}

        # When
        result = extractor._merge_context(base, updates)

        # Then
        assert result is not base
        assert result["items"] == [1, 2, 3]
        assert result["nested"] == {"a": 1, "b": 2}
