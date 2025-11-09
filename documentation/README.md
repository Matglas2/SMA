# SMA Documentation

This folder contains comprehensive documentation for the SMA (Salesforce Metadata Assistant) application.

## Core Documentation

- **[requirements.md](requirements.md)** - Complete requirements tracking, feature roadmap, and evolution timeline
- **[database-design.md](database-design.md)** - Database schema design, current and planned tables
- **[implementation-plan.md](implementation-plan.md)** - Technical implementation roadmap for Salesforce integration
- **[setup.md](setup.md)** - Installation and setup guide

## Documentation Standards

All features must be documented in this folder with the following information:
- Feature name and purpose
- Command syntax and options
- Example usage
- Technical implementation details
- Database schema changes (if any)

## Implemented Features

### Phase 0: Demo Features
1. [Hello Command](features/hello-command.md) - Greet users with inspirational quotes and ASCII art

### MVP Phase 1: Authentication & Tools
2. [Salesforce Authentication](features/salesforce-authentication.md) - OAuth 2.0 connection to Salesforce orgs
3. [Interactive Simple Salesforce Session](features/interactive-session.md) - Interactive Python REPL with authenticated Salesforce client
4. [Database Browser](features/database-browser.md) - Interactive web-based database explorer
5. [Database Reset](features/database-reset.md) - Reset Salesforce metadata while preserving user data

### MVP Phase 2: Metadata Retrieval
6. [Metadata Synchronization](features/metadata-sync.md) - Download and cache Salesforce object and field metadata

### MVP Phase 3: Dependency Tracking & Analysis
7. [Analyse Commands](features/analyse-commands.md) - Query field dependencies, Flow usage, and object relationships
8. [Fuzzy Search](features/fuzzy-search.md) - Intelligent field search with fuzzy matching

## Planned Features (MVP)

See [requirements.md](requirements.md) for the complete list of planned Salesforce integration features.
