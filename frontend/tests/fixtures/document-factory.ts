/**
 * Document Factory for RAG Pipeline Tests
 *
 * Factory functions for creating test document files
 * Used by Story 8.4: Backend - RAG Service (Document Processing)
 */

import * as fs from 'fs';
import * as path from 'path';
import { faker } from '@faker-js/faker';

/**
 * Document types supported by RAG pipeline
 */
export type DocumentType = 'txt' | 'md' | 'pdf' | 'docx';

/**
 * Document creation options
 */
export interface DocumentOptions {
  filename?: string;
  type?: DocumentType;
  content?: string;
  size?: 'small' | 'medium' | 'large';
  includeMetadata?: boolean;
}

/**
 * Document creation result
 */
export interface CreatedDocument {
  path: string;
  filename: string;
  content: string;
  size: number;
  type: DocumentType;
}

/**
 * Sample FAQ content for testing
 */
const SAMPLE_FAQ_CONTENT = `
# Frequently Asked Questions

## Shipping

**Q: What is your return policy?**
A: We accept returns within 30 days of purchase. Items must be unused and in original packaging.

**Q: How long does shipping take?**
A: Standard shipping takes 3-5 business days. Express shipping is 1-2 business days.

**Q: Do you offer international shipping?**
A: Yes, we ship to over 50 countries. International shipping takes 7-14 business days.

## Products

**Q: What materials are your products made from?**
A: We use sustainable, eco-friendly materials sourced from certified suppliers.

**Q: Do you offer product warranties?**
A: Yes, all products come with a 1-year warranty covering manufacturing defects.

## Payments

**Q: What payment methods do you accept?**
A: We accept Visa, MasterCard, American Express, PayPal, and Apple Pay.

**Q: Is my payment information secure?**
A: Yes, we use industry-standard SSL encryption and never store your full card details.

## Returns

**Q: How do I initiate a return?**
A: Log into your account, go to Orders, and click "Return Item" next to the product.

**Q: How long do refunds take?**
A: Refunds are processed within 5-7 business days after we receive the returned item.
`;

/**
 * Sample product documentation content
 */
const SAMPLE_PRODUCT_DOCS = `
# Product Documentation

## Getting Started

Welcome to our product! This guide will help you get started quickly.

### Installation

1. Download the installer from our website
2. Run the installer and follow the prompts
3. Launch the application and sign in

### Configuration

Configure your settings in the Settings panel:
- Language: English, Spanish, French, German
- Theme: Light, Dark, Auto
- Notifications: Email, Push, SMS

### Features

- **Dashboard**: View your metrics and analytics
- **Reports**: Generate custom reports
- **Integrations**: Connect with third-party services
- **API**: Access our REST API for automation

## Troubleshooting

### Common Issues

**Issue: Application won't start**
Solution: Check that you have the latest version installed and restart your computer.

**Issue: Login fails**
Solution: Reset your password using the "Forgot Password" link.

**Issue: Data not syncing**
Solution: Check your internet connection and try refreshing the page.

## Support

For additional help:
- Email: support@example.com
- Phone: 1-800-123-4567
- Chat: Available 24/7 in the app
`;

/**
 * Create a test document file
 *
 * @param options - Document creation options
 * @returns Created document metadata
 */
export function createTestDocument(options: DocumentOptions = {}): CreatedDocument {
  const {
    filename = `test-doc-${Date.now()}.txt`,
    type = 'txt',
    content,
    size = 'medium',
    includeMetadata = false,
  } = options;

  // Generate content based on size if not provided
  const documentContent = content || generateDocumentContent(size, type);

  // Create temp file path
  const tempDir = path.join(__dirname, '../temp');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  const filePath = path.join(tempDir, filename);

  // Write file
  fs.writeFileSync(filePath, documentContent, 'utf8');

  // Get file stats
  const stats = fs.statSync(filePath);

  return {
    path: filePath,
    filename,
    content: documentContent,
    size: stats.size,
    type,
  };
}

/**
 * Generate document content based on size
 */
function generateDocumentContent(size: 'small' | 'medium' | 'large', type: DocumentType): string {
  const baseContent = SAMPLE_FAQ_CONTENT;

  switch (size) {
    case 'small':
      return baseContent.slice(0, 500); // ~500 bytes

    case 'medium':
      return baseContent; // ~2KB

    case 'large':
      // Repeat content to create ~10KB file
      return Array(5).fill(baseContent).join('\n\n---\n\n');

    default:
      return baseContent;
  }
}

/**
 * Create a document with custom FAQ content
 *
 * @param faqs - Array of Q&A pairs
 * @returns Created document metadata
 */
export function createFAQDocument(
  faqs: Array<{ question: string; answer: string }> = []
): CreatedDocument {
  const defaultFAQs = [
    { question: 'What is your return policy?', answer: '30 days, unused items only.' },
    { question: 'How long does shipping take?', answer: '3-5 business days.' },
  ];

  const faqContent = (faqs.length > 0 ? faqs : defaultFAQs)
    .map(
      (faq) => `
**Q: ${faq.question}**
A: ${faq.answer}
`
    )
    .join('\n');

  const content = `# FAQ\n\n${faqContent}`;

  return createTestDocument({
    filename: `faq-${Date.now()}.txt`,
    content,
  });
}

/**
 * Create a product documentation file
 *
 * @param sections - Custom sections to include
 * @returns Created document metadata
 */
export function createProductDocumentation(
  sections: string[] = []
): CreatedDocument {
  const content =
    sections.length > 0 ? sections.join('\n\n') : SAMPLE_PRODUCT_DOCS;

  return createTestDocument({
    filename: `product-docs-${Date.now()}.md`,
    type: 'md',
    content,
  });
}

/**
 * Create a large document for performance testing
 *
 * @param targetSizeKB - Target size in kilobytes (default: 1024 = 1MB)
 * @returns Created document metadata
 */
export function createLargeDocument(targetSizeKB: number = 1024): CreatedDocument {
  const chunk = SAMPLE_FAQ_CONTENT;
  const chunkSizeKB = Buffer.byteLength(chunk, 'utf8') / 1024;
  const repetitions = Math.ceil(targetSizeKB / chunkSizeKB);

  const content = Array(repetitions)
    .fill(chunk)
    .join('\n\n--- Page Break ---\n\n');

  return createTestDocument({
    filename: `large-doc-${targetSizeKB}kb-${Date.now()}.txt`,
    content,
    size: 'large',
  });
}

/**
 * Create a document with specific content for similarity testing
 *
 * @param keywords - Keywords to include in document
 * @returns Created document metadata
 */
export function createKeywordDocument(keywords: string[] = []): CreatedDocument {
  const content = `
# Document with Keywords

This document contains specific keywords for testing vector similarity search.

Keywords: ${keywords.join(', ')}

## Content

${keywords.map((keyword) => `This section discusses ${keyword} in detail.`).join('\n\n')}

## Summary

The keywords mentioned in this document are: ${keywords.join(', ')}.
`;

  return createTestDocument({
    filename: `keyword-doc-${Date.now()}.txt`,
    content,
  });
}

/**
 * Clean up test document
 *
 * @param documentPath - Path to document file
 */
export function cleanupTestDocument(documentPath: string): void {
  if (fs.existsSync(documentPath)) {
    fs.unlinkSync(documentPath);
  }
}

/**
 * Clean up all test documents in temp directory
 */
export function cleanupAllTestDocuments(): void {
  const tempDir = path.join(__dirname, '../temp');

  if (fs.existsSync(tempDir)) {
    const files = fs.readdirSync(tempDir);
    files.forEach((file) => {
      fs.unlinkSync(path.join(tempDir, file));
    });
  }
}
