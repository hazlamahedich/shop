#!/bin/bash
# WebSocket Connection Monitor
# Watches backend logs for WebSocket connection events

echo "🔍 WebSocket Connection Monitor"
echo "Watching for WebSocket events in backend logs..."
echo "Press Ctrl+C to stop"
echo ""

# Tail the backend log file or journal
tail -f /Users/sherwingorechomante/shop/backend/*.log 2>/dev/null || \
journalctl -u shop-backend -f 2>/dev/null || \
echo "No log file found. Backend may be logging to stdout."
echo ""
echo "Please run this in a separate terminal to see live logs:"
echo "  cd backend && source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
