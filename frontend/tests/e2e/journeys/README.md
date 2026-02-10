# E2E Journey Tests

Comprehensive end-to-end tests covering complete user journeys through the Merchant Dashboard application.

## Test Files

### 1. Complete Onboarding Journey (`complete-onboarding.spec.ts`)
Tests the full onboarding flow from signup through platform connections to dashboard access.

**Coverage:**
- [P0] Complete happy path onboarding flow
- [P1] Facebook platform connection
- [P1] Shopify platform connection
- [P1] LLM provider configuration
- [P2] State persistence across reloads
- [P2] Accessibility (keyboard navigation, screen readers)

**Key Scenarios:**
- Prerequisites checklist completion
- Platform connection with OAuth mocking
- Provider selection and testing
- Navigation to dashboard after completion

### 2. Provider Switching Journey (`provider-switching.spec.ts`)
Tests merchant switching between LLM providers with cost comparison.

**Coverage:**
- [P0] Provider switching happy path (OpenAI → Anthropic)
- [P0] API key validation before switch
- [P1] Cost savings calculator display
- [P1] Cost changes verification after switch
- [P2] Conversation history preservation
- [P2] Provider feature comparison

**Key Scenarios:**
- Provider selection and configuration
- API key validation
- Cost comparison and savings calculation
- Real-time cost tracking updates

### 3. Search and Filter Conversations (`search-filter-conversations.spec.ts`)
Tests search and filter functionality for conversation management.

**Coverage:**
- [P0] Search by customer name
- [P0] Filter by status
- [P0] Filter by platform
- [P1] Multiple filter combination
- [P1] Clear all filters
- [P2] Filter persistence in URL
- [P2] Filter tags and individual removal

**Key Scenarios:**
- Text search functionality
- Status and platform filters
- Date range filtering
- Export filtered results
- Save filter preferences

### 4. Budget Cap Configuration (`budget-cap-configuration.spec.ts`)
Tests budget setting, visual validation, and progress tracking.

**Coverage:**
- [P0] Set monthly budget cap
- [P0] Budget usage progress bar
- [P0] Visual warning indicators
- [P1] Projected monthly spend
- [P1] Color-coded status (healthy/warning/critical)
- [P2] Budget recommendations
- [P2] No limit/unlimited option

**Key Scenarios:**
- Budget input and validation
- Progress bar visualization
- Warning/critical alerts
- Budget history and trends

### 5. Multi-Tab Authentication Sync (`multi-tab-auth-sync.spec.ts`)
Tests authentication state synchronization across browser tabs.

**Coverage:**
- [P0] Authentication sync across tabs
- [P1] Logout propagation
- [P1] Token refresh coordination
- [P2] Session expiry notifications
- [P2] Merchant context sync
- [P2] Preference synchronization

**Key Scenarios:**
- Login on one tab, verify on another
- Logout propagates to all tabs
- Token refresh coordination
- Concurrent login handling
- Offline/online tab handling

### 6. Data Deletion Flow (`data-deletion.spec.ts`)
Tests account and data deletion process with proper confirmations.

**Coverage:**
- [P0] Complete deletion happy path
- [P1] Email confirmation requirement
- [P1] Data deletion summary display
- [P1] Re-authentication before deletion
- [P2] Grace period cancellation
- [P2] Deletion report generation
- [P2] GDPR compliance

**Key Scenarios:**
- Initiate deletion request
- Confirmation with email/typing
- Data export option
- Grace period handling
- Session termination

### 7. Conversation Handoff Workflow (`conversation-handoff.spec.ts`)
Tests AI-to-human handoff and status tracking.

**Coverage:**
- [P0] Human takeover workflow
- [P1] Resume AI control
- [P1] Status change tracking
- [P1] Handoff history display
- [P2] Handoff reason selection
- [P2] Team notification
- [P2] Sentiment-based suggestions

**Key Scenarios:**
- Take over from AI
- Resume AI mode
- Track handoff status
- View handoff timeline
- Quick responses during takeover
- Context preservation

## Priority Levels

- **[P0]**: Critical paths - Happy path scenarios that must work
- **[P1]**: Important features - Core functionality with edge cases
- **[P2]**: Nice-to-have - Enhanced features and optimizations

## Running the Tests

```bash
# Run all journey tests
npm run test -- tests/e2e/journeys

# Run specific test file
npm run test -- tests/e2e/journeys/complete-onboarding.spec.ts

# Run only P0 tests
npm run test -- tests/e2e/journeys --grep "@P0"

# Run with UI
npm run test -- tests/e2e/journeys --ui

# Run with debug
npm run test -- tests/e2e/journeys --debug
```

## Test Patterns Used

### Given-When-Then Structure
```typescript
// GIVEN: User is on page
await page.goto('/conversations');

// WHEN: Performing action
await searchInput.fill('John');

// THEN: Verify result
await expect(results).toContainText('John');
```

### Network-First Pattern
```typescript
// Set up routes BEFORE navigation
await page.route('**/api/conversations**', route => {
  route.fulfill({ status: 200, body: JSON.stringify({...}) });
});

await page.goto('/conversations');
```

### Resilient Selectors
```typescript
// Use getByRole for accessibility
await page.getByRole('button', { name: /submit/i }).click();

// Use getByText for content
await expect(page.getByText(/success/i)).toBeVisible();

// Use getByLabel for form controls
await page.getByLabel(/email/i).fill('test@example.com');
```

### Multi-Tab Testing
```typescript
const page1 = await context.newPage();
const page2 = await context.newPage();

// Perform actions on both pages
await page1.goto('/login');
await page2.goto('/login');

// Verify sync
```

## Fixtures Used

- `page`: Playwright page fixture
- `context`: Browser context for multi-tab tests
- Custom routes for API mocking
- LocalStorage manipulation for state

## Requirements

- Playwright installed
- Frontend dev server running on http://localhost:5173
- Backend API available at http://localhost:8000 (or mocked)

## Maintenance

When updating UI components:
1. Update selectors in test files
2. Verify test assertions match new behavior
3. Update mock data if API changes
4. Check accessibility attributes
5. Test on multiple viewports

## Test Data

Tests use mocked API responses to ensure:
- Fast execution
- Deterministic results
- No external dependencies
- Privacy compliance

## CI/CD Integration

These tests are configured to run:
- On every pull request
- Before deployment to production
- In parallel for faster feedback
- With automatic retry on flaky tests
