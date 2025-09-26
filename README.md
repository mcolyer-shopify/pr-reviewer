# PR Code Review CLI

A CLI tool that uses AI to review GitHub Pull Requests via OpenAI-compatible APIs, based on the Gemini code review workflow from Google's GitHub Actions.

## Features

- 🔍 Fetches PR data and diffs using GitHub CLI
- 🤖 Uses OpenAI-compatible APIs for AI-powered code review
- 💾 Caches reviews to avoid redundant API calls
- 📝 Posts review comments back to GitHub
- 🎨 Rich console output with progress indicators

## Prerequisites

- [GitHub CLI](https://cli.github.com/) installed and authenticated
- Access to an OpenAI-compatible API endpoint
- Python 3.11+

## Environment Variables

The following environment variables are required:

- `OPENAI_BASE_URL`: Base URL for the OpenAI-compatible API endpoint
- `OPENAI_API_KEY`: API key for authentication (optional for some proxies, defaults to 'dummy')

### Examples:

```bash
# For OpenAI API
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-your-api-key

# For Shopify AI proxy
export OPENAI_BASE_URL=https://proxy-shopify-ai.local.shop.dev/v1

# For local LLM (like Ollama)
export OPENAI_BASE_URL=http://localhost:11434/v1
```

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### Basic Usage

Review a pull request:
```bash
uv run pr_review.py https://github.com/owner/repo/pull/123
```

### Options

- `--no-cache`: Disable caching and force fresh review
- `--dry-run`: Generate review but don't post to GitHub
- `--model MODEL`: AI model to use for review (default: google:gemini-2.5-pro)

### Examples

```bash
# Set environment variables
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-your-key

# Review a PR and post to GitHub
uv run pr_review.py https://github.com/owner/repo/pull/456

# Dry run (generate review but don't post)
uv run pr_review.py --dry-run https://github.com/owner/repo/pull/456

# Force fresh review (ignore cache)
uv run pr_review.py --no-cache https://github.com/owner/repo/pull/456

# Use a different model
uv run pr_review.py --model gpt-5 https://github.com/owner/repo/pull/456

# Combine options
uv run pr_review.py --model anthropic:claude-opus-4-1 --dry-run --no-cache https://github.com/owner/repo/pull/456
```

## How It Works

1. **Parse PR URL**: Extracts owner, repo, and PR number
2. **Fetch PR Data**: Uses `gh` CLI to get PR details, diff, and file list
3. **Cache Check**: Looks for cached review based on diff hash
4. **AI Review**: Sends data to configured OpenAI-compatible API
5. **Post Results**: Uses `gh` CLI to comment on the PR (unless `--dry-run`)

## Configuration

The AI prompt is stored in `gemini_prompt.yaml` and can be customized as needed. The prompt is based on the comprehensive code review instructions from Google's Gemini GitHub Actions workflow.

## Caching

Reviews are cached in `.cache/` directory using a hash of the PR diff. This prevents redundant API calls for the same content.

## Error Handling

- Validates PR URL format
- Checks for GitHub CLI authentication
- Validates required environment variables
- Handles API errors gracefully
- Provides clear error messages

## Development

Run in development mode:
```bash
uv run pr_review.py --help
```