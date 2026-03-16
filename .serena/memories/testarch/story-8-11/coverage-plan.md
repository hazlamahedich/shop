# Story 8-11: Test Coverage Plan

## Acceptance Criteria Mapping

| AC# | Scenario | Priority | Test Level | Coverage Status |
|-----|----------|----------|------------|------------------|
| 1. Multi-Provider Support | Gemini, OpenAI, Ollama embedding models work correctly | P0 | Unit + API | ✅ **Backend tests exist** |
| 2. Provider Configuration | Merchants configure embedding provider via settings UI/API | P1 | E2E + API | ⚠️ **Frontend settings component exists, needs E2E validation** |
| 3. Change Detection | System detects when embedding provider changes | P0 | Unit + API | ✅ **Backend tests exist** |
| 4. Automated Re-embedding | When provider changes, all docs automatically queued for re-embedding | P0 | Unit + API | ✅ **Backend tests exist** |
| 5. Background Processing | Re-embedding via background worker with progress tracking | P1 | Unit + Integration | ✅ **Backend tests exist** |
| 6. Vector Consistency | Retrieval ensures only current model embeddings are used | P0 | Unit + API | ✅ **Backend tests exist** |
| 7. Manual Trigger | POST /api/v1/knowledge/re-embed endpoint | P1 | API | ✅ **Backend tests exist** |
| 8. Error Handling | Graceful handling of provider-specific errors (rate limits, invalid API keys) | P0 | Unit + API | ✅ **Backend tests exist** |

## Coverage Gaps

| Gap | Priority | Test Level | Recommendation |
|-----|----------|------------|----------------|
| **E2E: Provider Switching Flow** | P0 | E2E | Create end-to-end test for complete provider switching flow |
| **API: Embedding Settings Endpoints** | P1 | API | Add contract tests for `/api/settings/embedding-provider` endpoint |
| **Frontend: EmbeddingSettings Component** | P1 | Component | Add component tests for EmbeddingSettings.tsx |
| **Integration: Cross-provider data migration** | P1 | Integration | Add test verifying data migration from OpenAI → Gemini preserves document integrity |
| **E2E: User Journey - Settings Update** | P2 | E2E | Add test for merchant updating embedding settings via dashboard |

## Recommended Test Structure
```
frontend/tests/
├── api/
│   ├── story-8-11-embedding-provider-settings.spec.ts  [P1]
│   └── story-8-11-reembed-endpoint.spec.ts  [P1]
├── e2e/
│   └── story-8-11-embedding-provider-switch.spec.ts  [P0]
├── component/
│   └── EmbeddingSettings.spec.tsx  [P1]
└── integration/
    └── story-8-11-cross-provider-migration.spec.ts  [P1]
```

## Priority Justification
- **P0**: Critical business functionality affecting RAG capabilities, cost optimization, and data integrity
- **P1**: Important user-facing features with moderate risk
- **P2**: Secondary flows, nice-to-have but lower priority

## Test Levels Chosen
| Level | Coverage | Rationale |
|-------|----------|-----------|
| **Unit** | Backend providers (✅ Existing) | Fast, isolated, pure logic testing |
| **API** | New endpoints + contract validation | Test service contracts without UI overhead |
| **Component** | Frontend settings UI | Test component behavior in isolation |
| **E2E** | Complete user journeys | Critical business flows with full browser context |
| **Integration** | Cross-service data flow | Verify data migration across services |

## Scope Decision
**Coverage Target: selective**

**Rationale:** Story 8-11 extends existing RAG functionality with new provider support. Focus on:
1. New Gemini provider integration
2. Provider switching workflow (critical path)
3. New API endpoints
4. Frontend settings UI
5. Cross-provider data migration

Avoid duplicating existing unit tests. Add E2E tests for critical user journeys and component tests for UI behavior.
