/**
 * Utility to handle encrypted/encoded text display
 */

/**
 * Check if text appears to be encrypted (Fernet, base64, etc.)
 */
export function isEncrypted(text: string): boolean {
  if (!text || typeof text !== 'string') return false;

  // Fernet encryption starts with 'gAAAA'
  if (text.startsWith('gAAAA')) return true;

  // Check for long base64-like strings
  if (text.length > 50 && /^[A-Za-z0-9+/=_-]+$/.test(text)) return true;

  return false;
}

/**
 * Sanitize encrypted text for display
 * Returns a user-friendly placeholder with a unique identifier
 */
export function sanitizeEncryptedText(text: string, maxLength = 50): string {
  if (!text) return '';

  if (isEncrypted(text)) {
    // Create a short unique ID from the encrypted string
    const shortId = text.substring(0, 8);
    return `Topic #${shortId}`;
  }

  // Truncate very long text
  if (text.length > maxLength) {
    return `${text.substring(0, maxLength)}...`;
  }

  return text;
}

/**
 * Format a document name, handling encrypted names
 */
export function formatDocumentName(name: string | null | undefined): string {
  if (!name) return '[Untitled]';

  if (isEncrypted(name)) {
    const shortId = name.substring(0, 8);
    return `Document #${shortId}`;
  }

  return name;
}
