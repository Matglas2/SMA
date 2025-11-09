# Database Reset Command

**Feature Status:** ✅ Implemented
**Version:** 0.1.0
**Date Added:** 2025-11-09

## Overview

The `db reset` command provides a safe way to clear all Salesforce metadata from the database while preserving important user data like greetings, quotes, and Salesforce org connections. This is useful when you want to start fresh with metadata synchronization without losing your authentication credentials or having to reconnect to your orgs.

## Command Syntax

```bash
sma db reset [OPTIONS]
```

### Options

- `--yes`: Confirm the action without prompting (bypasses confirmation dialog)
- `--help`: Show command help and exit

### Examples

```bash
# Reset database with confirmation prompt
sma db reset

# Reset database without confirmation (useful for scripts)
sma db reset --yes
```

## Features

1. **Selective table clearing**: Only clears Salesforce metadata tables
2. **Data preservation**: Keeps greetings, quotes, and salesforce_orgs tables intact
3. **Confirmation prompt**: Requires user confirmation before executing (unless --yes is used)
4. **Detailed reporting**: Shows exactly what was cleared and what was preserved
5. **Record counting**: Displays the number of records removed and kept for each table
6. **Safe operation**: Uses transactions to ensure data integrity

## What Gets Cleared

The following Salesforce metadata tables are completely cleared:

1. `sobjects` - Salesforce object definitions
2. `fields` - Field metadata
3. `sf_field_dependencies` - Field dependency tracking
4. `sf_flow_field_references` - Flow field references
5. `sf_field_relationships` - Field relationship mappings
6. `sf_object_relationships` - Object relationship data
7. `sf_trigger_metadata` - Trigger metadata
8. `sf_flow_metadata` - Flow metadata
9. `sf_automation_coverage` - Automation coverage statistics

## What Gets Preserved

The following tables are **never** touched by the reset command:

1. `greetings` - Greeting history from the hello command
2. `quotes` - Inspirational quotes database
3. `salesforce_orgs` - Salesforce org connection information and credentials

This means you can reset and re-sync metadata without having to re-authenticate with Salesforce.

## Technical Implementation

### Files Modified/Created

- `src/sma/cli.py`: Added `db_reset()` function under the database command group (line 1154)

### Implementation Details

The reset operation:
1. Opens a database connection using the Database context manager
2. Iterates through the list of tables to clear
3. Checks if each table exists before attempting to clear it
4. Counts records in each table before deletion
5. Executes DELETE statements to clear table contents
6. Commits all changes in a single transaction
7. Reports results to the user with color-coded output

### Dependencies

- `click`: CLI framework for command handling and confirmation prompts
- `sqlite3`: Built-in Python module for database operations
- `rich.console`: For colorized terminal output

### Database Operations

```python
# For each table to clear:
1. Check existence: SELECT name FROM sqlite_master WHERE type='table' AND name=?
2. Count records: SELECT COUNT(*) as count FROM {table}
3. Clear table: DELETE FROM {table}
4. Commit transaction
```

Tables are cleared using `DELETE` statements rather than `DROP TABLE` to preserve the schema structure and indexes.

## Safety Features

1. **Confirmation Required**: By default, prompts user to confirm the operation
   - Prompt text clearly explains what will be cleared and preserved
   - Can be bypassed with `--yes` flag for automation

2. **Transaction Safety**: All deletions happen within a single database transaction
   - If any operation fails, no changes are committed
   - Database remains in consistent state

3. **Table Existence Check**: Verifies each table exists before attempting to clear it
   - Handles cases where schema hasn't been fully initialized
   - Prevents errors from missing tables

4. **Read-only Operations on Preserved Tables**:
   - Only queries preserved tables to show record counts
   - Never modifies greetings, quotes, or salesforce_orgs

## Error Handling

- Wraps all operations in try-except block
- Displays user-friendly error messages on failure
- Includes full stack trace for debugging (in error case)
- Uses `click.Abort()` to exit gracefully on errors
- Database connection automatically closed via context manager

## Use Cases

1. **Troubleshooting sync issues**: Clear corrupt or incomplete metadata
2. **Switching metadata versions**: Start fresh with a different org state
3. **Testing**: Reset to a clean state between test runs
4. **Storage management**: Clear old metadata before a fresh sync
5. **Development**: Quick reset during feature development

## Output Format

### Successful Reset

```
Resetting database...

✓ Database reset complete!

Cleared tables:
  sobjects: 1,234 records removed
  fields: 5,678 records removed
  sf_field_dependencies: 234 records removed
  [etc.]

Preserved tables:
  greetings: 15 records kept
  quotes: 10 records kept
  salesforce_orgs: 2 records kept
```

### Empty Database

```
Resetting database...

No metadata found to clear.

Preserved tables:
  greetings: 0 records kept
  quotes: 10 records kept
  salesforce_orgs: 0 records kept
```

## Integration with Other Commands

- **Before**: `sma db reset --yes`
- **After**: `sma sf sync` to re-sync metadata from Salesforce
- **Related**: `sma db stats` to view database statistics
- **Related**: `sma db browse` to explore database contents

## Future Enhancements

Potential improvements for this feature:
- Add `--tables` option to selectively clear specific tables
- Create backup before reset (automatic or optional)
- Add `--backup` flag to export data before clearing
- Dry-run mode to preview what would be cleared
- Restore from backup functionality
- Progress bar for large deletions
- Confirmation with table-by-table breakdown
- Option to preserve specific metadata types (e.g., keep flows but clear fields)
- Archive old data instead of deleting
- Database vacuum after reset to reclaim space
