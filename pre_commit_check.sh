#!/bin/bash
# Pre-commit validation for Task Planner

set -e

echo "🔍 Running pre-commit checks..."
echo "================================"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check Python syntax
echo "📝 Checking Python syntax..."
python3 -m py_compile app.py
echo "✅ Python syntax OK"

# Run linter if available
if command -v flake8 &> /dev/null; then
    echo "🔎 Running linter..."
    flake8 app.py --max-line-length=120 --ignore=E501,W503 || true
    echo "✅ Linter check completed"
fi

# Run quick tests
echo "🧪 Running quick tests..."
pytest tests/ -v --tb=short -x -q 2>/dev/null || {
    echo "⚠️  Some tests failed. Please review."
    pytest tests/ -v --tb=short
}

echo ""
echo "================================"
echo "✅ Pre-commit checks passed!"
