#!/bin/bash
# NEXTRADER — One-command setup
set -e

echo "🚀 Setting up NEXTRADER..."

# Backend
echo "📦 Installing Python dependencies..."
cd backend
cp .env.example .env 2>/dev/null || true
pip install -r requirements.txt --quiet

echo "✅ Backend ready. Run with:"
echo "   cd backend && uvicorn main:app --reload"
echo ""

# Frontend
echo "📦 Installing Node dependencies..."
cd ../frontend
npm install --silent

echo "✅ Frontend ready. Run with:"
echo "   cd frontend && npm run dev"
echo ""
echo "─────────────────────────────────────────"
echo "  NEXTRADER Phase 1 setup complete!"
echo "  Backend  → http://localhost:8000"
echo "  API docs → http://localhost:8000/docs"
echo "  Frontend → http://localhost:5173"
echo "─────────────────────────────────────────"
