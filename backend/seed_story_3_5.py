import asyncio
from app.core.database import engine
from sqlalchemy import text
from datetime import datetime, timedelta
import random


async def seed():
    async with engine.connect() as conn:
        print("Seeding database...")

        # 1. Create Merchant
        await conn.execute(
            text(
                """
            INSERT INTO merchants (id, merchant_key, platform, status, config, created_at, updated_at)
            VALUES (1, 'test-merchant-3-5', 'shopify', 'active', '{"budget_cap": 50.0}', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """
            )
        )
        print(" - Merchant seeded.")

        # 2. Create Conversations
        for i in range(1, 6):
            psid = f"fb-psid-{i:03d}"
            await conn.execute(
                text(
                    f"""
                INSERT INTO conversations (id, merchant_id, platform, platform_sender_id, status, created_at, updated_at)
                VALUES ({i}, 1, 'facebook', '{psid}', 'active', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """
                )
            )

            # 3. Create Cost Records
            # Note: llm_conversation_costs.conversation_id uses the platform_sender_id (e.g. PSID)
            # as per the model definition and logic
            for _ in range(random.randint(2, 5)):
                await conn.execute(
                    text(
                        f"""
                    INSERT INTO llm_conversation_costs (
                        conversation_id, merchant_id, provider, model, 
                        prompt_tokens, completion_tokens, total_tokens,
                        input_cost_usd, output_cost_usd, total_cost_usd,
                        request_timestamp, processing_time_ms, created_at
                    ) VALUES (
                        '{psid}', 1, 'openai', 'gpt-4o-mini',
                        {random.randint(100, 500)}, {random.randint(50, 200)}, {random.randint(150, 700)},
                        {random.uniform(0.001, 0.005)}, {random.uniform(0.002, 0.008)}, {random.uniform(0.003, 0.013)},
                        NOW() - INTERVAL '{random.randint(0, 7)} days', {random.randint(200, 1500)}, NOW()
                    )
                """
                    )
                )

        await conn.commit()
        print(" - Conversations and costs seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
