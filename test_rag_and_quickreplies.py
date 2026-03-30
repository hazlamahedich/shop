#!/usr/bin/env python3
"""Test RAG and Quick Replies with proper conversation flow."""
import requests
import json

API_BASE = "http://localhost:8000/api/v1/widget"

def test_graduation_question():
    """Test the graduation question scenario."""
    print("=" * 60)
    print("TESTING: 'where did he graduate' with conversation context")
    print("=" * 60)
    print()

    # Step 1: Create session
    print("Step 1: Creating session...")
    session_response = requests.post(
        f"{API_BASE}/session",
        json={"merchant_id": "1"}
    )
    session_data = session_response.json()
    session_id = session_data["data"]["sessionId"]
    print(f"✓ Session created: {session_id}")
    print()

    # Step 2: Send greeting
    print("Step 2: Sending greeting 'hello'...")
    greeting_response = requests.post(
        f"{API_BASE}/message",
        json={"session_id": session_id, "message": "hello"}
    )
    greeting_data = greeting_response.json()

    print("Bot Response:")
    print(f"  Content: {greeting_data['data']['content'][:200]}...")

    quick_replies = greeting_data['data'].get('quickReplies') or greeting_data['data'].get('quick_replies')
    if quick_replies:
        print(f"  Quick Replies: {len(quick_replies)} chips")
        for i, reply in enumerate(quick_replies, 1):
            print(f"    {i}. {reply['text']} {reply.get('icon', '')}")
    else:
        print("  Quick Replies: NONE")
    print()

    # Step 3: Ask about graduation
    print("Step 3: Asking 'where did he graduate'...")
    question_response = requests.post(
        f"{API_BASE}/message",
        json={"session_id": session_id, "message": "where did he graduate"}
    )
    question_data = question_response.json()

    print("Bot Response:")
    content = question_data['data']['content']
    print(f"  Content: {content[:300]}...")

    # Check if graduation info was found
    if "university" in content.lower() or "graduated" in content.lower():
        if "santo tomas" in content.lower() or "ust" in content.lower():
            print("  ✅ RAG SUCCESS: Found 'University of Santo Tomas'")
        else:
            print("  ⚠️  RAG PARTIAL: Found graduation info but not specific university")
    else:
        print("  ❌ RAG FAILED: No graduation information found")
        print(f"     Bot said: {content[:200]}")
    print()

    # Check quick replies
    quick_replies = question_data['data'].get('quickReplies') or question_data['data'].get('quick_replies')
    if quick_replies:
        print(f"  Quick Replies: {len(quick_replies)} chips")
        for i, reply in enumerate(quick_replies, 1):
            print(f"    {i}. {reply['text']} {reply.get('icon', '')}")

        # Check if quick replies are contextual
        reply_texts = [r['text'].lower() for r in quick_replies]
        if any(text in reply_texts for text in ['yes', 'no']):
            print("  ❌ WRONG: Quick replies are Yes/No instead of contextual")
        else:
            print("  ✅ Quick replies are contextual")
    else:
        print("  ❌ Quick Replies: NONE")
    print()

    # Check sources
    sources = question_data['data'].get('sources')
    if sources:
        print(f"  Sources: {len(sources)} citations")
        for i, source in enumerate(sources, 1):
            print(f"    {i}. {source.get('title', 'Unknown')}")
    else:
        print("  Sources: NONE (RAG may not have been used)")
    print()

    return {
        'rag_found': 'university' in content.lower() and 'santo tomas' in content.lower(),
        'quick_replies_count': len(quick_replies) if quick_replies else 0,
        'has_sources': sources is not None
    }

if __name__ == '__main__':
    try:
        result = test_graduation_question()

        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"RAG Working: {'✅ YES' if result['rag_found'] else '❌ NO'}")
        print(f"Quick Replies: {'✅ ' + str(result['quick_replies_count']) + ' chips' if result['quick_replies_count'] > 0 else '❌ NONE'}")
        print(f"Has Sources: {'✅ YES' if result['has_sources'] else '❌ NO'}")
        print()

        if not result['rag_found']:
            print("⚠️  RAG ISSUE: The bot should have found 'University of Santo Tomas'")
            print("   This suggests the knowledge base search is not working properly.")

        if result['quick_replies_count'] == 2:
            print("⚠️  QUICK REPLIES ISSUE: Yes/No replies are not contextual")
            print("   Expected: Learn more, Contact us, Ask a question")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Make sure the backend is running on port 8000")
