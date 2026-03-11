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

| Story | Title | Priority | Est. Time | Dependencies |
|-------|-------|----------|-----------|--------------|
| 8.1 | Backend: Merchant Mode Field & API | P0 | 1.5h | None |
| 8.2 | Backend: Onboarding Mode Selection | P0 | 1h | 8.1 |
| 8.3 | Backend: Knowledge Base Models & Storage | P0 | 2h | 8.1 |
| 8.4 | Backend: RAG Service (Document Processing) | P1 | 3h | 8.3 |
| 8.5 | Backend: RAG Integration in Conversation | P1 | 2h | 8.4 |
| 8.6 | Frontend: Onboarding Mode Selection UI | P0 | 2h | 8.2 |
| 8.7 | Frontend: Settings Mode Toggle | P1 | 1.5h | 8.1 |
| 8.8 | Frontend: Knowledge Base Page | P1 | 3h | 8.3 |
| 8.9 | Testing & Quality Assurance | P1 | 2h | All |
| 8.10 | Frontend: Dashboard Mode-Aware Widgets | P1 | 2h | 8.1 |

**Total: ~20 hours**

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

### User Story

As a **new user registering**, I want to choose my use case during registration, so I'm not forced through irrelevant setup steps.

### Acceptance Criteria

**AC1:** Given the registration endpoint, when `mode` is provided, then it's stored on the merchant

**AC2:** Given a merchant with `mode=General`, when auth status is returned, then `has_store_connected=false` and `has_facebook_connected=false`

**AC3:** Given mode is not provided, when registering, then default to `"General"`

### Tasks

- [ ] Update registration schema (AC: 1, 3)
  - [ ] Update `backend/app/schemas/auth.py`
  - [ ] Add optional `mode: Optional[str]` to `RegisterRequest`
- [ ] Update registration endpoint (AC: 1, 3)
  - [ ] Update `backend/app/api/auth.py`
  - [ ] Store mode on merchant creation
  - [ ] Default to `"General"` if not provided
- [ ] Update auth status response (AC: 2)
  - [ ] Update `backend/app/api/auth.py`
  - [ ] Include `onboarding_mode` in login/status response
  - [ ] Derive `has_store_connected` and `has_facebook_connected` from mode + integrations

### Dev Notes

- **Backward Compatible**: Existing merchants without mode field should be treated as `ecommerce`
- **Migration**: Set existing merchants to `ecommerce` mode

### Files to Modify

```
backend/app/schemas/auth.py
backend/app/api/auth.py
```

---

## Story 8.3: Backend - Knowledge Base Models & Storage

### User Story

As a **merchant**, I want to upload documents that the chatbot can learn from, so it can answer questions about my business.

### Acceptance Criteria

**AC1:** Given an authenticated merchant, when they upload a document (PDF/TXT/MD/DOCX), then it's stored with metadata (filename, size, type, created_at, status)

**AC2:** Given a document upload, when the file is processed, then it's chunked into segments (500-1000 chars) for embedding

**AC3:** Given a merchant requests their documents, then all their documents are returned with processing status

**AC4:** Given a document, when delete is requested, then the document and all its chunks are removed

### Tasks

- [ ] Create KnowledgeDocument model (AC: 1)
  - [ ] Create `backend/app/models/knowledge_base.py`
  - [ ] Fields: id, merchant_id, filename, file_type, file_size, status, error_message, created_at, updated_at
- [ ] Create DocumentChunk model (AC: 2)
  - [ ] Add to `backend/app/models/knowledge_base.py`
  - [ ] Fields: id, document_id, chunk_index, content, embedding (vector), created_at
- [ ] Create database migration (AC: 1, 2)
  - [ ] Create `alembic/versions/XXX_add_knowledge_base.py`
  - [ ] Enable pgvector extension
  - [ ] Create vector index for similarity search
- [ ] Create knowledge base schemas (AC: 1, 3)
  - [ ] Create `backend/app/schemas/knowledge_base.py`
  - [ ] `DocumentUploadResponse`, `DocumentListResponse`, `DocumentDetail`
- [ ] Create document upload endpoint (AC: 1)
  - [ ] Create `backend/app/api/knowledge_base.py`
  - [ ] `POST /api/knowledge-base/upload`
  - [ ] Validate file type and size (max 10MB)
  - [ ] Store file and create document record
- [ ] Create document chunking service (AC: 2)
  - [ ] Create `backend/app/services/knowledge/chunker.py`
  - [ ] Split documents into 500-1000 char chunks with overlap
  - [ ] Handle different file types (PDF, TXT, MD, DOCX)
- [ ] Create document list/delete endpoints (AC: 3, 4)
  - [ ] Add to `backend/app/api/knowledge_base.py`
  - [ ] `GET /api/knowledge-base`, `DELETE /api/knowledge-base/{id}`
- [ ] Add CSRF bypass for new endpoints (AC: 1, 3, 4)
  - [ ] Update `backend/app/middleware/auth.py`

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

### Files to Modify

```
backend/app/middleware/auth.py
backend/app/main.py (add router)
```

---

## Story 8.4: Backend - RAG Service (Document Processing)

### User Story

As a **chatbot user**, I want the bot to answer questions based on uploaded documents, so I get accurate, business-specific information.

### Acceptance Criteria

**AC1:** Given a document is uploaded, when processing completes, then embeddings are generated for each chunk using the configured LLM provider

**AC2:** Given a user question, when RAG retrieval runs, then the top 5 most relevant chunks are returned with similarity scores

**AC3:** Given no relevant documents exist (similarity < 0.7), when retrieval runs, then an empty list is returned (no hallucination)

**AC4:** Given document processing fails, when error occurs, then the document status is updated to "error" with error message

### Tasks

- [ ] Create embedding service (AC: 1)
  - [ ] Create `backend/app/services/rag/embedding_service.py`
  - [ ] Generate embeddings using configured LLM provider
  - [ ] Support OpenAI, Anthropic, local (Ollama) embedding models
  - [ ] Batch embedding for multiple chunks
- [ ] Create retrieval service (AC: 2, 3)
  - [ ] Create `backend/app/services/rag/retrieval_service.py`
  - [ ] Vector similarity search using pgvector
  - [ ] Return top-k chunks with similarity threshold (0.7)
  - [ ] Filter by merchant_id for multi-tenant isolation
- [ ] Create document processor (AC: 1, 4)
  - [ ] Create `backend/app/services/rag/document_processor.py`
  - [ ] Orchestrate: upload → chunk → embed → store
  - [ ] Update document status throughout pipeline
  - [ ] Handle errors gracefully with status update
- [ ] Create background task for processing (AC: 1)
  - [ ] Create `backend/app/services/rag/processing_task.py`
  - [ ] Async processing of uploaded documents
  - [ ] Update document status: pending → processing → ready/error
- [ ] Integrate with knowledge base API (AC: 1, 4)
  - [ ] Update `backend/app/api/knowledge_base.py`
  - [ ] Trigger background processing on upload

### Dev Notes

- **Embedding Model**: Use `text-embedding-3-small` (OpenAI) or equivalent
- **Embedding Dimension**: 1536 (OpenAI) or 768 (local models)
- **Similarity Metric**: Cosine similarity
- **Threshold**: 0.7 minimum similarity (tunable per merchant)
- **Performance Target**: <500ms for retrieval

### Files to Create

```
backend/app/services/rag/__init__.py
backend/app/services/rag/embedding_service.py
backend/app/services/rag/retrieval_service.py
backend/app/services/rag/document_processor.py
backend/app/services/rag/processing_task.py
backend/tests/services/rag/test_retrieval.py
backend/tests/services/rag/test_embedding.py
```

---

## Story 8.5: Backend - RAG Integration in Conversation

### User Story

As a **user chatting with the bot**, I want answers grounded in the merchant's documents, so the information is accurate and relevant.

### Acceptance Criteria

**AC1:** Given a merchant has uploaded documents, when a user asks a question, then relevant document chunks are retrieved and included in the LLM context

**AC2:** Given RAG context is available, when the LLM generates a response, then it cites the source document name

**AC3:** Given General Chatbot Mode with e-commerce intent detected (product search, cart, checkout), when the bot responds, then a graceful fallback message is shown

**AC4:** Given RAG retrieval takes >500ms, when timeout occurs, then proceed without RAG context (graceful degradation)

### Tasks

- [ ] Create RAG context builder (AC: 1)
  - [ ] Create `backend/app/services/rag/context_builder.py`
  - [ ] Retrieve relevant chunks for user query
  - [ ] Format chunks as context string with source citations
- [ ] Integrate with UnifiedConversationService (AC: 1, 2)
  - [ ] Update `backend/app/services/conversation/unified_conversation_service.py`
  - [ ] Call RAG retrieval before LLM call for General merchants
  - [ ] Inject context into system prompt
  - [ ] Add source citation instruction to prompt
- [ ] Add General Chatbot Mode fallback handlers (AC: 3)
  - [ ] Update intent handlers in unified service
  - [ ] Return friendly message for e-commerce intents in General Chatbot Mode
  - [ ] Example: "I'm a general assistant. For product search and orders, please connect a store in Settings."
- [ ] Add timeout handling (AC: 4)
  - [ ] Add asyncio timeout to RAG retrieval
  - [ ] Log timeout events for monitoring
  - [ ] Proceed with LLM call without RAG context

### Dev Notes

- **Context Injection**: Prepend RAG context to system prompt
- **Citation Format**: "According to [Document Name], ..."
- **Timeout**: 500ms max for retrieval
- **Logging**: Track RAG usage and performance metrics

### Prompt Template

```
You are a helpful assistant with access to the following knowledge base:

{rag_context}

Use this information to answer the user's question. If you reference information from the knowledge base, cite the source document.

If the question is outside the scope of the knowledge base, provide a helpful general response or suggest the user contact support.
```

### Files to Create

```
backend/app/services/rag/context_builder.py
```

### Files to Modify

```
backend/app/services/conversation/unified_conversation_service.py
```

---

## Story 8.6: Frontend - Onboarding Mode Selection UI

### User Story

As a **new user**, I want a visual way to choose my use case during onboarding, so I understand what I'm signing up for.

### Acceptance Criteria

**AC1:** Given the onboarding page, when it loads, then a mode selection screen appears first with two options: "Chatbot Only" and "E-commerce"

**AC2:** Given "Chatbot Only" is selected, when continuing, then Shopify/Facebook steps are skipped and only LLM configuration is shown

**AC3:** Given "E-commerce" is selected, when continuing, then the existing 3-step wizard is shown

**AC4:** Given mode selection, when the user proceeds, then the mode is sent to the registration/onboarding API

### Tasks

- [ ] Create mode selection component (AC: 1)
  - [ ] Create `frontend/src/components/onboarding/ModeSelection.tsx`
  - [ ] Two card options with icons and descriptions
  - [ ] Highlighted selection state
- [ ] Update onboarding flow (AC: 2, 3)
  - [ ] Update `frontend/src/pages/Onboarding.tsx`
  - [ ] Add mode selection as Step 0
  - [ ] Conditionally show/hide integration steps based on mode
- [ ] Update onboarding store (AC: 4)
  - [ ] Update `frontend/src/stores/onboardingStore.ts`
  - [ ] Add `onboardingMode` state
  - [ ] Persist mode selection
- [ ] Update registration API call (AC: 4)
  - [ ] Update `frontend/src/services/auth.ts`
  - [ ] Include mode in registration request

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

- [ ] Create knowledge base store (AC: 1)
  - [ ] Create `frontend/src/stores/knowledgeBaseStore.ts`
  - [ ] State: documents, upload status, selected document
- [ ] Create knowledge base API service (AC: 1, 2, 3)
  - [ ] Create `frontend/src/services/knowledgeBase.ts`
  - [ ] Functions: getDocuments, uploadDocument, deleteDocument
- [ ] Create document list component (AC: 1, 4, 5)
  - [ ] Create `frontend/src/components/knowledge/DocumentList.tsx`
  - [ ] Table with columns: name, type, size, status, actions
  - [ ] Status badges with icons
- [ ] Create document uploader component (AC: 2)
  - [ ] Create `frontend/src/components/knowledge/DocumentUploader.tsx`
  - [ ] Drag-and-drop zone
  - [ ] File type validation
  - [ ] Size validation (10MB max)
  - [ ] Upload progress bar
- [ ] Create knowledge base page (AC: 1)
  - [ ] Create `frontend/src/pages/KnowledgeBase.tsx`
  - [ ] Layout: upload zone + document list
  - [ ] Empty state when no documents
- [ ] Add route and navigation (AC: 1)
  - [ ] Update `frontend/src/components/App.tsx`
  - [ ] Add `/knowledge-base` route
  - [ ] Add nav item to sidebar

### Dev Notes

- **UI Framework**: React 18 + TypeScript + Tailwind CSS
- **File Upload**: Use react-dropzone for drag-and-drop
- **State**: Zustand for local state
- **Data Fetching**: TanStack Query for API calls

### Files to Create

```
frontend/src/pages/KnowledgeBase.tsx
frontend/src/stores/knowledgeBaseStore.ts
frontend/src/services/knowledgeBase.ts
frontend/src/components/knowledge/DocumentList.tsx
frontend/src/components/knowledge/DocumentUploader.tsx
```

### Files to Modify

```
frontend/src/components/App.tsx
frontend/src/components/layout/Sidebar.tsx (or equivalent)
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

### User Story

As a **developer**, I want comprehensive tests for General Chatbot Mode, so the feature is reliable.

### Acceptance Criteria

**AC1:** Given mode API endpoints, when tested, then all CRUD operations work (create, read, update)

**AC2:** Given document upload flow, when tested, then files are processed correctly (upload, chunk, embed, store)

**AC3:** Given RAG retrieval, when tested, then relevant chunks are returned with correct similarity scores

**AC4:** Given the onboarding flow, when tested, then mode selection correctly affects subsequent steps

### Tasks

- [ ] Unit tests for merchant mode (AC: 1)
  - [ ] Create `backend/tests/api/test_merchant_mode.py`
  - [ ] Test default mode on registration
  - [ ] Test mode update endpoint
  - [ ] Test mode validation
- [ ] Unit tests for knowledge base API (AC: 2)
  - [ ] Create `backend/tests/api/test_knowledge_base.py`
  - [ ] Test document upload (all file types)
  - [ ] Test document list/delete
  - [ ] Test file size validation
- [ ] Unit tests for RAG service (AC: 3)
  - [ ] Create `backend/tests/services/rag/test_retrieval.py`
  - [ ] Test similarity search
  - [ ] Test threshold filtering
  - [ ] Test multi-tenant isolation
- [ ] Integration tests for RAG pipeline (AC: 2, 3)
  - [ ] Create `backend/tests/integration/test_rag_pipeline.py`
  - [ ] Test end-to-end: upload → process → retrieve
  - [ ] Test conversation with RAG context
- [ ] Frontend component tests (AC: 4)
  - [ ] Create `frontend/src/components/onboarding/__tests__/ModeSelection.test.tsx`
  - [ ] Create `frontend/src/components/knowledge/__tests__/DocumentUploader.test.tsx`
  - [ ] Test mode selection flow
  - [ ] Test document upload UI
- [ ] E2E tests for General Chatbot Mode (AC: 4)
  - [ ] Create `frontend/e2e/General-mode.spec.ts`
  - [ ] Test onboarding with Chatbot Only mode
  - [ ] Test knowledge base upload and chat
  - [ ] Test mode switching from settings

### Dev Notes

- **Coverage Target**: 80% minimum
- **Test Pyramid**: 70% unit / 20% integration / 10% E2E
- **Mock LLM**: Use mock embedding service for tests

### Files to Create

```
backend/tests/api/test_merchant_mode.py
backend/tests/api/test_knowledge_base.py
backend/tests/services/rag/test_retrieval.py
backend/tests/services/rag/test_embedding.py
backend/tests/integration/test_rag_pipeline.py
frontend/src/components/onboarding/__tests__/ModeSelection.test.tsx
frontend/src/components/knowledge/__tests__/DocumentUploader.test.tsx
frontend/src/components/knowledge/__tests__/DocumentList.test.tsx
frontend/e2e/General-mode.spec.ts
```

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
