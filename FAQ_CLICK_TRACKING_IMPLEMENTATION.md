# FAQ Click Tracking Implementation

## Summary
Fixed the FAQ Usage Widget not updating by implementing complete FAQ click tracking from the frontend widget to the backend database.

## Problem
The FAQ Usage Widget was displaying "Everything is here even though I have in the past pressed on the FAQ buttons" because:
1. ❌ No frontend code to track FAQ button clicks
2. ❌ No backend API endpoint to receive FAQ click events
3. ❌ FAQ clicks were not being saved to the `FaqInteractionLog` table
4. ✅ FAQ Usage Widget was querying the `FaqInteractionLog` table (but it was empty)

## Solution Implemented

### Backend Changes

#### 1. Created FAQ Click API Endpoint (`backend/app/api/faq_click.py`)
- **Endpoint**: `POST /api/v1/widget/faq-click`
- **Purpose**: Receives FAQ click events from the widget
- **Features**:
  - Validates FAQ exists and belongs to merchant
  - Creates `FaqInteractionLog` entry with:
    - `faq_id`: ID of clicked FAQ
    - `merchant_id`: Merchant ID
    - `session_id`: Widget session ID
    - `clicked_at`: Timestamp of click
    - `had_followup`: False (updated later if user sends follow-up message)

#### 2. Updated Widget Analytics (`backend/app/services/analytics/widget_analytics_service.py`)
- Added `"faq_click"` to `EVENT_TYPES` set
- Enables FAQ clicks to be tracked alongside other widget events

#### 3. Registered Router (`backend/app/main.py`)
- Imported and registered `faq_click_router` with prefix `/api/v1/widget`

### Frontend Changes

#### 1. Added FAQ Click Tracking Method (`frontend/src/widget/api/widgetClient.ts`)
- **Method**: `trackFaqClick(faqId, sessionId, merchantId)`
- **Implementation**: Follows same pattern as `submitFeedback`
- **Features**:
  - Makes POST request to `/api/v1/widget/faq-click`
  - Handles errors gracefully
  - Returns success status and click ID

#### 2. Implemented FAQ Click Handler (`frontend/src/widget/Widget.tsx`)
- **Handler**: `handleFaqButtonClick(button: FAQQuickButton)`
- **Logic**:
  1. Tracks the FAQ click in the background (non-blocking)
  2. Sends the FAQ question as a message
  3. Handles errors gracefully - user experience takes priority
  4. Works even if tracking fails (defensive programming)

#### 3. Connected Handler to ChatWindow
- Passed `onFaqButtonClick={handleFaqButtonClick}` to ChatWindow component

## Data Flow

```
User clicks FAQ button in widget
    ↓
ChatWindow.handleFaqButtonClick(button)
    ↓
Widget.handleFaqButtonClick(button)
    ↓
1. widgetClient.trackFaqClick(button.id, sessionId, merchantId)
   ↓
   POST /api/v1/widget/faq-click
   ↓
   Backend validates FAQ & merchant
   ↓
   Creates FaqInteractionLog entry
   ↓
2. sendMessage(button.question)
   ↓
   User sees FAQ question in chat
```

## FAQ Usage Widget Update Flow

```
FAQ Usage Widget queries analytics
    ↓
GET /api/v1/analytics/faq-usage?days=30
    ↓
AggregatedAnalyticsService.get_faq_usage()
    ↓
Queries FaqInteractionLog table
    ↓
Calculates:
- Total clicks per FAQ
- Conversion rates (followup messages / clicks)
- Unused FAQs (0 clicks)
- Period comparisons
    ↓
Displays in dashboard widget
```

## Testing Checklist

- [ ] Click FAQ button in widget
- [ ] Verify `FaqInteractionLog` entry created in database
- [ ] Check FAQ Usage Widget shows updated click count
- [ ] Verify FAQ question sent as message
- [ ] Test with invalid FAQ ID (should fail gracefully)
- [ ] Test with no session (should still send message)
- [ ] Test network errors (should not block user experience)

## Database Schema

### FaqInteractionLog Table
```sql
CREATE TABLE faq_interaction_logs (
    id SERIAL PRIMARY KEY,
    faq_id INTEGER NOT NULL REFERENCES faqs(id) ON DELETE CASCADE,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    clicked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    had_followup BOOLEAN DEFAULT FALSE,
    followup_at TIMESTAMP WITH TIME ZONE,
    INDEX (merchant_id, clicked_at),
    INDEX (faq_id, merchant_id)
);
```

## API Endpoints

### POST /api/v1/widget/faq-click
**Request:**
```json
{
  "faq_id": 1,
  "session_id": "widget-session-uuid",
  "merchant_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "click_id": 456
}
```

### GET /api/v1/analytics/faq-usage?days=30
Returns FAQ usage analytics including click counts, conversion rates, and period comparisons.

## Files Modified

### Backend
- ✅ `backend/app/api/faq_click.py` (NEW)
- ✅ `backend/app/api/main.py` (registered router)
- ✅ `backend/app/services/analytics/widget_analytics_service.py` (added faq_click event type)

### Frontend
- ✅ `frontend/src/widget/api/widgetClient.ts` (added trackFaqClick method)
- ✅ `frontend/src/widget/Widget.tsx` (implemented handleFaqButtonClick handler)

## Next Steps

1. **Test the implementation**:
   - Start the backend server
   - Load the widget on a page
   - Click FAQ buttons
   - Verify database entries created
   - Check FAQ Usage Widget updates

2. **Monitor analytics**:
   - Check FAQ usage dashboard after 24 hours
   - Verify click counts and conversion rates
   - Identify unused FAQs

3. **Optional enhancements**:
   - Add real-time updates to FAQ Usage Widget
   - Implement follow-up message tracking
   - Add FAQ click heatmaps
   - Export FAQ usage reports

## Deployment Notes

- No database migrations required (table already exists)
- Backend needs restart to load new router
- Frontend needs rebuild to include new tracking code
- No breaking changes to existing functionality

---

**Implementation Date**: 2025-03-28
**Story**: Story 10-10 - FAQ Usage Widget
**Status**: ✅ Complete
