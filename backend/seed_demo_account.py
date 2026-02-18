#!/usr/bin/env python3
"""Create demo@test.com merchant with fully populated data for testing.

This script creates a complete demo account with realistic data across all tables:
- Merchant account (fully onboarded)
- LLM configuration (Anthropic)
- Shopify & Facebook integrations
- Prerequisite checklist (completed)
- Tutorial progress (completed)
- FAQs (5 items)
- Product pins (4 products)
- Conversations with messages (3 conversations)
- LLM conversation costs (spread across 30 days)
- Budget alerts (read and unread)

Usage:
    python seed_demo_account.py           # Create demo account
    python seed_demo_account.py --reset   # Delete and recreate
"""

import argparse
import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import os
from cryptography.fernet import Fernet

if not os.getenv("FACEBOOK_ENCRYPTION_KEY"):
    temp_key = Fernet.generate_key().decode()
    os.environ["FACEBOOK_ENCRYPTION_KEY"] = temp_key
    print("  Generated temporary encryption key for this session")

from sqlalchemy import delete, select
from app.core.database import async_session
from app.core.auth import hash_password
from app.core.security import encrypt_access_token
from app.models.merchant import Merchant, PersonalityType, StoreProvider
from app.models.llm_configuration import LLMConfiguration
from app.models.tutorial import Tutorial
from app.models.faq import Faq
from app.models.product_pin import ProductPin
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.budget_alert import BudgetAlert
from app.models.handoff_alert import HandoffAlert
from app.models.onboarding import PrerequisiteChecklist
from app.models.shopify_integration import ShopifyIntegration
from app.models.facebook_integration import FacebookIntegration
from app.core.encryption import encrypt_conversation_content

DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "Demo12345"
DEMO_MERCHANT_KEY = "demo-merchant"


async def clear_demo_data(db):
    """Delete all demo account data."""
    result = await db.execute(select(Merchant).where(Merchant.email == DEMO_EMAIL))
    merchant = result.scalars().first()
    if merchant:
        await db.execute(delete(Merchant).where(Merchant.id == merchant.id))
        print(f"  Deleted existing demo account (ID: {merchant.id})")


async def seed_merchant(db) -> Merchant:
    """Create fully onboarded demo merchant."""
    merchant = Merchant(
        merchant_key=DEMO_MERCHANT_KEY,
        platform="shopify",
        status="active",
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        business_name="StyleHub Boutique",
        business_description="Curated fashion and accessories for the modern lifestyle. We specialize in sustainable, ethically-made clothing and unique jewelry pieces.",
        business_hours="Mon-Fri 9AM-6PM PST, Sat 10AM-4PM PST",
        bot_name="StyleBot",
        personality=PersonalityType.FRIENDLY,
        custom_greeting="Hi there! Welcome to StyleHub Boutique. I'm StyleBot, your personal shopping assistant. How can I help you find the perfect piece today?",
        use_custom_greeting=True,
        store_provider=StoreProvider.SHOPIFY,
        deployed_at=datetime.utcnow() - timedelta(days=60),
    )
    db.add(merchant)
    await db.flush()
    return merchant


async def seed_llm_configuration(db, merchant: Merchant):
    """Create LLM configuration with Anthropic."""
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="anthropic",
        api_key_encrypted=encrypt_access_token("sk-ant-demo-test-key-placeholder"),
        cloud_model="claude-3-haiku-20240307",
        status="active",
        configured_at=datetime.utcnow() - timedelta(days=60),
        last_test_at=datetime.utcnow() - timedelta(days=1),
        test_result={"success": True, "latency_ms": 245, "model": "claude-3-haiku-20240307"},
        total_tokens_used=random.randint(150000, 300000),
        total_cost_usd=round(random.uniform(15.0, 45.0), 4),
    )
    db.add(config)


async def seed_prerequisite_checklist(db, merchant: Merchant):
    """Create completed prerequisite checklist."""
    checklist = PrerequisiteChecklist(
        merchant_id=merchant.id,
        has_cloud_account=True,
        has_facebook_account=True,
        has_shopify_access=True,
        has_llm_provider_choice=True,
        completed_at=datetime.utcnow() - timedelta(days=65),
    )
    db.add(checklist)


async def seed_tutorial(db, merchant: Merchant):
    """Create completed tutorial."""
    tutorial = Tutorial(
        merchant_id=merchant.id,
        current_step=8,
        completed_steps=[
            "welcome",
            "connect_shopify",
            "connect_facebook",
            "configure_llm",
            "add_faqs",
            "pin_products",
            "customize_bot",
            "test_bot",
        ],
        started_at=datetime.utcnow() - timedelta(days=60),
        completed_at=datetime.utcnow() - timedelta(days=60),
        skipped=False,
        tutorial_version="1.0",
        steps_total=8,
    )
    db.add(tutorial)


async def seed_shopify_integration(db, merchant: Merchant):
    """Create Shopify integration."""
    integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="stylehub-boutique.myshopify.com",
        shop_name="StyleHub Boutique",
        storefront_token_encrypted=encrypt_access_token("shpat_demo_storefront_token"),
        admin_token_encrypted=encrypt_access_token("shpat_demo_admin_token"),
        scopes=["read_products", "read_product_listings", "read_inventory"],
        status="active",
        storefront_api_verified=True,
        admin_api_verified=True,
        webhook_subscribed=True,
        webhook_topic_subscriptions=[
            "products/create",
            "products/update",
            "inventory_levels/update",
        ],
        last_webhook_at=datetime.utcnow() - timedelta(hours=2),
        last_webhook_verified_at=datetime.utcnow() - timedelta(hours=2),
        connected_at=datetime.utcnow() - timedelta(days=60),
    )
    db.add(integration)


async def seed_facebook_integration(db, merchant: Merchant):
    """Create Facebook integration."""
    integration = FacebookIntegration(
        merchant_id=merchant.id,
        page_id="123456789012345",
        page_name="StyleHub Boutique",
        page_picture_url="https://graph.facebook.com/123456789012345/picture?type=large",
        access_token_encrypted=encrypt_access_token("EAA demo facebook page access token"),
        scopes=["pages_messaging", "pages_read_engagement", "pages_manage_metadata"],
        status="active",
        webhook_verified=True,
        last_webhook_at=datetime.utcnow() - timedelta(minutes=30),
        last_webhook_verified_at=datetime.utcnow() - timedelta(days=1),
        connected_at=datetime.utcnow() - timedelta(days=60),
    )
    db.add(integration)


async def seed_faqs(db, merchant: Merchant):
    """Create FAQ items."""
    faqs = [
        Faq(
            merchant_id=merchant.id,
            question="What is your return policy?",
            answer="We offer a 30-day return policy for all unworn items in original packaging. Simply start a return through your order confirmation email or contact us directly.",
            keywords="return, refund, exchange, policy",
            order_index=1,
        ),
        Faq(
            merchant_id=merchant.id,
            question="Do you offer international shipping?",
            answer="Yes! We ship to over 50 countries worldwide. International orders typically arrive within 7-14 business days. Shipping costs are calculated at checkout.",
            keywords="shipping, international, delivery, worldwide",
            order_index=2,
        ),
        Faq(
            merchant_id=merchant.id,
            question="How do I track my order?",
            answer="Once your order ships, you'll receive an email with a tracking number. You can also log into your account to view order status at any time.",
            keywords="track, order, status, shipping",
            order_index=3,
        ),
        Faq(
            merchant_id=merchant.id,
            question="Are your products sustainable?",
            answer="Absolutely! We're committed to sustainability. 80% of our products are made from organic or recycled materials, and we work with certified ethical manufacturers.",
            keywords="sustainable, eco-friendly, organic, ethical",
            order_index=4,
        ),
        Faq(
            merchant_id=merchant.id,
            question="Do you have a loyalty program?",
            answer="Yes! Join our StyleRewards program to earn points on every purchase. Get 1 point per dollar spent, and redeem 100 points for a $10 discount.",
            keywords="loyalty, rewards, points, membership",
            order_index=5,
        ),
    ]
    for faq in faqs:
        db.add(faq)


async def seed_product_pins(db, merchant: Merchant):
    """Create product pins."""
    products = [
        {
            "product_id": "shopify-product-001",
            "title": "Organic Cotton Essential Tee",
            "image_url": "https://cdn.shopify.com/s/files/1/0000/0001/products/essential-tee.jpg",
            "order": 1,
        },
        {
            "product_id": "shopify-product-002",
            "title": "Recycled Denim Straight Leg Jeans",
            "image_url": "https://cdn.shopify.com/s/files/1/0000/0001/products/denim-jeans.jpg",
            "order": 2,
        },
        {
            "product_id": "shopify-product-003",
            "title": "Handcrafted Gold Chain Necklace",
            "image_url": "https://cdn.shopify.com/s/files/1/0000/0001/products/gold-necklace.jpg",
            "order": 3,
        },
        {
            "product_id": "shopify-product-004",
            "title": "Sustainable Linen Blazer",
            "image_url": "https://cdn.shopify.com/s/files/1/0000/0001/products/linen-blazer.jpg",
            "order": 4,
        },
    ]
    for product in products:
        pin = ProductPin(
            id=str(uuid4()),
            merchant_id=merchant.id,
            product_id=product["product_id"],
            product_title=product["title"],
            product_image_url=product["image_url"],
            pinned_order=product["order"],
            pinned_at=datetime.utcnow() - timedelta(days=55),
        )
        db.add(pin)


async def seed_conversations_and_messages(db, merchant: Merchant):
    """Create conversations with messages."""
    conversations_data = [
        {
            "platform_sender_id": "fb-user-001",
            "status": "closed",
            "messages": [
                {
                    "sender": "customer",
                    "content": "Hi, I'm looking for a birthday gift for my sister. She loves sustainable fashion.",
                },
                {
                    "sender": "bot",
                    "content": "How wonderful! I'd love to help you find the perfect sustainable gift. What's your budget range, and do you know her preferred style?",
                },
                {"sender": "customer", "content": "Around $50-75. She likes minimalist styles."},
                {
                    "sender": "bot",
                    "content": "Perfect! I'd recommend our Organic Cotton Essential Tee ($35) paired with our Handcrafted Gold Chain Necklace ($42). Both are sustainable and have that clean, minimalist aesthetic. Would you like me to tell you more about either item?",
                },
                {
                    "sender": "customer",
                    "content": "That sounds perfect! What colors does the tee come in?",
                },
                {
                    "sender": "bot",
                    "content": "The Organic Cotton Essential Tee comes in White, Black, Sage Green, and Navy Blue. All colors use natural dyes. Which do you think she'd prefer?",
                },
                {"sender": "customer", "content": "Sage Green please! How do I order?"},
                {
                    "sender": "bot",
                    "content": "Great choice! You can add both items directly to cart on our website. I'll send you the links. Is there anything else I can help with?",
                },
            ],
        },
        {
            "platform_sender_id": "fb-user-002",
            "status": "active",
            "messages": [
                {"sender": "customer", "content": "Do you have the linen blazer in size M?"},
                {
                    "sender": "bot",
                    "content": "Let me check our inventory for the Sustainable Linen Blazer in Medium... Yes, we have it in stock! It's available in Natural, White, and Light Blue. Which color interests you?",
                },
                {"sender": "customer", "content": "Natural please. What's the price?"},
                {
                    "sender": "bot",
                    "content": "The Sustainable Linen Blazer is $128. It's made from 100% organic Belgian linen and features a relaxed fit perfect for both casual and semi-formal occasions.",
                },
            ],
        },
        {
            "platform_sender_id": "fb-user-003",
            "status": "active",
            "messages": [
                {
                    "sender": "customer",
                    "content": "I ordered last week but haven't received tracking. Order #12345",
                },
                {
                    "sender": "bot",
                    "content": "I'm sorry to hear about the delay! Let me look up order #12345 for you right away.",
                },
            ],
        },
    ]

    for conv_data in conversations_data:
        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            llm_provider="anthropic",
            platform_sender_id=conv_data["platform_sender_id"],
            status=conv_data["status"],
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
        )
        db.add(conversation)
        await db.flush()

        base_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        for i, msg_data in enumerate(conv_data["messages"]):
            content = msg_data["content"]
            if msg_data["sender"] == "customer":
                content = encrypt_conversation_content(content)

            message = Message(
                conversation_id=conversation.id,
                sender=msg_data["sender"],
                content=content,
                message_type="text",
                created_at=base_time + timedelta(minutes=i * 2),
            )
            db.add(message)


async def seed_llm_costs(db, merchant: Merchant):
    """Create LLM conversation costs spread across 30 days."""
    providers = ["anthropic", "anthropic", "anthropic", "openai"]
    models = {
        "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
    }

    costs = []
    for days_ago in range(30, 0, -1):
        num_requests = random.randint(3, 12)
        for _ in range(num_requests):
            provider = random.choice(providers)
            model = random.choice(models[provider])

            prompt_tokens = random.randint(150, 800)
            completion_tokens = random.randint(50, 400)
            total_tokens = prompt_tokens + completion_tokens

            if provider == "anthropic":
                if "haiku" in model:
                    input_cost = prompt_tokens * 0.00000025
                    output_cost = completion_tokens * 0.00000125
                else:
                    input_cost = prompt_tokens * 0.000003
                    output_cost = completion_tokens * 0.000015
            else:
                if "mini" in model:
                    input_cost = prompt_tokens * 0.00000015
                    output_cost = completion_tokens * 0.0000006
                else:
                    input_cost = prompt_tokens * 0.0000025
                    output_cost = completion_tokens * 0.00001

            cost = LLMConversationCost(
                conversation_id=f"conv-{random.randint(1000, 9999)}",
                merchant_id=merchant.id,
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_cost_usd=round(input_cost, 6),
                output_cost_usd=round(output_cost, 6),
                total_cost_usd=round(input_cost + output_cost, 6),
                request_timestamp=datetime.utcnow()
                - timedelta(days=days_ago, hours=random.randint(0, 23)),
                processing_time_ms=random.randint(150, 800),
            )
            costs.append(cost)

    for cost in costs:
        db.add(cost)

    return len(costs)


async def seed_budget_alerts(db, merchant: Merchant):
    """Create budget alerts (read and unread)."""
    alerts = [
        BudgetAlert(
            merchant_id=merchant.id,
            threshold=80,
            message="You've reached 80% of your monthly budget ($40 of $50). Consider reviewing your usage.",
            created_at=datetime.utcnow() - timedelta(days=5),
            is_read=True,
        ),
        BudgetAlert(
            merchant_id=merchant.id,
            threshold=100,
            message="You've reached 100% of your monthly budget ($50). Additional usage will incur overage charges.",
            created_at=datetime.utcnow() - timedelta(days=2),
            is_read=False,
        ),
        BudgetAlert(
            merchant_id=merchant.id,
            threshold=80,
            message="You've reached 80% of your monthly budget ($40 of $50). Consider reviewing your usage.",
            created_at=datetime.utcnow() - timedelta(days=35),
            is_read=True,
        ),
    ]
    for alert in alerts:
        db.add(alert)


async def seed_handoff_alerts_and_conversations(db, merchant: Merchant):
    """Create handoff alerts and a handoff conversation for Stories 4-5 and 4-6.

    Creates:
    - 1 conversation with handoff_status='pending' (for queue display)
    - 3 HandoffAlert records with different urgency levels (for notification testing)
    """
    handoff_conversation = Conversation(
        merchant_id=merchant.id,
        platform="facebook",
        llm_provider="anthropic",
        platform_sender_id="fb-user-handoff-001",
        status="handoff",
        handoff_status="pending",
        handoff_reason="keyword",
        handoff_triggered_at=datetime.utcnow() - timedelta(minutes=15),
        created_at=datetime.utcnow() - timedelta(minutes=45),
    )
    db.add(handoff_conversation)
    await db.flush()

    handoff_messages = [
        {
            "sender": "customer",
            "content": "Hi, I have a question about my recent order #SH-12345",
        },
        {
            "sender": "bot",
            "content": "I'd be happy to help with your order! Let me look that up for you.",
        },
        {
            "sender": "customer",
            "content": "It says delivered but I never received it. This is really frustrating!",
        },
        {
            "sender": "bot",
            "content": "I understand how frustrating that must be. Let me check the tracking details for you.",
        },
        {
            "sender": "customer",
            "content": "I need to talk to a human about this immediately!",
        },
    ]

    base_time = datetime.utcnow() - timedelta(minutes=45)
    for i, msg_data in enumerate(handoff_messages):
        content = msg_data["content"]
        if msg_data["sender"] == "customer":
            content = encrypt_conversation_content(content)

        message = Message(
            conversation_id=handoff_conversation.id,
            sender=msg_data["sender"],
            content=content,
            message_type="text",
            created_at=base_time + timedelta(minutes=i * 3),
        )
        db.add(message)

    handoff_alerts = [
        HandoffAlert(
            merchant_id=merchant.id,
            conversation_id=handoff_conversation.id,
            urgency_level="high",
            customer_name="Sarah Chen",
            customer_id="fb-user-handoff-001",
            conversation_preview="Order #SH-12345 delivery issue - customer needs immediate help\n\nCustomer: I need to talk to a human about this immediately!",
            wait_time_seconds=900,
            is_read=False,
            created_at=datetime.utcnow() - timedelta(minutes=15),
        ),
        HandoffAlert(
            merchant_id=merchant.id,
            conversation_id=handoff_conversation.id - 1,
            urgency_level="medium",
            customer_name="Mike Rodriguez",
            customer_id="fb-user-low-conf-001",
            conversation_preview="Bot had trouble understanding product requirements\n\nCustomer kept asking about sizes but bot gave generic responses",
            wait_time_seconds=1800,
            is_read=False,
            created_at=datetime.utcnow() - timedelta(hours=1),
        ),
        HandoffAlert(
            merchant_id=merchant.id,
            conversation_id=handoff_conversation.id - 2,
            urgency_level="low",
            customer_name=None,
            customer_id="fb-user-keyword-002",
            conversation_preview="Customer asked for customer service contact\n\nCustomer: Can I speak to customer service?",
            wait_time_seconds=7200,
            is_read=True,
            created_at=datetime.utcnow() - timedelta(hours=3),
        ),
        HandoffAlert(
            merchant_id=merchant.id,
            conversation_id=handoff_conversation.id,
            urgency_level="high",
            customer_name="Checkout Customer",
            customer_id="fb-user-checkout-001",
            conversation_preview="Checkout issue during purchase\n\nCustomer: Help! My payment won't go through at checkout!\nBot: I'm sorry, I'm having trouble processing that request...",
            wait_time_seconds=300,
            is_read=False,
            created_at=datetime.utcnow() - timedelta(minutes=5),
        ),
    ]
    for alert in handoff_alerts:
        db.add(alert)

    return len(handoff_alerts)


async def main():
    parser = argparse.ArgumentParser(description="Seed demo account with test data")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate demo account")
    args = parser.parse_args()

    print("=" * 60)
    print("DEMO ACCOUNT SEED SCRIPT")
    print("=" * 60)
    print()

    async with async_session() as db:
        if args.reset:
            print("Resetting demo account...")
            await clear_demo_data(db)
            await db.commit()
            print()

        result = await db.execute(select(Merchant).where(Merchant.email == DEMO_EMAIL))
        existing = result.scalars().first()

        if existing:
            print(f"Demo account already exists: {DEMO_EMAIL}")
            print("  Use --reset to delete and recreate")
            print()
            print(f"  Email: {DEMO_EMAIL}")
            print(f"  Password: {DEMO_PASSWORD}")
            print(f"  Merchant Key: {existing.merchant_key}")
            return

        print("Creating demo merchant...")
        merchant = await seed_merchant(db)
        print(f"  Created merchant ID: {merchant.id}")

        print("Creating LLM configuration...")
        await seed_llm_configuration(db, merchant)

        print("Creating prerequisite checklist...")
        await seed_prerequisite_checklist(db, merchant)

        print("Creating tutorial progress...")
        await seed_tutorial(db, merchant)

        print("Creating Shopify integration...")
        await seed_shopify_integration(db, merchant)

        print("Creating Facebook integration...")
        await seed_facebook_integration(db, merchant)

        print("Creating FAQs...")
        await seed_faqs(db, merchant)

        print("Creating product pins...")
        await seed_product_pins(db, merchant)

        print("Creating conversations and messages...")
        await seed_conversations_and_messages(db, merchant)

        print("Creating LLM costs (30 days of data)...")
        num_costs = await seed_llm_costs(db, merchant)
        print(f"  Created {num_costs} cost records")

        print("Creating budget alerts...")
        await seed_budget_alerts(db, merchant)

        print("Creating handoff alerts and conversations (Story 4-5/4-6)...")
        num_handoff_alerts = await seed_handoff_alerts_and_conversations(db, merchant)
        print(f"  Created {num_handoff_alerts} handoff alerts")

        await db.commit()

        print()
        print("=" * 60)
        print("DEMO ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Login credentials:")
        print(f"  Email:    {DEMO_EMAIL}")
        print(f"  Password: {DEMO_PASSWORD}")
        print()
        print("Data populated:")
        print("  - Fully onboarded merchant account")
        print("  - LLM configuration (Anthropic)")
        print("  - Shopify integration (active)")
        print("  - Facebook integration (active)")
        print("  - Prerequisite checklist (completed)")
        print("  - Tutorial (completed)")
        print("  - 5 FAQs")
        print("  - 4 product pins")
        print("  - 4 conversations with messages (1 with handoff)")
        print(f"  - {num_costs} LLM cost records (30 days)")
        print("  - 3 budget alerts (1 unread)")
        print(f"  - {num_handoff_alerts} handoff alerts (3 unread, 2 high urgency)")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
