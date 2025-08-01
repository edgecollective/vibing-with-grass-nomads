# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repository is currently empty except for Claude Code configuration files. When code is added to this repository, this file should be updated to include:

1. Build, test, and development commands
2. High-level architecture and structure
3. Important conventions and patterns used in the codebase
4. Any special setup or configuration requirements

## Development Logging

**IMPORTANT**: All significant development activities must be logged to `ai_agents/CLAUDE_LOG.md`. This includes:
- New features or components added
- Bug fixes and their solutions
- Refactoring activities
- Architecture changes
- Build/deployment modifications
- Test additions or changes

Each log entry should include timestamp, activity type, description, files modified, and any important context.

## Current Structure

- `.claude/` - Claude Code configuration directory
- `ai_agents/` - AI agent tooling and development logs
  - `CLAUDE_LOG.md` - Running log of all significant development activities

## Conventions and Best Practices

- Use the linux command `date` after completing any TODO list item
- When adding entries to the log, use `date` and ensure accurate timestamps for EDT timezone for each entry