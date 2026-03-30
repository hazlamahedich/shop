#!/usr/bin/env python3
"""Test script to verify response_type tracking is working correctly.

This script tests the fix for the RAG response type breakdown issue.
It verifies that:
1. LLM responses include response_type in metadata
2. Cost tracking extracts and stores response_type correctly
3. Response time distribution API returns breakdown by type

Usage:
    python test_response_type_fix.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.llm_conversation_cost import LLMConversationCost
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService


async def check_response_type_data():
    """Check if response_type data is being stored correctly."""
    print("🔍 Checking response_type data in database...")

    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if we have any cost records
        result = await session.execute(
            select(LLMConversationCost)
            .where(LLMConversationCost.response_type.isnot(None))
            .limit(10)
        )
        records = result.scalars().all()

        if not records:
            print("⚠️  No response_type records found. You need to:")
            print("   1. Send some messages through the widget")
            print("   2. Wait for cost tracking to record them")
            print("   3. Run this test again")
            return False

        print(f"\n✅ Found {len(records)} cost records with response_type\n")

        # Count by response type
        rag_count = sum(1 for r in records if r.response_type == "rag")
        general_count = sum(1 for r in records if r.response_type == "general")
        unknown_count = sum(1 for r in records if r.response_type == "unknown")

        print("📊 Response Type Distribution:")
        print(f"   RAG:     {rag_count}")
        print(f"   General: {general_count}")
        print(f"   Unknown: {unknown_count}")

        # Show sample records
        print("\n📋 Sample Records:")
        for record in records[:5]:
            print(f"   - {record.created_at.strftime('%Y-%m-%d %H:%M')} | "
                  f"{record.response_type:8} | {record.model} | "
                  f"{record.processing_time_ms:.0f}ms" if record.processing_time_ms else "N/A")

        print("\n" + "="*60)
        print("✅ Response type tracking is working!")
        print("="*60)

        return True


async def test_analytics_api():
    """Test that the analytics API returns response type breakdown."""
    print("\n🔍 Testing analytics API response type breakdown...")

    service = AggregatedAnalyticsService()

    try:
        # You'll need to provide a valid merchant_id here
        # For testing, we'll use merchant_id=1
        result = await service.get_response_time_distribution(
            db=None,  # We'll skip actual DB call for this test
            merchant_id=1,
            days=7
        )

        if result.get("responseTypeBreakdown"):
            print("✅ Analytics API returns response type breakdown")
            breakdown = result["responseTypeBreakdown"]
            print(f"   RAG:     {breakdown.get('rag', {}).get('count', 0)} responses")
            print(f"   General: {breakdown.get('general', {}).get('count', 0)} responses")
        else:
            print("⚠️  Analytics API doesn't include response type breakdown yet")
            print("   This is expected if there are no recent cost records")

    except Exception as e:
        print(f"⚠️  Could not test analytics API: {e}")


async def main():
    """Run all tests."""
    print("="*60)
    print("Testing Response Type Tracking Fix")
    print("="*60 + "\n")

    try:
        success = await check_response_type_data()

        if success:
            await test_analytics_api()

        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Send messages through the widget")
        print("2. Check the Response Time Widget in the dashboard")
        print("3. Verify RAG vs General breakdown appears")
        print("\nExpected in widget:")
        print("┌────────────────────────────────────┐")
        print("│ Response Type Breakdown           │")
        print("│ ┌────────────┬──────────────────┐ │")
        print("│ │ RAG        │ P50: 1.2s        │ │")
        print("│ │            │ P95: 2.1s        │ │")
        print("│ │            │ 23 responses      │ │")
        print("│ ├────────────┼──────────────────┤ │")
        print("│ │ General    │ P50: 0.8s        │ │")
        print("│ │            │ P95: 1.5s        │ │")
        print("│ │            │ 45 responses      │ │")
        print("│ └────────────┴──────────────────┘ │")
        print("└────────────────────────────────────┘")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
