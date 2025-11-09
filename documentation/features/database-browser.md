# Database Browser

**Feature Status:** ✅ Implemented
**Version:** 0.2.0
**Date Added:** 2025-11-08

## Overview

Interactive web-based database browser for exploring the SMA SQLite database. Provides a beautiful UI for viewing tables, running SQL queries, and exporting data using datasette.

## Commands

### Browse Database

```bash
# Open database browser (opens browser automatically)
sma db browse

# Specify custom port
sma db browse --port 8080

# Don't open browser (manual access)
sma db browse --no-browser
```

**What it does:**
1. Starts datasette web server
2. Opens browser to http://localhost:8001
3. Displays all tables and data
4. Allows SQL queries
5. Provides export options (JSON, CSV)

**Features:**
- 📊 Browse all tables with pagination
- 🔍 Run custom SQL queries
- 📥 Export data in multiple formats
- 🔗 View table relationships
- 📈 Generate charts and graphs (with plugins)
- 🌐 RESTful JSON API for each table

### Database Statistics

```bash
sma db stats
```

Shows:
- Database file path and size
- List of all tables
- Row count per table
- Total tables and records

**Example Output:**
```
Database Statistics

Location: C:\Users\YourName\.sma\sma.db
Size: 0.03 MB (28,672 bytes)

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Table Name         ┃ Row Count ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ greetings          │        15 │
│ quotes             │        10 │
│ salesforce_orgs    │         1 │
└────────────────────┴───────────┘

Total Tables: 3
Total Records: 26
```

### Database Path

```bash
sma db path
```

Displays the full path to the database file. Useful for:
- Opening in external tools (DB Browser for SQLite, etc.)
- Backup and restore operations
- Sharing database location

## Technical Implementation

### Dependencies

**datasette** (v1.0.0+)
- Web-based SQLite browser
- Built-in SQL editor
- JSON API
- Export capabilities

### Files Modified

- `requirements.txt` - Added datasette dependency
- `src/sma/cli.py` - Added `db` command group with 3 subcommands

### Architecture

**db browse command:**
1. Checks if database file exists
2. Launches datasette as subprocess
3. Passes database path and port
4. Opens browser automatically (unless --no-browser)
5. Runs until user presses Ctrl+C

**db stats command:**
1. Opens database connection
2. Queries sqlite_master for table list
3. Counts rows in each table
4. Displays formatted output using rich

**db path command:**
1. Constructs database path from user home directory
2. Checks if file exists
3. Shows file size if exists

## Usage Examples

### Exploring the Database

```bash
# 1. Open browser
sma db browse

# Browser opens to http://localhost:8001
# Click on tables to browse:
# - greetings: View all hello command usage
# - quotes: Browse inspirational quotes
# - salesforce_orgs: See connected Salesforce orgs

# 2. Run custom SQL query
# Click "SQL" tab in datasette
# Enter query:
SELECT username, COUNT(*) as greet_count
FROM greetings
GROUP BY username
ORDER BY greet_count DESC

# 3. Export data
# Click table → "Download as CSV" or "Download as JSON"
```

### Checking Database Size

```bash
# See database growth over time
sma db stats

# After syncing Salesforce metadata, check again
sma sf sync  # (Phase 2 feature)
sma db stats  # Will show new tables and counts
```

### Using External Tools

```bash
# Get database path
sma db path

# Copy path and open in:
# - DB Browser for SQLite
# - DBeaver
# - DataGrip
# - Any SQLite client
```

## Datasette Features

### Built-in Capabilities

1. **Table Browsing**
   - Paginated results
   - Column sorting
   - Faceted search
   - Full-text search

2. **SQL Queries**
   - Interactive SQL editor
   - Query history
   - Saved queries
   - Syntax highlighting

3. **Data Export**
   - CSV format
   - JSON format
   - Advanced JSON (with structure)

4. **API Access**
   - JSON API for each table
   - RESTful endpoints
   - Query parameters for filtering
   - Pagination support

### Example API Endpoints

When datasette is running:

```bash
# Get all quotes as JSON
http://localhost:8001/sma.json?sql=SELECT+*+FROM+quotes

# Get active Salesforce org
http://localhost:8001/sma/salesforce_orgs.json?is_active=1

# Count greetings by user
http://localhost:8001/sma.json?sql=SELECT+username,+COUNT(*)+FROM+greetings+GROUP+BY+username
```

### Datasette Plugins (Optional)

You can extend datasette with plugins:

```bash
# Install useful plugins
pip install datasette-vega  # Charts and graphs
pip install datasette-cluster-map  # Geographic data
pip install datasette-copyable  # Copy data to clipboard
pip install datasette-export-notebook  # Export to Jupyter

# Then browse with plugins available
sma db browse
```

## Security Considerations

1. **Local only:** Datasette runs on localhost (127.0.0.1)
2. **No authentication:** Database is exposed to all local users while running
3. **Read-write access:** Datasette can modify data (use caution)
4. **Port binding:** Only binds to localhost, not accessible from network

## Troubleshooting

### "datasette is not installed"
```bash
pip install datasette
# or
pip install -r requirements.txt
```

### Port already in use
```bash
# Use different port
sma db browse --port 8080
```

### Browser doesn't open
```bash
# Open manually
sma db browse --no-browser
# Then visit: http://localhost:8001
```

### Permission errors
- Ensure database file is not locked by another process
- Close other applications accessing the database

## Alternatives

If you prefer different tools:

1. **DB Browser for SQLite**
   - Download: https://sqlitebrowser.org/
   - GUI desktop application
   - More features than datasette

2. **sqlite-web**
   ```bash
   pip install sqlite-web
   sqlite-web ~/.sma/sma.db
   ```

3. **DBeaver** (Universal database tool)
   - Download: https://dbeaver.io/
   - Professional database IDE

4. **Command-line SQLite**
   ```bash
   sqlite3 ~/.sma/sma.db
   .tables
   SELECT * FROM quotes;
   ```

## Future Enhancements

### Planned
- Custom datasette plugins for SMA
- Metadata dependency graphs
- Pre-configured useful queries
- Database backup/restore commands
- Automatic datasette config generation

### Possible Additions
- `sma db query <sql>` - Run SQL from command line
- `sma db export <table>` - Export specific table
- `sma db vacuum` - Optimize database
- `sma db backup` - Create backup copy

## Related Commands

- `sma sf status` - Check which org's data is in database
- `sma sf list` - See all connected orgs (stored in database)
- Future: `sma sf sync` - Populate database with Salesforce metadata
