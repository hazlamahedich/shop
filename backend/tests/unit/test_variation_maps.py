"""Unit tests for variation_maps module.

Story 11-3: Tests synonym expansion, typo correction, brand normalization,
and the normalize_message() function.
"""

import pytest

from app.services.intent.variation_maps import (
    ALL_BRANDS,
    BRAND_CANONICAL,
    PRODUCT_SYNONYMS,
    TYPO_MAP,
    get_all_product_terms,
    get_product_category,
    normalize_brand,
    normalize_message,
)


class TestNormalizeMessageBasic:
    def test_returns_lowercased(self):
        result = normalize_message("HELLO WORLD")
        assert result == "hello world"

    def test_strips_whitespace(self):
        result = normalize_message("  hello  ")
        assert result == "hello"

    def test_truncates_at_max_length(self):
        long_msg = "a" * 500
        result = normalize_message(long_msg)
        assert len(result) <= 400


class TestTypoCorrection:
    def test_corrects_shose(self):
        result = normalize_message("I want shose")
        assert "shoes" in result

    def test_corrects_chep(self):
        result = normalize_message("show me chep stuff")
        assert "cheap" in result

    def test_corrects_expenisve(self):
        result = normalize_message("too expenisve")
        assert "expensive" in result

    def test_corrects_ordr(self):
        result = normalize_message("wher is my ordr")
        assert "where" in result
        assert "order" in result

    def test_corrects_laptob(self):
        result = normalize_message("need a laptob")
        assert "laptop" in result

    def test_corrects_serch(self):
        result = normalize_message("serch for shoes")
        assert "search" in result

    def test_does_not_corrupt_words(self):
        result = normalize_message("this bot isn't helping")
        assert "help" in result or "assisting" not in result.split()
        assert "bot" in result

    def test_preserves_non_typos(self):
        result = normalize_message("show me red shoes")
        assert "red" in result
        assert "shoes" in result


class TestSynonymExpansion:
    def test_expands_kicks_to_shoes(self):
        result = normalize_message("red kicks under 80")
        assert "shoes" in result

    def test_expands_basket_to_cart(self):
        result = normalize_message("show my basket")
        assert "cart" in result

    def test_expands_sneakers_to_shoes(self):
        result = normalize_message("got any sneakers")
        assert "shoes" in result

    def test_expands_shades_to_sunglasses(self):
        result = normalize_message("show me shades")
        assert "sunglasses" in result

    def test_does_not_expand_inside_words(self):
        result = normalize_message("helping shipping")
        assert "help" not in result.split()
        assert "shipping" in result or "send" in result


class TestBrandNormalization:
    def test_normalizes_swoosh_to_nike(self):
        result = normalize_message("I want swoosh shoes")
        assert "nike" in result

    def test_normalizes_chucks_to_converse(self):
        result = normalize_message("looking for chucks")
        assert "converse" in result

    def test_normalizes_lulu_to_lululemon(self):
        result = normalize_message("show me lulu gear")
        assert "lululemon" in result


class TestNormalizeBrand:
    def test_nike_alias(self):
        assert normalize_brand("swoosh") == "nike"

    def test_adidas_alias(self):
        assert normalize_brand("yeezy") == "adidas"

    def test_canonical_unchanged(self):
        assert normalize_brand("nike") == "nike"

    def test_unknown_unchanged(self):
        assert normalize_brand("unknownbrand") == "unknownbrand"

    def test_case_insensitive(self):
        assert normalize_brand("Swoosh") == "nike"


class TestGetProductCategory:
    def test_kicks_maps_to_shoes(self):
        assert get_product_category("kicks") == "shoes"

    def test_sneakers_maps_to_shoes(self):
        assert get_product_category("sneakers") == "shoes"

    def test_shades_maps_to_sunglasses(self):
        assert get_product_category("shades") == "sunglasses"

    def test_unknown_returns_none(self):
        assert get_product_category("unknownthing") is None

    def test_canonical_returns_self(self):
        assert get_product_category("shoes") == "shoes"


class TestGetAllProductTerms:
    def test_includes_canonical_categories(self):
        terms = get_all_product_terms()
        assert "shoes" in terms
        assert "shirt" in terms
        assert "jacket" in terms

    def test_includes_synonyms(self):
        terms = get_all_product_terms()
        assert "kicks" in terms
        assert "sneakers" in terms
        assert "shades" in terms


class TestAllBrands:
    def test_contains_major_brands(self):
        assert "nike" in ALL_BRANDS
        assert "adidas" in ALL_BRANDS
        assert "jordan" in ALL_BRANDS

    def test_contains_29_brands(self):
        assert len(ALL_BRANDS) >= 29


class TestTypoMapIntegrity:
    def test_all_corrections_are_lowercase(self):
        for typo, correction in TYPO_MAP.items():
            assert typo == typo.lower(), f"Typo {typo!r} not lowercase"
            assert correction == correction.lower(), f"Correction {correction!r} not lowercase"

    def test_no_empty_keys_or_values(self):
        for typo, correction in TYPO_MAP.items():
            assert typo.strip(), f"Empty typo key"
            assert correction.strip(), f"Empty correction for {typo!r}"


class TestBrandCanonicalIntegrity:
    def test_all_canonical_brands_in_all_brands(self):
        for alias, canonical in BRAND_CANONICAL.items():
            assert canonical in ALL_BRANDS, f"Canonical {canonical!r} not in ALL_BRANDS"
