# 🚀 Server Status - RUNNING

## ✅ Both Servers Operational

**Started**: 2026-03-28 ~12:10 PM UTC

---

## 📡 Server URLs

### Backend API Server
```
🔗 URL: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
📊 OpenAPI: http://localhost:8000/openapi.json
✅ Status: Running (Process ID: 1717)
```

### Frontend Dev Server
```
🔗 URL: http://localhost:5173
🌐 Network: http://192.168.0.244:5173
✅ Status: Running (Vite v5.4.21)
```

---

## 🎯 FAQ Click Tracking Features

### Available Endpoints

**Widget API:**
- `POST /api/v1/widget/session` - Create widget session
- `GET /api/v1/widget/faq-buttons/{merchant_id}` - Get FAQ buttons
- `POST /api/v1/widget/faq-click` - **Track FAQ clicks** ⭐ NEW!

**Analytics API:**
- `GET /api/v1/analytics/faq-usage?days=30` - FAQ usage data
- `GET /api/v1/analytics/faq-usage/export?days=30` - Export CSV

---

## 🧪 Testing FAQ Click Tracking

### Option 1: Via Browser (Recommended)
1. Open http://localhost:5173
2. Navigate to your dashboard
3. Open the widget (bottom-right corner)
4. Click FAQ buttons
5. Check FAQ Usage Widget for updated data

### Option 2: Via API
```bash
# Create session
curl -X POST http://localhost:8000/api/v1/widget/session \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "2"}'

# Get FAQ buttons
curl http://localhost:8000/api/v1/widget/faq-buttons/2

# Track FAQ click
curl -X POST http://localhost:8000/api/v1/widget/faq-click \
  -H "Content-Type: application/json" \
  -d '{
    "faq_id": 1,
    "session_id": "test-session-id",
    "merchant_id": 2
  }'
```

### Option 3: Check Database
```bash
psql -U developer -h 127.0.0.1 -p 5432 -d shop_dev -c "
SELECT
    fil.id,
    f.question,
    fil.clicked_at
FROM faq_interaction_logs fil
JOIN faqs f ON f.id = fil.faq_id
ORDER BY fil.id DESC
LIMIT 10;
"
```

---

## 📊 FAQ Usage Widget Data

Once users click FAQ buttons, the widget will display:

- **Total Clicks**: Sum of all FAQ clicks
- **Average Conversion**: Follow-up messages / clicks
- **Unused FAQs**: Count of FAQs with 0 clicks
- **Per-FAQ Statistics**:
  - Click count
  - Conversion rate
  - Period comparison (change %)

---

## 🛠️ Development Tools

### Backend Logs
```bash
tail -f /tmp/backend.log
```

### Frontend Logs
```bash
tail -f /tmp/frontend.log
```

### Process Management
```bash
# Check servers
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Stop servers
pkill -f uvicorn     # Stop backend
pkill -f vite        # Stop frontend
```

---

## 📝 Notes

- **Port 173**: Requires root access, using 5173 instead
- **Database**: PostgreSQL on port 5432
- **Test Merchant**: ID 2 with 3 FAQs created
- **FAQ Click Tracking**: Fully operational and tested

---

## 🎉 Ready to Use!

**Your application is now running:**
- ✅ Backend API on http://localhost:8000
- ✅ Frontend UI on http://localhost:5173
- ✅ FAQ click tracking active
- ✅ FAQ Usage Widget ready to display data

**Start clicking those FAQ buttons and watch the analytics grow!** 📊
