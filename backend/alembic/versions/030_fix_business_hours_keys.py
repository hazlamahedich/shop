"""Fix business_hours_config keys from camelCase to snake_case.

Revision ID: 030_fix_business_hours_keys
Revises: 029_handoff_resolution_fields
Create Date: 2026-02-24

Bug: model_dump() with serialize_by_alias=True stored camelCase keys
(isOpen, openTime, closeTime), but business_hours_service.py expects
snake_case keys (is_open, open_time, close_time).

This caused all handoffs to be incorrectly flagged as "after hours"
since is_open key wasn't found, defaulting to False (closed).

This migration:
- Transforms existing camelCase keys to snake_case
- Is idempotent (safe to run multiple times)
- Logs each merchant_id that gets fixed
- Has downgrade to revert if needed

Run: alembic upgrade head
"""

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection
import logging
import json

revision = "030_fix_business_hours_keys"
down_revision = "029_resolution_fields"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.migration")


def _transform_hours_to_snake_case(hours: list) -> tuple[list, bool]:
    """Transform hours array from camelCase to snake_case keys.

    Returns:
        Tuple of (transformed_hours, was_transformed)
    """
    key_mapping = {
        "isOpen": "is_open",
        "openTime": "open_time",
        "closeTime": "close_time",
    }

    transformed = False
    new_hours = []

    for day_config in hours:
        if not isinstance(day_config, dict):
            new_hours.append(day_config)
            continue

        new_config = {}
        for key, value in day_config.items():
            if key in key_mapping:
                new_config[key_mapping[key]] = value
                transformed = True
            else:
                new_config[key] = value
        new_hours.append(new_config)

    return new_hours, transformed


def _transform_hours_to_camel_case(hours: list) -> tuple[list, bool]:
    """Transform hours array from snake_case to camelCase keys.

    Returns:
        Tuple of (transformed_hours, was_transformed)
    """
    key_mapping = {
        "is_open": "isOpen",
        "open_time": "openTime",
        "close_time": "closeTime",
    }

    transformed = False
    new_hours = []

    for day_config in hours:
        if not isinstance(day_config, dict):
            new_hours.append(day_config)
            continue

        new_config = {}
        for key, value in day_config.items():
            if key in key_mapping:
                new_config[key_mapping[key]] = value
                transformed = True
            else:
                new_config[key] = value
        new_hours.append(new_config)

    return new_hours, transformed


def upgrade() -> None:
    """Fix business_hours_config keys from camelCase to snake_case."""
    conn: Connection = op.get_bind()

    result = conn.execute(
        text(
            "SELECT id, business_hours_config FROM merchants WHERE business_hours_config IS NOT NULL"
        )
    )
    merchants = result.fetchall()

    fixed_count = 0
    skipped_count = 0

    for merchant_id, config in merchants:
        if not config:
            skipped_count += 1
            continue

        if isinstance(config, str):
            config = json.loads(config)

        hours = config.get("hours", [])
        if not hours:
            skipped_count += 1
            continue

        new_hours, was_transformed = _transform_hours_to_snake_case(hours)

        if was_transformed:
            config["hours"] = new_hours

            conn.execute(
                text("UPDATE merchants SET business_hours_config = :config WHERE id = :id"),
                {"config": json.dumps(config), "id": merchant_id},
            )

            logger.info(f"Fixed business_hours_config for merchant_id: {merchant_id}")
            fixed_count += 1
        else:
            skipped_count += 1

    logger.info(
        f"Migration complete: Fixed {fixed_count} of {len(merchants)} merchants, skipped {skipped_count}"
    )


def downgrade() -> None:
    """Revert business_hours_config keys from snake_case to camelCase."""
    conn: Connection = op.get_bind()

    result = conn.execute(
        text(
            "SELECT id, business_hours_config FROM merchants WHERE business_hours_config IS NOT NULL"
        )
    )
    merchants = result.fetchall()

    reverted_count = 0
    skipped_count = 0

    for merchant_id, config in merchants:
        if not config:
            skipped_count += 1
            continue

        if isinstance(config, str):
            config = json.loads(config)

        hours = config.get("hours", [])
        if not hours:
            skipped_count += 1
            continue

        new_hours, was_transformed = _transform_hours_to_camel_case(hours)

        if was_transformed:
            config["hours"] = new_hours

            conn.execute(
                text("UPDATE merchants SET business_hours_config = :config WHERE id = :id"),
                {"config": json.dumps(config), "id": merchant_id},
            )

            logger.info(f"Reverted business_hours_config for merchant_id: {merchant_id}")
            reverted_count += 1
        else:
            skipped_count += 1

    logger.info(
        f"Downgrade complete: Reverted {reverted_count} of {len(merchants)} merchants, skipped {skipped_count}"
    )
