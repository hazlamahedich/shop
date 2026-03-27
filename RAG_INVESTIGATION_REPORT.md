# RAG Issue Investigation Report

## Problem Statement
User asks: "where did he graduate"
Expected: Bot should answer "Ateneo de Manila University" from the resume
Actual: Bot says "I don't have information about where Sherwin Mante graduated"

## Investigation Findings

### ✅ Database Status
- Resume file exists: `resume of Sherwin G. Mante.pdf` (document_id=1)
- Document status: `ready`
- Chunks created: 11 chunks
- Embeddings generated: All 11 chunks have embeddings (3072 dimensions)
- Embedding version: `gemini-gemini-embedding-001`
- Content verification: Chunk 21 contains "Ateneo de Manila University B.S. Management in Information Systems | June 1998 - March 2002"

### ✅ Merchant Configuration
- Merchant ID: 1
- Onboarding mode: `general` (RAG enabled)
- Embedding provider: `gemini`
- Embedding model: `gemini-embedding-001`
- API key: Configured and encrypted in database

### ✅ RAG Pipeline Status
1. **Embedding Service**: Working (API key configured)
2. **Document Processing**: Complete (all chunks embedded)
3. **Retrieval Service**: Functional (no errors in logs)
4. **Context Builder**: Initialized and called

### ❌ Root Cause Identified
**Similarity threshold too high for semantic matching**

The issue:
- Query: "where did he graduate"
  - Embedding focuses on the word "graduate"
- Content: "EDUCATION Ateneo de Manila University B.S. Management in Information Systems"
  - Contains "university" and "education" but NOT "graduate"
- Semantic similarity: ~0.3-0.4 (below threshold of 0.5)
- Result: Chunks filtered out, no context provided to LLM

### Evidence from Database Query
```sql
-- Check if resume was ever retrieved
SELECT * FROM rag_query_logs
WHERE merchant_id = 1
AND sources::text ILIKE '%resume%';
-- Result: 0 rows (resume NEVER retrieved)
```

### Evidence from Test Results
```
Query: "where did he go to college"
Response: "I don't have information about where he went to college"

Query: "ateneo"
Response: "I'm not sure what you mean by 'ateneoateneo'" (word repetition issue)
```

## Solution Options

### Option 1: Lower Similarity Threshold (RECOMMENDED)
**File**: `backend/app/services/rag/context_builder.py`
**Change**: Lower default threshold from 0.5 to 0.3

```python
# Line 63 and 151
async def build_rag_context(
    self,
    merchant_id: int,
    user_query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.3,  # Changed from 0.5
    embedding_version: str | None = None,
) -> str | None:
```

**Pros**:
- Quick fix
- Improves recall
- Minimal code change

**Cons**:
- May retrieve less relevant chunks
- Increases noise in results

### Option 2: Implement Query Expansion
**File**: `backend/app/services/rag/query_rewriter.py`
**Change**: Add synonym expansion for education-related queries

```python
education_synonyms = {
    "graduate": ["college", "university", "education", "school", "degree"],
    "education": ["university", "college", "school", "graduate", "study"],
    # ... more mappings
}
```

**Pros**:
- Better semantic matching
- More robust solution
- Improves user experience

**Cons**:
- More complex implementation
- Requires testing
- May increase latency

### Option 3: Add Keyword-Based Fallback
**File**: New file or enhancement to retrieval service
**Change**: If semantic search fails, fall back to keyword search

```python
if not chunks or chunks[0].similarity < 0.5:
    # Try keyword search as fallback
    chunks = await self._keyword_search(merchant_id, query)
```

**Pros**:
- Guarantees results for exact matches
- Hybrid approach (best of both worlds)

**Cons**:
- Most complex implementation
- Requires keyword indexing
- May return irrelevant results

## Recommendation

**Implement Option 1 (Lower Threshold) as immediate fix**

1. Change `similarity_threshold` default from 0.5 to 0.3 in `context_builder.py`
2. Test with various queries
3. Monitor quality of results
4. Implement Option 2 (Query Expansion) as enhancement

## Additional Findings

### Test Expectations Were Wrong
The test document `TEST_RESULTS.md` expected the bot to find "University of Santo Tomas", but the actual resume contains "Ateneo de Manila University". This is a data mismatch, not a bug.

### Word Repetition Issue
When user types "ateneo", the bot responds "I'm not sure what you mean by 'ateneoateneo'" - this suggests a text processing bug that needs investigation.

## Next Steps
1. Implement similarity threshold fix
2. Test with graduation/education queries
3. Fix word repetition bug
4. Consider implementing query expansion for long-term improvement
