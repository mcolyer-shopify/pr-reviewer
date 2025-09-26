# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--model` CLI option to specify AI model for reviews (default: google:gemini-2.5-pro)
- Support for configurable OpenAI-compatible API endpoints via `OPENAI_BASE_URL`
- Claude Code pre-commit hooks for automated linting and formatting
- Comprehensive ruff configuration for code quality enforcement
- GitHub Actions workflow for automated CI/CD linting
- Caching system for PR reviews based on diff hash
- Rich console interface with progress indicators

### Changed
- Updated docstring from "Shopify proxy" to "AI service" for broader compatibility
- Improved error messages and user feedback
- Enhanced README with configuration examples for multiple API providers

### Fixed
- Proper handling of missing filename fields in PR file data
- Code formatting and linting compliance with modern Python standards

## [1.0.0] - 2025-09-26

### Added
- Initial release of PR Code Review CLI tool
- AI-powered GitHub PR reviews using OpenAI-compatible APIs
- GitHub CLI integration for fetching PR data and posting comments
- Support for environment variable configuration (`OPENAI_BASE_URL`, `OPENAI_API_KEY`)
- Dry-run mode for testing reviews without posting
- Cache management to avoid redundant API calls
- Comprehensive documentation and usage examples
- Based on Google Gemini review workflow from GitHub Actions