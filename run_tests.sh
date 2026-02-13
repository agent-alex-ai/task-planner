#!/bin/bash
# Run Task Planner tests

set -e

echo "🧪 Running Task Planner Tests..."
echo "================================"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
pip install pytest pytest-flask pytest-cov -q

# Run tests
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "================================"
echo "✅ Tests completed!"
echo ""
echo "Coverage report: htmlcov/index.html"
