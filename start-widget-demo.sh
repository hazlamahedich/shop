#!/bin/bash

# Widget Demo Launcher
# Quick script to start the widget demo

echo "🎨 Widget UI/UX Demo Launcher"
echo "=============================="
echo ""

# Check if we're in the project root
if [ ! -d "frontend" ]; then
  echo "❌ Error: Please run this script from the project root directory"
  exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
  echo "📦 Installing dependencies..."
  cd frontend
  npm install
  cd ..
fi

echo "🚀 Starting development server..."
echo ""
echo "📍 Demo will be available at:"
echo "   http://localhost:5173/widget-demo"
echo ""
echo "💡 Tips:"
echo "   - Use the control panel to switch features"
echo "   - Toggle between light/dark themes"
echo "   - Try voice input (requires Chrome/Edge)"
echo "   - Drag the chat window to reposition"
echo "   - Watch for proactive triggers after 5 seconds"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dev server
cd frontend
npm run dev
