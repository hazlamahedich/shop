"""CLI command for creating merchant accounts.

Story 1.8: Merchant Dashboard Authentication
Provides interactive and non-interactive modes for creating merchants.

Usage:
    # Interactive mode
    python -m backend.app.cli.create_merchant

    # Non-interactive mode
    python -m backend.app.cli.create_merchant --email merchant@example.com --password SecurePass123
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from sqlalchemy import select

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import async_session
from app.core.auth import hash_password, validate_password_requirements
from app.models.merchant import Merchant


app = typer.Typer(help="Create merchant accounts")


def validate_email(email: str) -> bool:
    """Basic email validation.

    Args:
        email: Email address to validate

    Returns:
        True if email appears valid
    """
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True


def prompt_email() -> str:
    """Prompt user for email address.

    Returns:
        Email address from user input
    """
    while True:
        email = typer.prompt("Enter merchant email").strip()
        if validate_email(email):
            return email
        typer.echo("Invalid email format. Please try again.")


def prompt_password() -> str:
    """Prompt user for password.

    Returns:
        Password from user input
    """
    while True:
        password = typer.prompt("Enter password", hide_input=True)
        is_valid, errors = validate_password_requirements(password)

        if is_valid:
            # Confirm password
            confirm = typer.prompt("Confirm password", hide_input=True)
            if password == confirm:
                return password
            typer.echo("Passwords do not match. Please try again.")
        else:
            typer.echo("Password requirements not met:")
            for error in errors:
                typer.echo(f"  - {error}")


async def create_merchant(email: str, password: str) -> Merchant:
    """Create merchant account with email and password.

    Args:
        email: Merchant email
        password: Plain text password

    Returns:
        Created Merchant instance

    Raises:
        ValueError: If email already exists or password invalid
    """
    # Validate password first (before DB check - prevents email enumeration via timing)
    is_valid, errors = validate_password_requirements(password)
    if not is_valid:
        raise ValueError("Password requirements not met: " + ", ".join(errors))

    async with async_session() as db:
        # Check if email already exists
        result = await db.execute(
            select(Merchant).where(Merchant.email == email)
        )
        existing = result.scalars().first()

        if existing:
            raise ValueError(f"Merchant with email {email} already exists")

        # Hash password
        password_hash = hash_password(password)

        # Generate merchant key
        import uuid
        merchant_key = uuid.uuid4().hex[:12]

        # Create merchant
        merchant = Merchant(
            merchant_key=merchant_key,
            platform="shopify",  # Default platform
            status="active",
            email=email,
            password_hash=password_hash,
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        return merchant


@app.command()
def main(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Merchant email"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Merchant password"),
) -> None:
    """Create a new merchant account.

    If email and password are not provided, runs in interactive mode.
    """
    if email and password:
        # Non-interactive mode
        if not validate_email(email):
            typer.echo(f"Error: Invalid email format: {email}", err=True)
            raise typer.Exit(1)

        is_valid, errors = validate_password_requirements(password)
        if not is_valid:
            typer.echo("Error: Password requirements not met:", err=True)
            for error in errors:
                typer.echo(f"  - {error}", err=True)
            raise typer.Exit(1)

        try:
            merchant = asyncio.run(create_merchant(email, password))
            typer.echo(f"✓ Merchant account created successfully!")
            typer.echo(f"  Merchant ID: {merchant.id}")
            typer.echo(f"  Merchant Key: {merchant.merchant_key}")
            typer.echo(f"  Email: {merchant.email}")
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error creating merchant: {e}", err=True)
            raise typer.Exit(1)

    else:
        # Interactive mode
        typer.echo("=== Create Merchant Account ===")
        typer.echo("Password requirements:")
        typer.echo("  - At least 8 characters")
        typer.echo("  - At least one uppercase letter")
        typer.echo("  - At least one lowercase letter")
        typer.echo()

        email = prompt_email()
        password = prompt_password()

        try:
            merchant = asyncio.run(create_merchant(email, password))
            typer.echo()
            typer.echo(f"✓ Merchant account created successfully!")
            typer.echo(f"  Merchant ID: {merchant.id}")
            typer.echo(f"  Merchant Key: {merchant.merchant_key}")
            typer.echo(f"  Email: {merchant.email}")
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error creating merchant: {e}", err=True)
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
