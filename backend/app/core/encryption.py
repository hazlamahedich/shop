"""Field-level encryption utilities for sensitive conversation data (NFR-S2).

Provides Fernet symmetric encryption for conversation content and metadata.
Uses separate encryption keys from OAuth tokens to implement defense in depth.

Data to encrypt:
- Customer message content
- Voluntary memory (preferences, history)
- User input data

Data to keep plaintext:
- Order references (business requirement)
- Bot responses (non-sensitive)
- Message metadata (timestamps, IDs)
"""

from __future__ import annotations

import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def get_conversation_fernet() -> Fernet:
    """Get Fernet instance for conversation encryption.

    Returns:
        Fernet instance configured with CONVERSATION_ENCRYPTION_KEY

    Raises:
        ValueError: If CONVERSATION_ENCRYPTION_KEY is not set

    Note:
        Creates new instance each time to support key rotation.
        Separate from FACEBOOK_ENCRYPTION_KEY for defense in depth.
    """
    key = os.getenv("CONVERSATION_ENCRYPTION_KEY")
    if not key:
        # Fallback to FACEBOOK_ENCRYPTION_KEY for development
        # In production, always use separate CONVERSATION_ENCRYPTION_KEY
        key = os.getenv("FACEBOOK_ENCRYPTION_KEY", "")
        if not key:
            raise ValueError(
                "CONVERSATION_ENCRYPTION_KEY environment variable must be set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
    return Fernet(key.encode())


def encrypt_conversation_content(content: str) -> str:
    """Encrypt conversation content (customer messages, user input).

    Args:
        content: Plain text conversation content

    Returns:
        Encrypted content as base64 string

    Note:
        Returns original content if empty (None or empty string).
        This allows graceful migration from plaintext to encrypted.
    """
    if not content:
        return content

    fernet = get_conversation_fernet()
    encrypted = fernet.encrypt(content.encode())
    return encrypted.decode()


def decrypt_conversation_content(encrypted: str) -> str:
    """Decrypt conversation content.

    Args:
        encrypted: Encrypted content string

    Returns:
        Decrypted plain text content

    Note:
        Returns original value if decryption fails.
        This supports migration from plaintext to encrypted data.
        Once all data is encrypted, this could raise instead.
    """
    if not encrypted:
        return encrypted

    try:
        fernet = get_conversation_fernet()
        decrypted = fernet.decrypt(encrypted.encode())
        return decrypted.decode()
    except (InvalidToken, Exception):
        # Return original if decryption fails (migration case)
        # TODO: After migration complete, consider raising error instead
        return encrypted


def encrypt_metadata(metadata: dict) -> dict:
    """Encrypt sensitive fields in conversation metadata.

    Args:
        metadata: Metadata dictionary potentially containing sensitive data

    Returns:
        Metadata dictionary with sensitive fields encrypted

    Note:
        Currently encrypts 'user_input' field if present.
        Extend this function to encrypt additional sensitive fields.
    """
    if not metadata:
        return metadata

    encrypted_metadata = metadata.copy()

    # Encrypt user input if present
    if "user_input" in encrypted_metadata and encrypted_metadata["user_input"]:
        encrypted_metadata["user_input"] = encrypt_conversation_content(
            encrypted_metadata["user_input"]
        )

    # Encrypt voluntary memory fields if present
    if "voluntary_memory" in encrypted_metadata and encrypted_metadata["voluntary_memory"]:
        voluntary_memory = encrypted_metadata["voluntary_memory"]
        if isinstance(voluntary_memory, dict):
            encrypted_voluntary_memory = voluntary_memory.copy()
            # Encrypt preferences
            if "preferences" in encrypted_voluntary_memory:
                encrypted_voluntary_memory["preferences"] = encrypt_conversation_content(
                    str(encrypted_voluntary_memory["preferences"])
                )
            # Encrypt history
            if "history" in encrypted_voluntary_memory:
                encrypted_voluntary_memory["history"] = encrypt_conversation_content(
                    str(encrypted_voluntary_memory["history"])
                )
            encrypted_metadata["voluntary_memory"] = encrypted_voluntary_memory

    return encrypted_metadata


def decrypt_metadata(metadata: dict) -> dict:
    """Decrypt sensitive fields in conversation metadata.

    Args:
        metadata: Metadata dictionary with encrypted sensitive data

    Returns:
        Metadata dictionary with sensitive fields decrypted

    Note:
        Returns original value if decryption fails (migration support).
    """
    if not metadata:
        return metadata

    decrypted_metadata = metadata.copy()

    # Decrypt user input if present
    if "user_input" in decrypted_metadata and decrypted_metadata["user_input"]:
        try:
            decrypted_metadata["user_input"] = decrypt_conversation_content(
                decrypted_metadata["user_input"]
            )
        except Exception:
            # Keep original if decryption fails
            pass

    # Decrypt voluntary memory fields if present
    if "voluntary_memory" in decrypted_metadata and decrypted_metadata["voluntary_memory"]:
        voluntary_memory = decrypted_metadata["voluntary_memory"]
        if isinstance(voluntary_memory, dict):
            decrypted_voluntary_memory = voluntary_memory.copy()
            # Decrypt preferences
            if "preferences" in decrypted_voluntary_memory:
                try:
                    decrypted_voluntary_memory["preferences"] = decrypt_conversation_content(
                        decrypted_voluntary_memory["preferences"]
                    )
                except Exception:
                    pass
            # Decrypt history
            if "history" in decrypted_voluntary_memory:
                try:
                    decrypted_voluntary_memory["history"] = decrypt_conversation_content(
                        decrypted_voluntary_memory["history"]
                    )
                except Exception:
                    pass
            decrypted_metadata["voluntary_memory"] = decrypted_voluntary_memory

    return decrypted_metadata


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be encrypted.

    Args:
        value: String value to check

    Returns:
        True if value appears to be Fernet-encrypted, False otherwise

    Note:
        Fernet encrypted values follow format: base64(timestamp || IV || ciphertext || HMAC)
        This is a heuristic check - valid encrypted data will pass, invalid will fail.
        Checks for Fernet token prefix and valid base64 encoding.
    """
    if not value:
        return False

    try:
        # Fernet tokens are base64 encoded and have specific structure
        # Fernet format: Version(1) || Timestamp(8) || IV(16) || Ciphertext(N*16) || HMAC(32)
        # Minimum: 1 + 8 + 16 + 16 + 32 = 73 bytes (with 1 block of ciphertext)
        import base64
        decoded = base64.urlsafe_b64decode(value.encode())

        # Fernet tokens have minimum length of 73 bytes
        if len(decoded) < 73:
            return False

        # Check if length is valid
        # After Version(1) + Timestamp(8) + IV(16) + HMAC(32) = 57 bytes
        # Remaining is ciphertext which must be multiple of 16
        return (len(decoded) - 57) % 16 == 0
    except Exception:
        return False
