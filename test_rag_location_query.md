# RAG Location Query Investigation

## Issue Summary
The RAG system is not able to answer "where is he located?" even though the location information exists in the resume.

## Investigation Findings

### ✅ What's Working
1. **Resume is processed**: Document status = 'ready'
2. **Location exists in chunk 0**: "504 Friday Road, Saint Joseph Village, P.F. Espiritu 3, Bacoor, Cavite"
3. **All chunks have embeddings**: 67/67 chunks (100% coverage)
4. **Embeddings are correct dimension**: 3072 (gemini-gemini-embedding-001)
5. **Overall match rate is good**: 71.9% (110/153 queries matched)

### 🔍 Root Cause Analysis

The issue is likely due to **semantic embedding mismatch**:

1. **Similarity Threshold**: RetrievalService uses 0.5 threshold
2. **Query vs Content Semantics**:
   - Query: "where is he located"
   - Content: "504 Friday Road, Saint Joseph Village, P.F. Espiritu 3, Bacoor, Cavite"
   - These may not have high semantic similarity in embedding space

3. **Missing Location Queries**: No location-related queries found in logs, suggesting this query type hasn't been tested

## Recommendations

### 1. Lower Similarity Threshold (Immediate Fix)
Change the threshold from 0.5 to 0.3 for better recall:

```python
# In RetrievalService.__init__
SIMILARITY_THRESHOLD = 0.3  # Lowered from 0.5
```

### 2. Improve Chunking Strategy
The chunking algorithm (500-1000 chars) may not preserve context well for address information. Consider:
- Smaller chunks for structured data (addresses, contact info)
- Preserve section boundaries (header sections should be separate chunks)

### 3. Add Query Rewriting
For location queries, rewrite them to be more explicit:
- "where is he located" → "address location contact"
- This improves semantic matching

### 4. Test with Widget
Test the actual widget with these queries:
- "where is he located"
- "what is his address"
- "contact information"
- "location"

## Test Plan

1. **Immediate**: Lower threshold to 0.3
2. **Test**: Run location queries through widget
3. **Monitor**: Check rag_query_logs for match rates
4. **Iterate**: Adjust threshold based on results

## Files to Modify

1. `backend/app/services/rag/retrieval_service.py` - Lower SIMILARITY_THRESHOLD
2. `backend/app/services/knowledge/chunker.py` - Improve chunking for addresses
3. `backend/app/services/rag/query_rewriter.py` - Add location query expansions

