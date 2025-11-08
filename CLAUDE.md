# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SMA (Salesforce Metadata Assistant)** is a CLI-based tool designed to help troubleshoot and analyze Salesforce environments by querying metadata, automations, and code dependencies.

### Vision
Save time during Salesforce troubleshooting by providing quick answers to metadata and dependency questions that normally require manual exploration through the Salesforce UI or metadata files.

### Current Status
Phase 0: Basic CLI prototype with demo features (hello command, quote database). The Salesforce integration features are planned for the MVP phase.

See [REQUIREMENTS.md](documentation/REQUIREMENTS.md) for complete feature roadmap and evolution timeline.

## Project Structure

```
SMA/
├── src/sma/              # Main application package
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # CLI commands using Click framework
│   └── database.py       # SQLite database management
├── documentation/        # Feature documentation (CRITICAL - see below)
│   ├── README.md         # Documentation index
│   ├── setup.md          # Installation and setup guide
│   └── features/         # Individual feature documentation
├── pyproject.toml        # Project metadata and dependencies
└── requirements.txt      # Python dependencies
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

# Run specific command
sma hello
sma hello --name "YourName"
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

- `greetings` table: Tracks hello command usage with timestamps and usernames (demo feature)
- `quotes` table: Stores inspirational quotes with text, author, and timestamp (demo feature)

For planned Salesforce metadata schema, see [DATABASE_DESIGN.md](documentation/DATABASE_DESIGN.md)

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
   - See: `documentation/features/hello-command.md`

### MVP: Salesforce Integration (📋 Planned)

The following features are planned for the MVP release:
- OAuth authentication with Salesforce
- Real-time metadata retrieval and local caching
- Field/object/flow dependency queries
- Apex code analysis and indexing
- Azure DevOps repository integration
- CLI autocomplete for Salesforce objects and fields

See [REQUIREMENTS.md](documentation/REQUIREMENTS.md) for complete MVP specifications and user requirements.

## Windows-Specific Notes

- Uses `os.environ.get('USERNAME')` for Windows username detection
- Database path uses `Path.home()` which works cross-platform but resolves to Windows user directory
- Path separators are handled by `pathlib.Path` for cross-platform compatibility
