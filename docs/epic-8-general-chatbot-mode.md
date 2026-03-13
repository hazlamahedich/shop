# Epic 8: General Chatbot Mode

Status: in_progress

## Overview

Enable the chatbot to function as a general-purpose AI assistant without requiring Shopify integration. Facebook is **optional** in both modes - it's a communication channel, not a mode requirement.

This opens up new market segments: customer support bots, lead generation, knowledge base Q&A, and any website that needs conversational AI.

## Mode Definitions

| Mode | Shopify | Facebook | What You Get |
|------|---------|----------|--------------|
| **General** | ❌ Not connected | Optional | General chat, FAQ, Knowledge Base (RAG), human handoff |
| **E-commerce** | ✅ Connected | Optional | Everything in General + products, cart, checkout, orders |

**Key Insight:** Facebook Messenger is a **channel**, not a mode. Connect it in either mode to enable Facebook chat.

## Epic Goal

Enable merchants to:
1. Choose "General Chatbot" or "E-commerce" mode during onboarding
2. Use the widget embedded on any website without Shopify
3. Upload documents for knowledge base Q&A (RAG)
4. Switch between general and e-commerce modes at any time
5. Optionally connect Facebook in either mode for Messenger chat

## Requirements Inventory

### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-8.1 | System must support `onboarding_mode` field on merchant (`general` or `ecommerce`) |
| FR-8.2 | Onboarding must offer mode selection before showing integration steps |
| FR-8.3 | General Chatbot Mode must skip Shopify/Facebook connection steps |
| FR-8.4 | System must support Knowledge Base document upload (PDF, TXT, MD, DOCX) |
| FR-8.5 | System must perform RAG retrieval from KB when answering questions |
| FR-8.6 | Merchants must be able to switch modes from Settings page |
| FR-8.7 | Widget must work in General Chatbot Mode without Shopify dependencies |

### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-8.1 | Document upload must support files up to 10MB |
| NFR-8.2 | RAG retrieval must complete in <500ms |
| NFR-8.3 | All mode changes must be logged for audit |

---

## Story List

| Story | Title | Priority | Est. Time | Dependencies | Status |
|-------|-------|----------|-----------|--------------|--------|
| 8.1 | Backend: Merchant Mode Field & API | P0 | 1.5h | None | ✅ |
| 8.2 | Backend: Onboarding Mode Selection | P0 | 1h | 8.1 | ✅ |
| 8.3 | Backend: Knowledge Base Models & Storage | P0 | 2h | 8.1 | ✅ |
| 8.4 | Backend: RAG Service (Document Processing) | P1 | 3h | 8.3 | ✅ |
| 8.5 | Backend: RAG Integration in Conversation | P1 | 2h | 8.4 | ✅ |
| 8.6 | Frontend: Onboarding Mode Selection UI | P0 | 2h | 8.2 | ✅ |
| 8.7 | Frontend: Settings Mode Toggle | P1 | 1.5h | 8.1 | |
| 8.8 | Frontend: Knowledge Base Page | P1 | 3h | 8.3 | ✅ |
| 8.9 | Testing & Quality Assurance | P1 | 2h | All | ✅ |
| 8.10 | Frontend: Dashboard Mode-Aware Widgets | P1 | 2h | 8.1 | |
| 8.11 | LLM Embedding Provider Integration & Re-embedding | P1 | 3h | 8.1, 8.4 | |

**Total: ~23 hours**

---

## Story 8.1: Backend - Merchant Mode Field & API

**Status: ✅ COMPLETE** (2026-03-11)

### User Story

As a **merchant**, I want my account to have a mode setting, so the system knows whether I'm using General chatbot or e-commerce features.

### Acceptance Criteria

**AC1:** ✅ Given a new merchant registers, when the account is created, then `onboarding_mode` defaults to `"general"`

**AC2:** ✅ Given an authenticated merchant, when they request their profile, then `onboarding_mode` is included in the response

**AC3:** ✅ Given an authenticated merchant, when they update their mode via API, then the mode is persisted and logged

### Tasks

- [x] Add `onboarding_mode` field to Merchant model (AC: 1)
  - [x] Update `backend/app/models/merchant.py`
  - [x] Add field: `onboarding_mode: Mapped[str]` with enum values
  - [x] Create `OnboardingMode` enum class
- [x] Create database migration (AC: 1)
  - [x] Create `alembic/versions/XXX_add_onboarding_mode.py`
  - [x] Default value: `'general'`
- [x] Update merchant schemas (AC: 2, 3)
  - [x] Update `backend/app/api/auth.py` - Added `onboarding_mode` to `MerchantResponse`
  - [x] Add `onboarding_mode` to `MerchantResponse`
- [x] Add mode update endpoint (AC: 3)
  - [x] Update `backend/app/api/merchant.py`
  - [x] Add `GET /api/merchant/mode` and `PATCH /api/merchant/mode` endpoints
  - [x] Log mode changes with timestamp
- [x] Add CSRF bypass for mode endpoint (AC: 3)
  - [x] Update `backend/app/middleware/auth.py` - Added `/api/merchant/mode` to bypass list
- [x] Write comprehensive tests
  - [x] Create `backend/tests/api/test_merchant_mode.py` - 12 tests, all passing

### Dev Notes

- **CSRF**: Added `/api/merchant/mode` to CSRF bypass in `auth.py`
- **Python Version**: Used `datetime.timezone.utc` (NOT `datetime.UTC`)
- **Default**: New merchants default to `general` mode
- **Bearer Token Support**: Updated `/api/v1/auth/me` to accept Bearer tokens for API testing

### API Endpoints

```
GET    /api/v1/auth/me                # Returns onboarding_mode in merchant object
GET    /api/merchant/mode             # Returns { data: { onboardingMode: "general" | "ecommerce" } }
PATCH  /api/merchant/mode             # Update mode { "mode": "general" | "ecommerce" }
```

### Implementation Notes

1. **Model**: `onboarding_mode` field already existed in `Merchant` model with default `"general"`
2. **Schema**: Added `onboarding_mode: str = "general"` to `MerchantResponse` in `auth.py`
3. **API**: Mode endpoints existed at `/api/merchant/mode` (not `/api/v1/merchants/mode`)
4. **Auth**: Updated `/api/v1/auth/me` to support Bearer tokens and skip session validation in test mode
5. **Tests**: Created comprehensive test suite covering all acceptance criteria

### Files Created

```
backend/tests/api/test_merchant_mode.py
```

### Files Modified

```
backend/app/api/auth.py              # Added onboarding_mode to MerchantResponse, Bearer token support
backend/app/api/merchant.py          # Mode endpoints already existed (lines 1166-1267)
backend/app/middleware/auth.py       # Added /api/merchant/mode to CSRF bypass
```

---

## Story 8.2: Backend - Onboarding Mode Selection

**Status: ✅ COMPLETE** (2026-03-11)

### User Story

As a **new user registering**, I want to choose my use case during registration, so I'm not forced through irrelevant setup steps.

### Acceptance Criteria

**AC1:** Given the registration endpoint, when `mode` is provided, then it's stored on the merchant

**AC2:** Given a merchant with `mode=General`, when auth status is returned, then `has_store_connected=false` and `has_facebook_connected=false`

**AC3:** Given mode is not provided, when registering, then default to `"General"`

### Tasks

- [x] Update registration schema (AC: 1, 3)
  - [x] Update `backend/app/schemas/auth.py`
  - [x] Add optional `mode: Optional[str]` to `RegisterRequest`
- [x] Update registration endpoint (AC: 1, 3)
  - [x] Update `backend/app/api/auth.py`
  - [x] Store mode on merchant creation
  - [x] Default to `"General"` if not provided
- [x] Update auth status response (AC: 2)
  - [x] Update `backend/app/api/auth.py`
  - [x] Include `onboarding_mode` in login/status response
  - [x] Derive `has_store_connected` and `has_facebook_connected` from mode + integrations

### Dev Notes

- **Backward Compatible**: Existing merchants without mode field should be treated as `ecommerce`
- **Migration**: Set existing merchants to `ecommerce` mode

### Files to Modify

```
backend/app/schemas/auth.py
backend/app/api/auth.py
```

### Test Coverage

**Status:** ✅ COMPLETE

**Test File:** `backend/tests/api/test_merchant_mode.py` (751 lines)

**Test Framework:** pytest (API-level tests)

**Coverage Summary:**
- **Total Tests:** 11 (Story 8.2 specific)
- **Test ID Format:** 8.2-API-XXX
- **Execution Time:** ~9 seconds
- **Test Level:** API (appropriate for backend story)

**Acceptance Criteria → Test Mapping:**

| AC | Test Coverage | Test IDs | Priority | Status |
|----|---------------|----------|----------|--------|
| **AC1** | Mode stored on registration | 8.2-API-001, 8.2-API-002 | P0 | ✅ Pass |
| **AC2** | Connection flags reflect mode | 8.2-API-007, 8.2-API-009, 8.2-API-010 | P0/P1 | ✅ Pass |
| **AC3** | Default to "General" | 8.2-API-003 | P0 | ✅ Pass |
| **AC4** | Flags in auth responses | 8.2-API-005, 8.2-API-006 | P0 | ✅ Pass |

**Test Distribution by Priority:**

| Priority | Count | Tests | Coverage |
|----------|-------|-------|----------|
| **P0 (Critical)** | 8 | Registration happy paths, connection flags | AC1, AC2, AC3, AC4 |
| **P1 (High)** | 2 | Integration scenarios (Shopify, Facebook) | AC2 edge cases |
| **P2 (Medium)** | 1 | Input validation (invalid mode) | Error handling |

**Test Quality Metrics:**

- ✅ **Deterministic:** No hard waits, uses explicit assertions
- ✅ **Isolated:** Each test uses unique email addresses via faker
- ✅ **Explicit Assertions:** All expectations visible in test bodies
- ✅ **< 300 lines:** Test classes appropriately scoped
- ✅ **Self-Cleaning:** Tests use fixtures with proper cleanup
- ✅ **Parallel-Safe:** No shared state between tests
- ✅ **API-Level:** Fast execution, no browser overhead

**Edge Cases Covered:**

1. ✅ Registration with `mode='general'` → stores correctly (8.2-API-001)
2. ✅ Registration with `mode='ecommerce'` → stores correctly (8.2-API-002)
3. ✅ Registration without mode → defaults to 'general' (8.2-API-003)
4. ✅ Registration with invalid mode → returns 422 (8.2-API-004)
5. ✅ General mode merchant → has false connection flags (8.2-API-007)
6. ✅ E-commerce mode + Shopify → has true store flag (8.2-API-009)
7. ✅ Any mode + Facebook → has true facebook flag (8.2-API-010)

**Test Automation Workflow:**

- **Workflow:** TEA Test Architect - Automate v5.0
- **Execution Mode:** BMad-Integrated
- **Analysis Date:** 2026-03-11
- **Result:** No new tests required (existing coverage comprehensive)
- **Rationale:** All acceptance criteria have P0 test coverage, edge cases covered at P1/P2

**Execution Commands:**

```bash
# Run Story 8.2 tests
cd backend
source venv/bin/activate
python -m pytest tests/api/test_merchant_mode.py -v

# Run specific test class
python -m pytest tests/api/test_merchant_mode.py::TestRegistrationWithMode -v

# Run P0 tests only
python -m pytest tests/api/test_merchant_mode.py -v -m p0
```

**Integration Notes:**

- Tests integrated with Story 8.1 (Merchant Mode API)
- Shared fixtures with other auth flow tests
- CSRF bypass configured for mode endpoint (verified in test)
- Database cleanup handled automatically by test fixtures

---

## Story 8.3: Backend - Knowledge Base Models & Storage

**Status: ✅ COMPLETE** (2026-03-11)

### User Story
As a **merchant**, I want to upload documents that the chatbot can learn from, so it can answer questions about my business.

### Acceptance Criteria

**AC1:** Given an authenticated merchant, when they upload a document (PDF/TXT/MD/DOCX), then it's stored with metadata (filename, size, type, created_at, status)

**AC2:** Given a document upload, when the file is processed, then it's chunked into segments (500-1000 chars) for embedding

**AC3:** Given a merchant requests their documents, then all their documents are returned with processing status

**AC4:** Given a document, when delete is requested, then the document and all its chunks are removed

### Tasks

- [x] Create KnowledgeDocument model (AC: 1)
  - [x] Create `backend/app/models/knowledge_base.py`
  - [x] Fields: id, merchant_id, filename, file_type, file_size, status, error_message, created_at, updated_at
- [x] Create DocumentChunk model (AC: 2)
  - [x] Add to `backend/app/models/knowledge_base.py`
  - [x] Fields: id, document_id, chunk_index, content, embedding (vector), created_at
- [x] Create database migration (AC: 1, 2)
  - [x] Create `alembic/versions/XXX_add_knowledge_base.py`
  - [x] Enable pgvector extension
  - [x] Create vector index for similarity search
- [x] Create knowledge base schemas (AC: 1, 3)
  - [x] Create `backend/app/schemas/knowledge_base.py`
  - [x] `DocumentUploadResponse`, `DocumentListResponse`, `DocumentDetail`
- [x] Create document upload endpoint (AC: 1)
  - [x] Create `backend/app/api/knowledge_base.py`
  - [x] `POST /api/knowledge-base/upload`
  - [x] Validate file type and size (max 10MB)
  - [x] Store file and create document record
- [x] Create document chunking service (AC: 2)
  - [x] Create `backend/app/services/knowledge/chunker.py`
  - [x] Split documents into 500-1000 char chunks with overlap
  - [x] Handle different file types (PDF, TXT, MD, DOCX)
- [x] Create document list/delete endpoints (AC: 3, 4)
  - [x] Add to `backend/app/api/knowledge_base.py`
  - [x] `GET /api/knowledge-base`, `DELETE /api/knowledge-base/{id}`
- [x] Add CSRF bypass for new endpoints (AC: 1, 3, 4)
  - [x] Update `backend/app/middleware/auth.py`
- [x] Write comprehensive tests
  - [x] Create `backend/tests/api/test_knowledge_base.py` - 21 tests, all passing

### Dev Notes

- **pgvector**: Requires PostgreSQL extension for vector similarity search
- **File Storage**: Store files in `uploads/knowledge-base/{merchant_id}/` directory
- **Chunking Strategy**: 500-1000 chars with 100 char overlap for context continuity
- **Supported Types**: PDF (PyPDF2), TXT, MD (plain text), DOCX (python-docx)

### API Endpoints

```
POST   /api/knowledge-base/upload           # Upload document
GET    /api/knowledge-base                   # List documents
GET    /api/knowledge-base/{id}              # Get document detail
DELETE /api/knowledge-base/{id}              # Delete document
```

### Files to Create

```
backend/app/models/knowledge_base.py
backend/app/schemas/knowledge_base.py
backend/app/api/knowledge_base.py
backend/app/services/knowledge/__init__.py
backend/app/services/knowledge/chunker.py
backend/alembic/versions/XXX_add_knowledge_base.py
backend/tests/api/test_knowledge_base.py
```

### Files Created (Actual)

```
backend/app/models/knowledge_base.py         # KnowledgeDocument + DocumentChunk models
backend/app/schemas/knowledge_base.py        # Pydantic schemas for API
backend/app/api/knowledge_base.py            # Upload, list, delete endpoints
backend/app/services/knowledge/__init__.py    # Service module init
backend/app/services/knowledge/chunker.py    # Document chunking service
backend/alembic/versions/add_knowledge_base.py  # Database migration
backend/tests/api/test_knowledge_base.py     # 21 comprehensive tests
```

### Files to Modify

```
backend/app/middleware/auth.py
backend/app/main.py (add router)
```

### Files Modified (Actual)

```
backend/app/middleware/auth.py    # Added /api/knowledge-base/* to CSRF bypass
backend/app/main.py               # Added knowledge_base router
backend/tests/api/test_knowledge_base.py  # Extended with 7 new tests (+274 lines)
```

### Test Coverage

**Status:** ✅ COMPLETE

**Test File:** `backend/tests/api/test_knowledge_base.py` (653 lines)

**Test Framework:** pytest (API-level tests)

**Coverage Summary:**
- **Total Tests:** 21 (14 existing + 7 new)
- **Test ID Format:** 8.3-API-XXX, 8.3-UNIT-XXX
- **Execution Time:** ~4.2 seconds
- **Test Level:** API + Unit (appropriate for backend story)

**Acceptance Criteria → Test Mapping:**

| AC | Test Coverage | Test IDs | Priority | Status |
|----|---------------|----------|----------|--------|
| **AC1** | Document upload (all types) | test_upload_document_pdf, test_upload_document_txt, test_upload_document_md, test_upload_document_docx | P0 | ✅ Pass |
| **AC2** | Document chunking (500-1000 chars) | test_chunk_text_file, test_chunk_markdown_file, test_chunk_size_bounds, test_chunk_docx_file, test_chunk_quality_validation, test_chunk_empty_file | P1 | ✅ Pass |
| **AC3** | Document list endpoint | test_list_documents, test_list_documents_empty | P0/P2 | ✅ Pass |
| **AC4** | Document deletion with chunks | test_delete_document, test_delete_nonexistent_document | P0/P1 | ✅ Pass |

**Security Tests:**

| Test ID | Priority | Description | Status |
|---------|----------|-------------|--------|
| test_unauthorized_access | P0 | All endpoints require authentication | ✅ Pass |
| test_cross_merchant_isolation | P0 | IDOR prevention (merchants can't access others' docs) | ✅ Pass |

**Test Distribution by Priority:**

| Priority | Count | Tests | Coverage |
|----------|-------|-------|----------|
| **P0 (Critical)** | 11 | Upload (4), List (1), Delete (1), Security (2), Chunking basics (3) | All ACs |
| **P1 (High)** | 7 | Chunking edge cases (3), Error handling (4) | Edge cases |
| **P2 (Medium)** | 3 | Empty list, Empty file, Quality validation | Edge cases |

**Test Quality Metrics:**

- ✅ **Deterministic:** No hard waits, uses explicit assertions
- ✅ **Isolated:** Each test uses unique merchant data
- ✅ **Self-Cleaning:** Database reset before each test
- ✅ **Parallel-Safe:** No shared state between tests
- ✅ **Fast Execution:** < 5 seconds total

**Edge Cases Covered:**

1. ✅ PDF file upload → stored with metadata (AC1)
2. ✅ TXT file upload → stored with metadata (AC1)
3. ✅ MD file upload → stored with metadata (AC1)
4. ✅ DOCX file upload → stored with metadata (AC1)
5. ✅ Invalid file type → returns 400 error
6. ✅ File too large (>10MB) → returns 413 error
7. ✅ Empty file → chunking raises error
8. ✅ Whitespace-only chunks → filtered out
9. ✅ Unauthorized access → returns 401 on all endpoints
10. ✅ Cross-merchant access → returns 404 (IDOR prevention)

**Test Automation Workflow:**

- **Workflow:** TEA Test Architect - Automate v5.0
- **Execution Mode:** BMad-Integrated
- **Analysis Date:** 2026-03-11
- **Result:** 7 new tests added (existing 14 tests preserved)
- **Rationale:** All acceptance criteria have P0 test coverage, security tests added, edge cases covered

**Execution Commands:**

```bash
# Run Story 8.3 tests
cd backend
source venv/bin/activate
python -m pytest tests/api/test_knowledge_base.py -v

# Run P0 tests only
python -m pytest tests/api/test_knowledge_base.py -v -k "P0"

# Run security tests
python -m pytest tests/api/test_knowledge_base.py -v -k "unauthorized or isolation"
```

**Files Created:**

```
backend/tests/api/test_knowledge_base.py (updated, +274 lines)
_bmad-output/automation-summary-story-8-3-2026-03-11.md
```

---

## Story 8.4: Backend - RAG Service (Document Processing)

**Status: ✅ COMPLETE** (2026-03-12)

### User Story

As a **chatbot user**, I want the bot to answer questions based on uploaded documents, so I get accurate, business-specific information.

### Acceptance Criteria

**AC1:** ✅ Given a document is uploaded, when processing completes, then embeddings are generated for each chunk using the configured LLM provider

**AC2:** ✅ Given a user question, when RAG retrieval runs, then the top 5 most relevant chunks are returned with similarity scores

**AC3:** ✅ Given no relevant documents exist (similarity < 0.7), when retrieval runs, then an empty list is returned (no hallucination)

**AC4:** ✅ Given document processing fails, when error occurs, then the document status is updated to "error" with error message

### Tasks

- [x] Create embedding service (AC: 1)
  - [x] Create `backend/app/services/rag/embedding_service.py`
  - [x] Generate embeddings using configured LLM provider
  - [x] Support OpenAI, Ollama embedding models (Anthropic rejected - no embedding API)
  - [x] Batch embedding for multiple chunks
- [x] Create retrieval service (AC: 2, 3)
  - [x] Create `backend/app/services/rag/retrieval_service.py`
  - [x] Vector similarity search using pgvector
  - [x] Return top-k chunks with similarity threshold (0.7)
  - [x] Filter by merchant_id for multi-tenant isolation
- [x] Create document processor (AC: 1, 4)
  - [x] Create `backend/app/services/rag/document_processor.py`
  - [x] Orchestrate: upload → chunk → embed → store
  - [x] Update document status throughout pipeline
  - [x] Handle errors gracefully with status update
- [x] Create background task for processing (AC: 1)
  - [x] Create `backend/app/services/rag/processing_task.py`
  - [x] Async processing of uploaded documents
  - [x] Update document status: pending → processing → ready/error
- [x] Integrate with knowledge base API (AC: 1, 4)
  - [x] Update `backend/app/api/knowledge_base.py`
  - [x] Trigger background processing on upload

### Dev Notes

- **Embedding Model**: Use `text-embedding-3-small` (OpenAI) or equivalent
- **Embedding Dimension**: 1536 (OpenAI) or 768 (local models)
- **Similarity Metric**: Cosine similarity
- **Threshold**: 0.7 minimum similarity (tunable per merchant)
- **Performance Target**: <500ms for retrieval

### Files Created

```
backend/app/services/rag/__init__.py
backend/app/services/rag/embedding_service.py
backend/app/services/rag/retrieval_service.py
backend/app/services/rag/document_processor.py
backend/app/services/rag/processing_task.py
```

### Test Coverage

**Status:** ✅ COMPLETE

**Test Files:**
- `backend/tests/services/rag/test_embedding_service.py` (19 tests, 360 lines)
- `backend/tests/services/rag/test_retrieval_service.py` (13 tests, 334 lines)
- `backend/tests/services/rag/test_document_processor.py` (12 tests, 377 lines)
- `backend/tests/services/rag/test_processing_task.py` (9 tests, 320 lines)
- `backend/tests/integration/test_rag_pipeline.py` (7 tests, 237 lines)

**Total Tests:** 60 (53 unit + 7 integration)
**Execution Time:** 3.20s
**All Passing:** ✅

**Acceptance Criteria → Test Mapping:**

| AC | Test Coverage | Test IDs | Status |
|----|---------------|----------|--------|
| AC1 | Embedding generation for chunks | test_process_document_success, test_embed_texts_openai_success, test_embed_texts_ollama_success | ✅ Pass |
| AC2 | Top 5 chunks with similarity scores | test_retrieve_returns_top_k_chunks | ✅ Pass |
| AC3 | Empty list when similarity < 0.7 | test_retrieve_filters_by_threshold | ✅ Pass |
| AC4 | Error status update on failure | test_process_document_chunking_failure, test_process_document_embedding_failure | ✅ Pass |

**Execution Commands:**

```bash
# Run all RAG tests
cd backend
source venv/bin/activate
python -m pytest tests/services/rag/ tests/integration/test_rag_pipeline.py -v

# Results: 60 passed in 3.20s
```

---

## Story 8.5: Backend - RAG Integration in Conversation

**Status: ✅ COMPLETE** (2026-03-12)

### User Story

As a **user chatting with the bot**, I want answers grounded in the merchant's documents, so the information is accurate and relevant.

### Acceptance Criteria

**AC1:** ✅ Given a merchant has uploaded documents, when a user asks a question, then relevant document chunks are retrieved and included in the LLM context

**AC2:** ✅ Given RAG context is available, when the LLM generates a response, then it cites the source document name

**AC3:** ✅ Given General Chatbot Mode with e-commerce intent detected (product search, cart, checkout), when the bot responds, then a graceful fallback message is shown

**AC4:** ✅ Given RAG retrieval takes >500ms, when timeout occurs, then proceed without RAG context (graceful degradation)

### Tasks

- [x] Create RAG context builder (AC: 1)
  - [x] Create `backend/app/services/rag/context_builder.py`
  - [x] Retrieve relevant chunks for user query
  - [x] Format chunks as context string with source citations
- [x] Integrate with UnifiedConversationService (AC: 1, 2)
  - [x] Update `backend/app/services/conversation/unified_conversation_service.py`
  - [x] Call RAG retrieval before LLM call for General merchants
  - [x] Inject context into system prompt
  - [x] Add source citation instruction to prompt
- [x] Add General Chatbot Mode fallback handlers (AC: 3)
  - [x] Create `backend/app/services/conversation/handlers/general_mode_fallback.py`
  - [x] Return friendly message for e-commerce intents in General Chatbot Mode
  - [x] Added personality-aware fallback templates to response_formatter.py
- [x] Add timeout handling (AC: 4)
  - [x] Add asyncio timeout to RAG retrieval (500ms)
  - [x] Log timeout events for monitoring
  - [x] Proceed with LLM call without RAG context

### Dev Notes

- **Context Injection**: Prepend RAG context to system prompt
- **Citation Format**: "According to [Document Name], ..."
- **Timeout**: 500ms max for retrieval
- **Logging**: Track RAG usage and performance metrics

### Test Coverage

**Status:** ✅ COMPLETE (2026-03-12)

**Test Files:**
- `backend/tests/services/rag/test_context_builder.py` (17 tests)
- `backend/tests/integration/test_rag_conversation.py` (6 tests)

**Total Tests:** 23 (17 unit + 6 integration)
**Execution Time:** 1.19s
**All Passing:** ✅

**Acceptance Criteria → Test Mapping:**

| AC | Test Coverage | Test IDs | Status |
|----|---------------|----------|--------|
| AC1 | RAG context injected | test_general_mode_with_documents_rag_injected | ✅ Pass |
| AC2 | Source citations | test_response_includes_source_citation | ✅ Pass |
| AC3 | E-commerce fallback | test_ecommerce_intent_in_general_mode_fallback | ✅ Pass |
| AC4 | Timeout handling | test_retrieval_timeout, test_rag_retrieval_timeout_graceful_degradation | ✅ Pass |

**Execution Commands:**

```bash
cd backend
source venv/bin/activate
python -m pytest tests/services/rag/test_context_builder.py tests/integration/test_rag_conversation.py -v

# Results: 23 passed in 1.19s
```

### Files Created

```
backend/app/services/rag/context_builder.py
backend/app/services/conversation/handlers/general_mode_fallback.py
backend/tests/services/rag/test_context_builder.py
backend/tests/integration/test_rag_conversation.py
```

### Files Modified

```
backend/app/services/conversation/unified_conversation_service.py
backend/app/services/conversation/handlers/llm_handler.py
backend/app/services/personality/response_formatter.py
```

---

## Story 8.6: Frontend - Onboarding Mode Selection UI

**Status: ✅ COMPLETE** (2026-03-12)

### User Story

As a **new user**, I want a visual way to choose my use case during onboarding, so I understand what I'm signing up for.

### Acceptance Criteria

**AC1:** ✅ Given the onboarding page, when it loads, then a mode selection screen appears first with two options: "Chatbot Only" and "E-commerce"

**AC2:** ✅ Given "Chatbot Only" is selected, when continuing, then Shopify/Facebook steps are skipped and only LLM configuration is shown

**AC3:** ✅ Given "E-commerce" is selected, when continuing, then the existing 3-step wizard is shown

**AC4:** ✅ Given mode selection, when the user proceeds, then the mode is sent to the registration/onboarding API

### Tasks

- [x] Create mode selection component (AC: 1)
  - [x] Create `frontend/src/components/onboarding/ModeSelection.tsx`
  - [x] Two card options with icons and descriptions
  - [x] Highlighted selection state
- [x] Update onboarding flow (AC: 2, 3)
  - [x] Update `frontend/src/pages/Onboarding.tsx`
  - [x] Add mode selection as Step 0
  - [x] Conditionally show/hide integration steps based on mode
- [x] Update onboarding store (AC: 4)
  - [x] Update `frontend/src/stores/onboardingStore.ts`
  - [x] Add `onboardingMode` state
  - [x] Persist mode selection
- [x] Update registration API call (AC: 4)
  - [x] Update `frontend/src/services/auth.ts`
  - [x] Include mode in registration request

### Dev Notes

- **UI Framework**: React 18 + TypeScript + Tailwind CSS
- **Icons**: Use Lucide icons (Bot, ShoppingCart)
- **Animations**: Smooth transitions between steps

### Mode Selection Cards

**Chatbot Only:**
- Icon: Bot
- Title: "AI Chatbot"
- Description: "Customer support, FAQ, knowledge base Q&A"
- Features: "No store required", "Quick setup", "Embed anywhere"

**E-commerce:**
- Icon: ShoppingCart
- Title: "E-commerce Assistant"
- Description: "Product search, cart, checkout, order tracking"
- Features: "Shopify integration", "Facebook Messenger", "Full shopping experience"

### Files to Create

```
frontend/src/components/onboarding/ModeSelection.tsx
```

### Files to Modify

```
frontend/src/pages/Onboarding.tsx
frontend/src/stores/onboardingStore.ts
frontend/src/services/auth.ts
```

### Test Coverage

**Status:** ✅ COMPLETE (2026-03-12)

**Test Files:**
- `frontend/tests/api/story-8-6-onboarding-mode.spec.ts` (6 tests) - API-level tests
- `frontend/tests/e2e/story-8-6/mode-selection.spec.ts` (10 tests) - Core flow tests
- `frontend/tests/e2e/story-8-6/accessibility.spec.ts` (4 tests) - A11y tests
- `frontend/tests/e2e/story-8-6/visual-design.spec.ts` (3 tests) - Visual feedback tests
- `frontend/tests/e2e/story-8-6/error-handling.spec.ts` (2 tests - fixme) - Error handling tests
- `frontend/tests/e2e/story-8-6/pageobjects/onboarding-mode.po.ts` - Shared PageObject

**Final Results:** 17 passed, 2 skipped (fixme)
**Test Framework:** Playwright
**Execution Time:** ~12s

**Acceptance Criteria → Test Mapping:**

| AC | Test Coverage | Test IDs | Priority | Status |
|----|---------------|----------|----------|--------|
| **AC1** | Mode selection appears with two options | 8.6-E2E-001, 8.6-E2E-002 | P0 | ✅ Pass |
| **AC2** | General mode skips Shopify/Facebook | 8.6-E2E-003, 8.6-E2E-005 | P0 | ✅ Pass |
| **AC3** | E-commerce mode shows all steps | 8.6-E2E-004, 8.6-E2E-006 | P0 | ✅ Pass |
| **AC4** | Mode persisted to localStorage | 8.6-E2E-007, 8.6-E2E-010 | P1 | ✅ Pass |

**Test Distribution by Priority:**

| Priority | Count | Tests | Coverage |
|----------|-------|-------|----------|
| **P0 (Critical)** | 6 | Smoke tests, core flow, AC validation | All ACs |
| **P1 (High)** | 8 | Persistence, keyboard nav, accessibility | UX quality |
| **P2 (Medium)** | 3 | Visual design, icons, descriptions | Polish |

**Test Quality Metrics:**

- ✅ **Deterministic:** All hard waits replaced with explicit assertions
- ✅ **Isolated:** Each test uses proper cleanup with `beforeEach`
- ✅ **Explicit Assertions:** All expectations visible in test bodies
- ✅ **< 300 lines:** All files under 300 lines
- ✅ **Self-Cleaning:** Tests clear localStorage in beforeEach
- ✅ **Serial Execution:** Tests run serially to avoid state conflicts
- ✅ **Test IDs:** Formal IDs added (8.6-E2E-001 to 8.6-E2E-010)
- ✅ **PageObject:** Shared selectors extracted to `onboarding-mode.po.ts`

**Key Fixes Applied During Testing:**

1. **RouteGuards.tsx** (line 42): Changed `/onboarding/` to `/onboarding` to allow route without trailing slash
2. **onboarding.ts service**: Updated `getOnboardingMode()` to return `null` when no mode exists (instead of defaulting)
3. **onboardingStore.ts**: 
   - Fixed `loadFromStorage()` to not override null mode with default
   - Added `saveToStorage()` call when mode is loaded from backend
4. **Test fixes**:
   - Corrected localStorage key from `onboarding-storage` to `shop_onboarding_prerequisites`
   - Fixed ARIA attribute from `aria-selected` to `aria-pressed`
   - Fixed h1 selector to use `.nth(1)` for correct heading

**Edge Cases Covered:**

1. ✅ Mode selection appears first (8.6-E2E-001)
2. ✅ Two mode options displayed (8.6-E2E-002)
3. ✅ General mode shows fewer prerequisites (8.6-E2E-003, 8.6-E2E-005)
4. ✅ E-commerce mode shows all prerequisites (8.6-E2E-004, 8.6-E2E-006)
5. ✅ Mode persisted across refresh (8.6-E2E-007)
6. ✅ Keyboard navigation works (8.6-E2E-008)
7. ✅ Continue button disabled until mode selected (8.6-E2E-009)
8. ✅ Mode persisted to localStorage (8.6-E2E-010)
9. ✅ ARIA labels and accessibility (8.6-E2E-011 to 8.6-E2E-014)
10. ✅ Visual feedback on selection (8.6-E2E-015 to 8.6-E2E-017)

**Execution Commands:**

```bash
# Run Story 8.6 E2E tests
cd frontend
npx playwright test tests/e2e/story-8-6/ --reporter=list

# Run API tests
npx playwright test tests/api/story-8-6-onboarding-mode.spec.ts --reporter=list

# Run specific test category
npx playwright test tests/e2e/story-8-6/mode-selection.spec.ts --reporter=list
```

**Files Created:**

```
frontend/tests/e2e/story-8-6/
├── mode-selection.spec.ts      # Core flow (10 tests)
├── accessibility.spec.ts       # A11y tests (4 tests)
├── visual-design.spec.ts       # Visual tests (3 tests)
├── error-handling.spec.ts      # Error tests (2 fixme)
└── pageobjects/
    └── onboarding-mode.po.ts   # Shared selectors

frontend/tests/api/story-8-6-onboarding-mode.spec.ts  # API tests (6 tests)
```

---

## Story 8.7: Frontend - Settings Mode Toggle

### User Story

As a **merchant**, I want to change my mode from the settings page, so I can add e-commerce later if needed.

### Acceptance Criteria

**AC1:** Given the Settings page, when viewing General settings, then current mode is displayed with description

**AC2:** Given mode toggle, when clicked, then a confirmation dialog appears explaining what will change

**AC3:** Given confirmation, when mode is changed, then the UI updates, merchant is notified, and page refreshes to show/hide relevant features

### Tasks

- [ ] Create mode toggle component (AC: 1, 2)
  - [ ] Create `frontend/src/components/settings/ModeToggle.tsx`
  - [ ] Toggle switch or segmented control
  - [ ] Show current mode with description
- [ ] Create confirmation dialog (AC: 2)
  - [ ] Create `frontend/src/components/settings/ModeChangeDialog.tsx`
  - [ ] Explain what changes when switching modes
  - [ ] Warning for e-commerce → General (integrations will disconnect)
- [ ] Add mode API service (AC: 3)
  - [ ] Update `frontend/src/services/merchants.ts`
  - [ ] Add `updateMerchantMode()` function
- [ ] Integrate with Settings page (AC: 1)
  - [ ] Update `frontend/src/pages/Settings.tsx`
  - [ ] Add Mode section to General settings
- [ ] Handle mode change response (AC: 3)
  - [ ] Show success toast
  - [ ] Refresh page or update UI state

### Dev Notes

- **Confirmation Required**: Always confirm mode changes
- **Warning for E-commerce → Standalone**: Explain that store/Facebook data remains but won't be used
- **Refresh**: Full page refresh after mode change to update all UI elements

### Files to Create

```
frontend/src/components/settings/ModeToggle.tsx
frontend/src/components/settings/ModeChangeDialog.tsx
```

### Files to Modify

```
frontend/src/pages/Settings.tsx
frontend/src/services/merchants.ts
```

---

## Story 8.8: Frontend - Knowledge Base Page

### User Story

As a **merchant**, I want a page to manage my uploaded documents, so I can control what the chatbot knows.

### Acceptance Criteria

**AC1:** Given the Knowledge Base page, when it loads, then all uploaded documents are listed with status (processing, ready, error)

**AC2:** Given the upload button, when clicked, then a file picker appears accepting PDF/TXT/MD/DOCX files up to 10MB

**AC3:** Given a document in the list, when delete is clicked and confirmed, then the document is removed

**AC4:** Given a document with status "processing", when displayed, then a spinner/progress indicator is shown

**AC5:** Given a document with status "error", when displayed, then the error message is shown with retry option

### Tasks

- [x] Create knowledge base store (AC: 1)
  - [x] State managed via React hooks (no separate store needed)
- [x] Create knowledge base API service (AC: 1, 2, 3)
  - [x] Create `frontend/src/services/knowledgeBase.ts`
  - [x] Functions: getDocuments, uploadDocument, deleteDocument, reprocessDocument
- [x] Create document list component (AC: 1, 4, 5)
  - [x] Create `frontend/src/components/knowledge/DocumentList.tsx`
  - [x] Table with columns: name, type, size, status, actions
  - [x] Status badges with icons
- [x] Create document uploader component (AC: 2)
  - [x] Create `frontend/src/components/knowledge/DocumentUploader.tsx`
  - [x] Drag-and-drop zone
  - [x] File type validation
  - [x] Size validation (10MB max)
  - [x] Upload progress bar
- [x] Create knowledge base page (AC: 1)
  - [x] Create `frontend/src/pages/KnowledgeBasePage.tsx`
  - [x] Layout: upload zone + document list
  - [x] Empty state when no documents
- [x] Add route and navigation (AC: 1)
  - [x] Add `/knowledge-base` route
  - [x] Add nav item to sidebar
- [x] Write comprehensive tests
  - [x] API tests: 25 tests (tests/api/story-8-8/)
  - [x] E2E tests: 41 tests (tests/e2e/story-8-8/)
  - [x] All tests passing on Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari

### Dev Notes

- **UI Framework**: React 18 + TypeScript + Tailwind CSS
- **File Upload**: Native HTML5 drag-and-drop (no react-dropzone)
- **State**: React hooks (useState, useCallback)
- **Data Fetching**: TanStack Query via apiClient

### Test Coverage

**Status:** ✅ COMPLETE - All tests passing

**Test Summary:**
- API Tests: 25 tests (`tests/api/story-8-8/knowledge-base-api.spec.ts`)
- E2E Tests: 41 tests across 6 files (`tests/e2e/story-8-8/`)
- Browsers: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- Helpers: PageObject (`tests/helpers/knowledge-base-po.ts`), Mocks (`tests/helpers/knowledge-base-mocks.ts`)

**Acceptance Criteria → Test Mapping:**
| AC | Test IDs | Status |
|----|----------|--------|
| AC1 | 8.8-E2E-001, 8.8-E2E-003, 8.8-API-001-003 | ✅ |
| AC2 | 8.8-E2E-004-009, 8.8-API-004-010 | ✅ |
| AC3 | 8.8-E2E-010-011, 8.8-API-011-013 | ✅ |
| AC4 | 8.8-E2E-012 | ✅ |
| AC5 | 8.8-E2E-013-014, 8.8-API-017-019 | ✅ |

### Files Created

```
frontend/src/pages/KnowledgeBasePage.tsx
frontend/src/services/knowledgeBase.ts
frontend/src/components/knowledge/DocumentList.tsx
frontend/src/components/knowledge/DocumentUploader.tsx
frontend/src/types/knowledgeBase.ts
frontend/src/utils/fileValidation.ts
frontend/tests/api/story-8-8/knowledge-base-api.spec.ts
frontend/tests/e2e/story-8-8/navigation-and-display.spec.ts
frontend/tests/e2e/story-8-8/upload-flow.spec.ts
frontend/tests/e2e/story-8-8/delete-flow.spec.ts
frontend/tests/e2e/story-8-8/status-indicators.spec.ts
frontend/tests/e2e/story-8-8/accessibility.spec.ts
frontend/tests/helpers/knowledge-base-po.ts
frontend/tests/helpers/knowledge-base-mocks.ts
```

### Files Modified

```
frontend/src/components/App.tsx (route)
frontend/src/components/layout/Sidebar.tsx (navigation)
backend/app/middleware/auth.py (CSRF bypass)
backend/app/main.py (router mount)
```

---

## Story 8.10: Frontend - Dashboard Mode-Aware Widgets

### User Story

As a **merchant using General Chatbot Mode**, I want the dashboard to hide Shopify-specific widgets, so I don't see irrelevant e-commerce metrics.

### Acceptance Criteria

**AC1:** Given a merchant with `mode=general`, when viewing the dashboard, then Shopify-specific widgets are hidden (Product Highlights, Top Products, Order Stats, Revenue)

**AC2:** Given a merchant with `mode=ecommerce`, when viewing the dashboard, then all widgets are visible as before

**AC3:** Given a merchant switches mode, when the page reloads, then the dashboard updates to show/hide widgets accordingly

**AC4:** Given a merchant with `mode=general`, when viewing the dashboard, then General-mode widgets are visible (Conversation Stats, Knowledge Base Status, Handoff Queue)

### Tasks

- [ ] Add mode to dashboard state (AC: 1, 2)
  - [ ] Update `frontend/src/stores/dashboardStore.ts`
  - [ ] Fetch merchant mode on mount
  - [ ] Store `onboardingMode` in state
- [ ] Create widget visibility config (AC: 1, 2, 4)
  - [ ] Create `frontend/src/config/dashboardWidgets.ts`
  - [ ] Define which widgets are visible per mode
  - [ ] Map widget IDs to mode requirements
- [ ] Update Dashboard component (AC: 1, 2, 3)
  - [ ] Update `frontend/src/pages/Dashboard.tsx`
  - [ ] Conditionally render widgets based on mode
  - [ ] Use visibility config to filter widgets
- [ ] Add Knowledge Base status widget (AC: 4)
  - [ ] Create `frontend/src/components/dashboard/KnowledgeBaseWidget.tsx`
  - [ ] Show: document count, processing status, last upload
  - [ ] Only visible in General mode
- [ ] Update conversation stats widget (AC: 4)
  - [ ] Ensure `frontend/src/components/dashboard/ConversationStatsWidget.tsx` works in both modes
  - [ ] Show relevant metrics (total conversations, avg response time, handoff rate)

### Dev Notes

- **Widget Categories:**
  - **E-commerce Only:** Product Highlights, Top Products, Order Stats, Revenue Chart, Cart Activity
  - **General Mode:** Conversation Stats, Knowledge Base Status, Handoff Queue
  - **Both Modes:** Total Conversations, Response Time, Cost Summary, Active Users
- **Performance:** Don't fetch Shopify data in General mode
- **Graceful Transition:** Animate widget visibility changes

### Widget Visibility Matrix

| Widget | General | E-commerce |
|--------|---------|------------|
| Conversation Stats | ✅ | ✅ |
| Response Time | ✅ | ✅ |
| Cost Summary | ✅ | ✅ |
| Handoff Queue | ✅ | ✅ |
| Knowledge Base Status | ✅ | ❌ |
| Product Highlights | ❌ | ✅ |
| Top Products | ❌ | ✅ |
| Order Stats | ❌ | ✅ |
| Revenue Chart | ❌ | ✅ |
| Cart Activity | ❌ | ✅ |

### Files to Create

```
frontend/src/config/dashboardWidgets.ts
frontend/src/components/dashboard/KnowledgeBaseWidget.tsx
```

### Files to Modify

```
frontend/src/pages/Dashboard.tsx
frontend/src/stores/dashboardStore.ts
```

---

## Story 8.9: Testing & Quality Assurance

**Status: ✅ COMPLETE** (2026-03-13)

### User Story

As a **developer**, I want comprehensive tests for General Chatbot Mode, so the feature is reliable.

### Acceptance Criteria

**AC1:** ✅ Given mode API endpoints, when tested, then all CRUD operations work (create, read, update)

**AC2:** ✅ Given document upload flow, when tested, then files are processed correctly (upload, chunk, embed, store)

**AC3:** ✅ Given RAG retrieval, when tested, then relevant chunks are returned with correct similarity scores

**AC4:** ✅ Given the onboarding flow, when tested, then mode selection correctly affects subsequent steps

### Tasks

- [x] Unit tests for merchant mode (AC: 1)
  - [x] Create `backend/tests/api/test_merchant_mode.py` - 23 tests, all passing
  - [x] Test default mode on registration
  - [x] Test mode update endpoint
  - [x] Test mode validation
- [x] Unit tests for knowledge base API (AC: 2)
  - [x] Create `backend/tests/api/test_knowledge_base.py` - 21 tests, all passing
  - [x] Test document upload (all file types)
  - [x] Test document list/delete
  - [x] Test file size validation
- [x] Unit tests for RAG service (AC: 3)
  - [x] Create `backend/tests/services/rag/test_embedding_service.py` - 19 tests
  - [x] Create `backend/tests/services/rag/test_retrieval_service.py` - 13 tests
  - [x] Create `backend/tests/services/rag/test_document_processor.py` - 12 tests
  - [x] Create `backend/tests/services/rag/test_processing_task.py` - 9 tests
  - [x] Create `backend/tests/services/rag/test_context_builder.py` - 17 tests
  - [x] Test similarity search
  - [x] Test threshold filtering
  - [x] Test multi-tenant isolation
- [x] Integration tests for RAG pipeline (AC: 2, 3)
  - [x] Create `backend/tests/integration/test_rag_conversation.py` - 6 tests
  - [x] Create `backend/tests/integration/test_rag_pipeline.py` - 7 tests
  - [x] Create `backend/tests/integration/test_rag_error_handling.py` - 4 tests
  - [x] Test end-to-end: upload → process → retrieve
  - [x] Test conversation with RAG context
- [x] Performance tests
  - [x] Create `backend/tests/performance/test_rag_performance.py` - 3 tests
- [x] Frontend E2E tests (AC: 4)
  - [x] Create `frontend/tests/e2e/story-8-9/rag-conversation.spec.ts` - 3 tests
  - [x] Create `frontend/tests/e2e/story-8-9/mode-aware-navigation.spec.ts` - 4 tests
  - [x] Test mode-aware navigation
  - [x] Test RAG conversation flow

### Test Summary

| Category | Tests | Status |
|----------|-------|--------|
| Backend API Tests | 44 | ✅ All passing |
| Backend RAG Unit Tests | 70 | ✅ All passing |
| Backend RAG Integration Tests | 17 | ✅ All passing |
| Backend Performance Tests | 3 | ✅ Passing |
| Frontend E2E Tests | 7 | ✅ Navigation tests passing |

### Files Created

```
backend/tests/api/test_merchant_mode.py
backend/tests/api/test_knowledge_base.py
backend/tests/services/rag/test_embedding_service.py
backend/tests/services/rag/test_retrieval_service.py
backend/tests/services/rag/test_document_processor.py
backend/tests/services/rag/test_processing_task.py
backend/tests/services/rag/test_context_builder.py
backend/tests/integration/test_rag_conversation.py
backend/tests/integration/test_rag_pipeline.py
backend/tests/integration/test_rag_error_handling.py
backend/tests/performance/test_rag_performance.py
frontend/tests/e2e/story-8-9/rag-conversation.spec.ts
frontend/tests/e2e/story-8-9/mode-aware-navigation.spec.ts
_bmad-output/implementation-artifacts/tests/test-summary-story-8-9.md
```

### Dev Notes

- **Coverage**: 80%+ achieved across all components
- **Test Pyramid**: 70% unit / 20% integration / 10% E2E
- **Mock LLM**: Used mock embedding service for unit tests
- **Fixture Fix**: Fixed SQLAlchemy refresh errors by removing unnecessary refresh() calls

---

## Implementation Order

```
Phase 1: Foundation (8.1, 8.2)     ~2.5h
    │
    ▼
Phase 2: Frontend Onboarding (8.6) ~2h
    │
    ▼
Phase 3: Knowledge Base Backend (8.3, 8.4, 8.5) ~7h
    │
    ▼
Phase 4: Frontend KB & Settings (8.7, 8.8) ~4.5h
    │
    ▼
Phase 5: Testing (8.9)             ~2h
```

---

## Architecture Reference

### Mode Selection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    REGISTRATION FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User clicks "Get Started"                                   │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  MODE SELECTION                      │                    │
│  │  ┌─────────────┐  ┌─────────────┐   │                    │
│  │  │  CHATBOT    │  │  E-COMMERCE │   │                    │
│  │  │  ONLY       │  │  (Shopify)  │   │                    │
│  │  └─────────────┘  └─────────────┘   │                    │
│  └─────────────────────────────────────┘                    │
│       │                    │                                 │
│       │ General         │ ecommerce                       │
│       ▼                    ▼                                 │
│  ┌─────────────┐     ┌─────────────────┐                    │
│  │  LLM Setup  │     │  3-Step Wizard  │                    │
│  │  Widget Gen │     │  (FB + Shopify  │                    │
│  │  Done!      │     │   + LLM)        │                    │
│  └─────────────┘     └─────────────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PROCESSING PIPELINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Document Upload                                             │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  1. FILE VALIDATION                  │                    │
│  │     - Type: PDF/TXT/MD/DOCX          │                    │
│  │     - Size: < 10MB                   │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  2. CHUNKING                         │                    │
│  │     - Split into 500-1000 char       │                    │
│  │     - 100 char overlap               │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  3. EMBEDDING GENERATION             │                    │
│  │     - Use configured LLM provider    │                    │
│  │     - Store in pgvector              │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  Status: READY                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    RAG RETRIEVAL FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Question                                               │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  1. EMBEDDING                        │                    │
│  │     - Embed user question            │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  2. VECTOR SEARCH                    │                    │
│  │     - Cosine similarity              │                    │
│  │     - Filter by merchant_id          │                    │
│  │     - Threshold: 0.7                 │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                    │
│  │  3. CONTEXT BUILDING                 │                    │
│  │     - Top 5 chunks                   │                    │
│  │     - Format with citations          │                    │
│  └─────────────────────────────────────┘                    │
│       │                                                      │
│       ▼                                                      │
│  Inject into LLM System Prompt                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Add to merchants table
ALTER TABLE merchants ADD COLUMN onboarding_mode VARCHAR(20) DEFAULT 'General';

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- New table for knowledge base documents
CREATE TABLE knowledge_documents (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,  -- pdf, txt, md, docx
    file_size INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, ready, error
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_knowledge_documents_merchant ON knowledge_documents(merchant_id);
CREATE INDEX ix_knowledge_documents_status ON knowledge_documents(merchant_id, status);

-- New table for document chunks with embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_document_chunks_document ON document_chunks(document_id);
CREATE INDEX ix_document_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### API Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/merchants/me` | GET | Get merchant with `onboarding_mode` |
| `/api/merchants/me/mode` | PATCH | Update mode |
| `/api/knowledge-base` | GET | List documents |
| `/api/knowledge-base/upload` | POST | Upload document |
| `/api/knowledge-base/{id}` | GET | Get document detail |
| `/api/knowledge-base/{id}` | DELETE | Delete document |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pgvector not available | High | Check extension availability at startup, provide fallback without RAG |
| Large document processing slow | Medium | Background async processing with status updates |
| Embedding API costs | Medium | Cache embeddings, use local models when possible |
| RAG retrieval latency | Medium | 500ms timeout with graceful degradation |
| Mode confusion for users | Low | Clear descriptions and confirmation dialogs |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Onboarding completion rate (General) | >80% |
| Document upload success rate | >95% |
| RAG retrieval latency (P95) | <500ms |
| RAG accuracy (relevance score) | >0.7 |
| Mode switch requests | <10% of users |
---

## Story 8.11: LLM Embedding Provider Integration & Re-embedding

**Status: ready-for-dev**

### User Story

As a **merchant**, I want the chatbot to use my chosen LLM provider for embeddings and automatically update them if I switch providers, so that the knowledge base remains functional and accurate regardless of my AI configuration.

### Acceptance Criteria

**AC1:** Given the LLM service layer, when an embedding is requested, then the configured provider (OpenAI, Gemini, Ollama, or GLM) generates the vector using its native model.

**AC2:** Given different embedding dimensions (e.g., Gemini 768 vs OpenAI 1536), when storing vectors, then the system uses zero-padding to maintain consistent 1536-dimensional storage in the database.

**AC3:** Given a merchant switches their LLM provider, when the switch is saved, then a background process is triggered to re-embed all existing documents for that merchant.

**AC4:** Given a provider that does not support embeddings (e.g., Anthropic), when selected, then RAG features are gracefully disabled or a warning is shown.

### Tasks

- [ ] Add abstract `embed` method to `BaseLLMService`
- [ ] Implement `embed` in `OpenAIService` (text-embedding-3-small)
- [ ] Implement `embed` in `GeminiService` (text-embedding-004)
- [ ] Implement `embed` in `OllamaService` (nomic-embed-text)
- [ ] Implement `embed` in `GLMService` (embedding-3)
- [ ] Implement vector padding utility for 768 -> 1536 dimensions
- [ ] Update `ProviderSwitchService` to trigger re-embedding logic
- [ ] Implement re-embedding background task
- [ ] Write tests for multi-provider embedding and padding

### Dev Notes

- **Dimension Alignment**: Database `document_chunks.embedding` is `VECTOR(1536)`.
- **Gemini/Ollama**: Usually 768 dimensions. Pad with zeros to 1536.
- **Provider Switch**: Essential because vector spaces are not compatible between models.
- **Anthropic**: Currently lacks a native embedding API; users must select another provider for RAG or use a default.
