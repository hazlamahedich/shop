#!/usr/bin/env python3
"""Test embedding similarity manually."""
import asyncio
import json
import numpy as np

# Sample chunks from resume
resume_chunks = [
    "EDUCATION Ateneo de Manila University B.S. Management in Information Systems | June 1998 - March 2002",
    "Sherwin G. Mante is an innovative technology leader with over 20 years of experience",
    "PROFESSIONAL EXPERIENCE A3 Automated Solutions Founder & AI Solutions Architect",
]

# Sample queries
queries = [
    "where did he graduate",
    "what university did he attend",
    "education background",
    "ateneo",
    "college",
]

print("=" * 60)
print("Testing Embedding Similarity (Conceptual)")
print("=" * 60)
print()

print("Resume chunks contain:")
for i, chunk in enumerate(resume_chunks, 1):
    print(f"{i}. {chunk[:80]}...")

print()
print("Expected similarity scores:")
print("- Higher for 'ateneo', 'education', 'college' queries")
print("- Lower for 'where did he graduate' (semantic mismatch)")
print()

print("The issue is likely:")
print("1. Query: 'where did he graduate' → Embedding focuses on 'graduate'")
print("2. Content: 'Ateneo de Manila University' → No explicit 'graduate' keyword")
print("3. Similarity score falls below threshold (0.5)")
print()

print("Solution ideas:")
print("1. Lower similarity threshold (currently 0.5)")
print("2. Improve query expansion (add synonyms: graduate→college→university→education)")
print("3. Re-embed content with better model")
print("4. Add keyword-based fallback for specific terms")
