"""Mock Shopify API responses for testing.

Provides test doubles for Shopify Storefront API (GraphQL) and Admin API (REST).
"""

from __future__ import annotations


# Mock response for Admin API shop verification
MOCK_SHOP_SUCCESS = {
    "id": 123456789,
    "name": "Test Store",
    "domain": "test-store.myshopify.com",
    "email": "owner@test-store.com"
}

# Mock response for Storefront token creation
MOCK_STOREFRONT_TOKEN = {
    "storefront_access_token": {
        "id": 987654321,
        "access_token": "test_storefront_token",
        "access_scope": "unauthenticated_read_product_listings,unauthenticated_read_checkouts"
    }
}

# Mock response for product search (Storefront API GraphQL)
MOCK_PRODUCTS = {
    "data": {
        "search": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/Product/1",
                        "title": "Test Product",
                        "description": "Test description",
                        "descriptionHtml": "<p>Test description</p>",
                        "priceRangeV2": {
                            "minVariantPrice": {"amount": "100.00", "currencyCode": "USD"},
                            "maxVariantPrice": {"amount": "100.00", "currencyCode": "USD"}
                        },
                        "images": {
                            "edges": [
                                {
                                    "node": {
                                        "url": "https://example.com/product.jpg",
                                        "altText": "Test product image"
                                    }
                                }
                            ]
                        },
                        "variants": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "gid://shopify/ProductVariant/1",
                                        "availableForSale": True
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }
}

# Mock response for checkout creation (Storefront API GraphQL)
MOCK_CHECKOUT_RESPONSE = {
    "data": {
        "checkoutCreate": {
            "checkout": {
                "id": "gid://shopify/Checkout/1",
                "webUrl": "https://checkout.shopify.com/test"
            },
            "checkoutUserErrors": []
        }
    }
}

# Mock response for webhook subscription (Admin API REST)
MOCK_WEBHOOK_SUBSCRIPTION = {
    "webhook": {
        "id": 123456789,
        "topic": "orders/create",
        "address": "https://example.com/api/webhooks/shopify",
        "format": "json",
        "created_at": "2024-01-01T00:00:00Z"
    }
}

# Mock response for webhook list (Admin API REST)
MOCK_WEBHOOK_LIST = {
    "webhooks": [
        {
            "id": 123456789,
            "topic": "orders/create",
            "address": "https://example.com/api/webhooks/shopify",
            "format": "json",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 987654321,
            "topic": "orders/updated",
            "address": "https://example.com/api/webhooks/shopify",
            "format": "json",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}

# Mock OAuth token exchange response
MOCK_TOKEN_EXCHANGE = {
    "access_token": "test_admin_token",
    "scope": "read_products,read_inventory,write_orders,read_orders,write_checkouts,read_checkouts",
    "expires_in": None,
    "associated_user_scope": "read_products,read_inventory,write_orders,read_orders,write_checkouts,read_checkouts",
    "associated_user": {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "email_verified": True,
        "account_owner": True,
        "locale": "en",
        "collaborator": False
    }
}
