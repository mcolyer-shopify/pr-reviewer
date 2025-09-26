#!/bin/bash

# Claude Code Pre-commit Hook
# Runs linting and formatting before each commit

set -e

echo "🔍 Running pre-commit checks..."

# Format code with ruff
echo "📝 Formatting code with ruff..."
if ! uv run ruff format .; then
    echo "❌ Code formatting failed!"
    exit 1
fi

# Lint code with ruff
echo "🧹 Linting code with ruff..."
if ! uv run ruff check .; then
    echo "❌ Code linting failed!"
    echo "💡 Try running: uv run ruff check --fix ."
    exit 1
fi

# Stage any formatting changes
if [[ -n $(git diff --name-only) ]]; then
    echo "📦 Staging formatting changes..."
    git add -u
fi

echo "✅ All pre-commit checks passed!"