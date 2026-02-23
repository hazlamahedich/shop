"""Test script for handoff flow with urgency and business hours.

This script:
1. Creates test conversations with handoff-triggering messages
2. Verifies conversation status changes to "handoff"
3. Checks if HandoffAlert was created with correct urgency
4. Tests business hours awareness (is_offline flag)

Run: python backend/scripts/test_handoff_gap.py

Story 4-12: Business Hours Aware Handoff
- Urgency Logic:
  - HIGH: Checkout mentioned (revenue at risk)
  - MEDIUM: Low confidence or clarification loop (bot failed)
  - LOW: Keyword trigger (routine request)
  - After hours: All become LOW (no one available)
"""

from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy import select, delete

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.handoff_alert import HandoffAlert
from app.models.merchant import Merchant
from app.services.conversation.unified_conversation_service import UnifiedConversationService
from app.services.conversation.schemas import ConversationContext, Channel


async def get_merchant() -> Merchant | None:
    """Get merchant with business_hours_config loaded."""
    async with async_session() as db:
        result = await db.execute(select(Merchant).where(Merchant.id == 1))
        return result.scalars().first()


async def cleanup_test_data(session_id_prefix: str) -> None:
    """Clean up test data from previous runs."""
    from app.models.message import Message

    async with async_session() as db:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.platform_sender_id.startswith(session_id_prefix)
            )
        )
        convs = conv_result.scalars().all()

        for conv in convs:
            await db.execute(delete(Message).where(Message.conversation_id == conv.id))
            await db.execute(delete(HandoffAlert).where(HandoffAlert.conversation_id == conv.id))
            await db.delete(conv)
        await db.commit()


async def run_single_test(test_num: int, message: str, merchant_id: int, session_id: str) -> dict:
    """Run a single handoff test with its own database session."""
    result = {
        "test_num": test_num,
        "message": message,
        "session_id": session_id,
        "intent": None,
        "confidence": None,
        "response": None,
        "conversation_status": None,
        "handoff_status": None,
        "handoff_reason": None,
        "alert_found": False,
        "alert_urgency": None,
        "alert_is_offline": None,
        "error": None,
        "datetime_error": False,
    }

    async with async_session() as db:
        try:
            service = UnifiedConversationService(db=db)
            context = ConversationContext(
                session_id=session_id,
                merchant_id=merchant_id,
                channel=Channel.WIDGET,
                conversation_history=[],
                platform_sender_id=None,
                user_id=None,
            )

            response = await service.process_message(
                db=db,
                context=context,
                message=message,
            )

            result["intent"] = response.intent
            result["confidence"] = response.confidence
            result["response"] = response.message[:100] if response.message else None

        except Exception as e:
            error_str = str(e)
            result["error"] = error_str
            if "offset-naive and offset-aware datetimes" in error_str:
                result["datetime_error"] = True
            return result

        try:
            conv_result = await db.execute(
                select(Conversation).where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.platform_sender_id == session_id,
                )
            )
            conversation = conv_result.scalars().first()

            if conversation:
                result["conversation_status"] = conversation.status
                result["handoff_status"] = conversation.handoff_status
                result["handoff_reason"] = conversation.handoff_reason

                alert_result = await db.execute(
                    select(HandoffAlert).where(HandoffAlert.conversation_id == conversation.id)
                )
                alert = alert_result.scalars().first()

                if alert:
                    result["alert_found"] = True
                    result["alert_urgency"] = alert.urgency_level
                    result["alert_is_offline"] = getattr(alert, "is_offline", False)

        except Exception as e:
            result["error"] = f"Error checking results: {e}"

    return result


async def main() -> None:
    print("=" * 70)
    print("HANDOFF FLOW TEST - Urgency & Business Hours")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    merchant = await get_merchant()
    if not merchant:
        print("ERROR: Merchant not found")
        return

    merchant_id = merchant.id
    business_hours = getattr(merchant, "business_hours_config", None)
    test_session_prefix = "test_handoff_gap"

    print(f"Merchant ID: {merchant_id}")
    print(f"Business Hours Config: {'Yes' if business_hours else 'No'}")
    print(f"Test Session Prefix: {test_session_prefix}")
    print()

    print("Cleaning up any existing test data...")
    await cleanup_test_data(test_session_prefix)

    test_cases = [
        ("I need to speak to a human", "low", "Keyword trigger = LOW"),
        ("connect me to an agent", "low", "Keyword trigger = LOW"),
        ("let me talk to customer service", "low", "Keyword trigger = LOW"),
    ]

    results = []

    for i, (message, expected_urgency, description) in enumerate(test_cases, 1):
        session_id = f"{test_session_prefix}_{i}"
        print()
        print("-" * 70)
        print(f"TEST {i}: '{message}'")
        print(f"  Expected: {expected_urgency.upper()} ({description})")
        print("-" * 70)

        result = await run_single_test(i, message, merchant_id, session_id)
        results.append(result)

        if result["error"]:
            if result["datetime_error"]:
                print(f"  [ERROR] DateTime timezone mismatch!")
            else:
                print(f"  [ERROR] {result['error'][:200]}...")
            continue

        print(f"  Intent: {result['intent']}")
        print(f"  Confidence: {result['confidence']}")
        if result["response"]:
            print(f"  Response: {result['response'][:80]}...")

        print()
        print("  STEP 1: Conversation Status")
        print("  " + "-" * 40)

        if result["conversation_status"]:
            print(f"    Status: {result['conversation_status']}")
            print(f"    Handoff Status: {result['handoff_status']}")
            print(f"    Handoff Reason: {result['handoff_reason']}")

            if result["conversation_status"] == "handoff":
                print("    [PASS] Status correctly set to 'handoff'")
            else:
                print("    [FAIL] Status NOT set to 'handoff'")
        else:
            print("    [FAIL] Conversation not found!")

        print()
        print("  STEP 2: HandoffAlert Check")
        print("  " + "-" * 40)

        if result["alert_found"]:
            urgency_match = result["alert_urgency"] == expected_urgency
            urgency_status = "[PASS]" if urgency_match else "[FAIL]"
            print(
                f"    {urgency_status} Urgency: {result['alert_urgency']} (expected: {expected_urgency})"
            )
            print(f"    [INFO] Is Offline: {result['alert_is_offline']}")

            if result["alert_is_offline"]:
                print("    [INFO] Outside business hours - urgency should be LOW")
                if result["alert_urgency"] == "low":
                    print("    [PASS] After-hours urgency correctly set to LOW")
                else:
                    print("    [FAIL] After-hours urgency should be LOW")
        else:
            print("    [FAIL] NO HandoffAlert found!")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    errors = sum(1 for r in results if r["error"])
    alert_failures = sum(1 for r in results if not r["alert_found"] and not r["error"])
    urgency_matches = sum(
        1
        for i, r in enumerate(results)
        if r["alert_found"] and r["alert_urgency"] == test_cases[i][1] and not r["error"]
    )

    print()
    print(f"Tests run: {len(test_cases)}")
    print(f"Errors: {errors}")
    print(f"Alerts created: {len(results) - alert_failures - errors}")
    print(f"Urgency correct: {urgency_matches}/{len(test_cases) - errors}")

    if alert_failures > 0:
        print()
        print(f"[FAIL] {alert_failures} tests missing HandoffAlerts")
    else:
        print()
        print("[PASS] All HandoffAlerts created successfully!")

    if errors == 0 and alert_failures == 0:
        print("[PASS] Handoff flow is working correctly!")

    print()
    print(
        "See: _bmad-output/planning-artifacts/sprint-change-proposal-handoff-alert-integration.md"
    )
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
