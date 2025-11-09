# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SMA (Salesforce Metadata Assistant)** is a CLI-based tool designed to help troubleshoot and analyze Salesforce environments by querying metadata, automations, and code dependencies.

### Vision
Save time during Salesforce troubleshooting by providing quick answers to metadata and dependency questions that normally require manual exploration through the Salesforce UI or metadata files.

### Current Status
**Phase 3 Complete**: Dependency tracking and analysis commands are now fully implemented. The tool can:
- Connect to Salesforce orgs via OAuth (with PKCE)
- Sync metadata including objects, fields, Flows, and Triggers
- Parse Flow XML to extract field references
- Track field relationships (lookups, master-detail)
- Query field dependencies using the `analyse` command group
- Browse all data using web-based database interface

**Latest Features:**
- `sma sf analyse field-flows` - Show which Flows use a specific field
- `sma sf analyse field-triggers` - Show Triggers on an object
- `sma sf analyse field-deps` - Show all dependencies for a field
- `sma sf analyse flow-fields` - Show all fields used by a Flow
- `sma sf analyse object-relationships` - Display relationship graph

See [requirements.md](documentation/requirements.md) for complete feature roadmap and evolution timeline.

## Project Structure

```
SMA/
├── src/sma/                    # Main application package
│   ├── __init__.py             # Package initialization
│   ├── cli.py                  # CLI commands using Click framework
│   ├── database.py             # SQLite database management
│   ├── interactive_session.py  # Interactive Simple Salesforce REPL
│   ├── parsers/                # Metadata parsers
│   │   ├── __init__.py         # Package initialization
│   │   └── flow_parser.py      # Flow XML parser for field extraction
│   └── salesforce/             # Salesforce integration modules
│       ├── __init__.py         # Package initialization
│       ├── auth.py             # OAuth authentication with PKCE
│       ├── connection.py       # Connection and credential management
│       └── metadata.py         # Metadata retrieval and sync
├── documentation/              # Feature documentation (CRITICAL - see below)
│   ├── README.md               # Documentation index
│   ├── setup.md                # Installation and setup guide
│   ├── requirements.md         # Product requirements and roadmap
│   ├── database-design.md      # Database schema documentation
│   ├── implementation-plan.md  # Implementation phases and status
│   └── features/               # Individual feature documentation
│       ├── hello-command.md
│       ├── salesforce-authentication.md
│       ├── interactive-session.md
│       ├── metadata-sync.md
│       ├── database-browser.md
│       └── analyse-commands.md
├── pyproject.toml              # Project metadata and dependencies
└── requirements.txt            # Python dependencies
```

## Development Setup

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Run Commands

```bash
# Show all commands
sma --help

# Demo commands
sma hello
sma hello --name "YourName"

# Salesforce commands
sma sf connect --alias myorg --client-id <CLIENT_ID> --client-secret <CLIENT_SECRET>
sma sf list
sma sf sync

# Interactive Salesforce session
sma ss                      # Start interactive Python session with Salesforce client
sma ss --alias myorg        # Use specific org

# Analysis commands (Phase 3)
sma sf analyse field-flows Account Email
sma sf analyse field-deps Contact Phone
sma sf analyse flow-fields "My Flow Name"
sma sf analyse object-relationships Account

# Database browser
sma db browse
```

## Development Workflow

### Standard Workflow for Feature Changes

**IMPORTANT**: After implementing any feature or change and receiving user approval:

1. **Create a feature branch**
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. **Commit changes with descriptive message**
   ```bash
   git add <files>
   git commit -m "Brief description

   Detailed explanation of changes...

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

3. **Push to remote**
   ```bash
   git push -u origin feature/descriptive-name
   ```

4. **Create Pull Request**
   - Visit the PR URL provided by git push output
   - Or use `gh pr create` if GitHub CLI is available
   - Include summary, changes made, and test plan in PR description

5. **Merge after review**
   - User reviews and merges the PR on GitHub

This workflow ensures:
- All changes are reviewed before merging to main
- Clear history of what was changed and why
- Easy rollback if needed
- Proper collaboration practices

## Database

- **Technology**: SQLite3 (built-in Python module)
- **Location**: `~/.sma/sma.db` (user's home directory on Windows: `C:\Users\<Username>\.sma\sma.db`)
- **Auto-initialization**: Database and tables are created automatically on first use
- **Management**: All database operations are in `src/sma/database.py`

### Current Schema

**Demo Features:**
- `greetings` table: Tracks hello command usage with timestamps and usernames
- `quotes` table: Stores inspirational quotes with text, author, and timestamp

**Salesforce Integration:**
- `sf_connections` table: Stores connected org information and metadata
- `sf_custom_objects` table: Salesforce custom and standard objects
- `sf_custom_fields` table: Custom fields with metadata
- `sf_flows` table: Flow definitions and versions
- `sf_process_builders` table: Process Builder metadata
- `sf_validation_rules` table: Validation rules
- `sf_apex_classes` table: Apex class definitions
- `sf_apex_triggers` table: Apex trigger definitions

For complete schema details, see [database-design.md](documentation/database-design.md)

## CLI Framework

- **Framework**: Click (https://click.palletsprojects.com/)
- **Main entry point**: `src/sma/cli.py::main()`
- **Command decorator**: Use `@main.command()` to add new commands
- **Styling**: Click provides color/style functions (`click.style()`, `click.echo()`)

## 🚨 CRITICAL: Documentation Requirements

**ALL FEATURES MUST BE DOCUMENTED IN THE `documentation/` FOLDER.**

### When Adding New Features:

1. **Create feature documentation** in `documentation/features/<feature-name>.md` with:
   - Feature overview and purpose
   - Command syntax and options
   - Usage examples
   - Technical implementation details
   - Database schema changes (if any)
   - Files created/modified

2. **Update the feature index** in `documentation/README.md`

3. **Use the existing documentation as a template**: See `documentation/features/hello-command.md` for the standard format

### Documentation Format

Each feature document should include:
- **Feature Status**: ✅ Implemented / 🚧 In Progress / 📋 Planned
- **Version**: When it was added
- **Date Added**: ISO format (YYYY-MM-DD)
- **Overview**: What the feature does
- **Command Syntax**: Full command with options
- **Examples**: Real usage examples
- **Technical Implementation**: Files, database schema, dependencies
- **Error Handling**: How failures are managed
- **Future Enhancements**: Potential improvements

## Architecture Notes

### Adding New CLI Commands

1. Define command function in `src/sma/cli.py`
2. Use `@main.command()` decorator
3. Add Click options with `@click.option()`
4. Access database using `with Database() as db:` context manager
5. Use `click.echo()` and `click.style()` for output
6. **Document in `documentation/features/`**

### Adding Database Tables

1. Add schema in `Database._initialize_schema()` method in `src/sma/database.py`
2. Use `CREATE TABLE IF NOT EXISTS` for idempotency
3. Document schema in feature documentation

### Code Style

- Follow PEP 8 conventions
- Use type hints where appropriate
- Include docstrings for all functions and classes
- Handle errors gracefully (especially database operations)

## Current Features

### Phase 0: Demo Features (✅ Implemented)

1. **hello command** (`sma hello`): Greets users with personalized messages, random inspiring quotes from database, and ASCII art. Logs greetings to database.
   - See: [hello-command.md](documentation/features/hello-command.md)

### Phase 1: Salesforce OAuth Authentication (✅ Implemented)

**Commands:**
- `sma sf connect` - Authenticate with Salesforce org using OAuth 2.0 with PKCE
- `sma sf disconnect` - Remove stored credentials for an org
- `sma sf list` - List all connected Salesforce orgs
- `sma ss` - Start interactive Simple Salesforce session with authenticated client

**Features:**
- OAuth 2.0 authentication flow with PKCE (RFC 7636)
- Secure credential storage using system keyring
- Multi-org support with connection aliases
- Token refresh functionality
- Support for both production and sandbox environments
- Interactive Python REPL with pre-configured Salesforce client and helper functions

See: [salesforce-authentication.md](documentation/features/salesforce-authentication.md) and [interactive-session.md](documentation/features/interactive-session.md)

### Phase 2: Metadata Synchronization (✅ Implemented)

**Commands:**
- `sma sf sync` - Sync metadata from Salesforce to local database
- `sma sf browse` - Launch web-based database browser (datasette)

**Features:**
- Real-time metadata retrieval via Salesforce REST and Tooling APIs
- Local SQLite caching for offline access
- Incremental sync with last-modified tracking
- Support for: Custom Objects, Fields, Flows, Process Builders, Validation Rules, Apex Classes/Triggers
- Interactive database browser with search and export capabilities

See: [metadata-sync.md](documentation/features/metadata-sync.md) and [database-browser.md](documentation/features/database-browser.md)

### Future Phases (📋 Planned)

The following features are planned for future releases:
- Field/object/flow dependency graph visualization
- Apex code analysis and indexing
- Impact analysis for field and object changes
- Azure DevOps repository integration
- CLI autocomplete for Salesforce objects and fields
- Automated change documentation

See [requirements.md](documentation/requirements.md) for complete roadmap and specifications.

## Windows-Specific Notes

- Uses `os.environ.get('USERNAME')` for Windows username detection
- Database path uses `Path.home()` which works cross-platform but resolves to Windows user directory
- Path separators are handled by `pathlib.Path` for cross-platform compatibility
