# Interactive Simple Salesforce Session

**Feature Status:** ✅ Implemented
**Version:** 0.1.0
**Date Added:** 2025-11-09

## Overview

The `ss` command starts an interactive Python session with an authenticated Simple Salesforce client. This allows developers to explore Salesforce data, test SOQL queries, and interact with the Salesforce API in real-time without writing separate scripts.

The session provides both a raw Simple Salesforce client (`sf`) and convenient helper functions for common operations like querying, describing objects, and searching.

## Command Syntax

```bash
sma ss [OPTIONS]
```

### Options

- `--alias TEXT`: Salesforce org alias (uses active org if not specified)

### Examples

```bash
# Start session with active org
sma ss

# Start session with specific org
sma ss --alias production

# Start session with sandbox org
sma ss --alias sandbox
```

## Features

1. **Authenticated Salesforce client**: Reuses existing OAuth credentials from `sma sf connect`
2. **Helper functions**: Convenience functions for common operations
3. **IPython support**: Uses IPython if available for better interactive experience
4. **Fallback console**: Falls back to standard Python console if IPython not installed
5. **Rich formatted output**: Color-coded success/error messages
6. **Multi-org support**: Switch between different orgs using `--alias` option

## Interactive Session Objects

### sf (Salesforce Client)

The main Simple Salesforce client object. Use this to access any Salesforce API functionality.

```python
# Access SObject types directly
sf.Account
sf.Contact
sf.Opportunity

# Create records
sf.Account.create({'Name': 'Test Account'})

# Update records
sf.Account.update('001XXXXXXXXXXXXXXX', {'Name': 'Updated Name'})

# Delete records
sf.Account.delete('001XXXXXXXXXXXXXXX')

# Get object metadata
sf.Account.describe()

# Get record by ID
sf.Account.get('001XXXXXXXXXXXXXXX')
```

### query(soql)

Execute SOQL queries with formatted output.

```python
# Query records
query('SELECT Id, Name FROM Account LIMIT 10')

# Complex queries
query('''
    SELECT Id, Name, (SELECT Id, FirstName, LastName FROM Contacts)
    FROM Account
    WHERE Industry = 'Technology'
    ORDER BY Name
    LIMIT 5
''')

# Returns query result with totalSize
```

### describe(sobject_name)

Describe Salesforce objects with formatted metadata display.

```python
# Describe standard object
describe('Account')

# Describe custom object
describe('MyCustomObject__c')

# Returns full describe result
```

### get_record(sobject_name, record_id)

Retrieve a specific record by ID.

```python
# Get Account record
get_record('Account', '001XXXXXXXXXXXXXXX')

# Get custom object record
get_record('MyCustomObject__c', 'a00XXXXXXXXXXXXXXX')

# Returns full record data
```

### search(sosl)

Execute SOSL searches.

```python
# Search across all fields
search('FIND {John} IN ALL FIELDS')

# Search in specific fields
search('FIND {Acme} IN NAME FIELDS RETURNING Account(Id, Name)')

# Returns search results
```

## Technical Implementation

### Files Created

- `src/sma/interactive_session.py`: Interactive session logic with helper functions
- Updated `src/sma/cli.py`: Added `ss` command at main level (not in `sf` group)

### Architecture

1. **Command Entry Point** (`cli.py`):
   - Validates org connection
   - Retrieves authenticated Salesforce client from `SalesforceConnection`
   - Launches interactive session

2. **Session Handler** (`interactive_session.py`):
   - Displays welcome message with org information
   - Defines helper functions (query, describe, get_record, search)
   - Creates namespace with `sf` client and helper functions
   - Attempts to use IPython for better UX, falls back to standard Python console

### Dependencies

- `simple_salesforce`: Salesforce API client (already used by authentication)
- `rich`: Terminal formatting for colored output
- `IPython` (optional): Enhanced interactive console experience
- Existing authentication infrastructure from `salesforce/auth.py` and `salesforce/connection.py`

### Reused Components

This feature leverages the existing authentication architecture:

- `SalesforceAuth`: OAuth 2.0 with PKCE flow
- `SalesforceConnection`: Connection management and credential storage
- `Database`: Org tracking and active connection status
- System keyring: Secure credential storage

## Usage Workflow

1. **Connect to Salesforce** (one-time setup):
   ```bash
   sma sf connect --alias production --client-id YOUR_ID --client-secret YOUR_SECRET
   ```

2. **Start Interactive Session**:
   ```bash
   sma ss
   ```

3. **Interact with Salesforce**:
   ```python
   # Query data
   >>> result = query('SELECT Id, Name FROM Account LIMIT 5')
   ✓ Query successful - 5 record(s) found

   # Inspect results
   >>> result['records']
   [{'attributes': {...}, 'Id': '001...', 'Name': 'Acme Corp'}, ...]

   # Describe objects
   >>> describe('Contact')
   ✓ Object: Contact
     API Name: Contact
     Fields: 67
     Createable: True

   # Direct API access
   >>> sf.Contact.create({'LastName': 'Smith', 'Email': 'smith@example.com'})
   {'id': '003XXXXXXXXXXXXXXX', 'success': True, 'errors': []}
   ```

4. **Exit Session**:
   ```python
   >>> exit()
   ```
   Or press `Ctrl+D`

## Error Handling

- **No active connection**: Displays error message and suggests running `sma sf connect`
- **Org not found**: Shows list command to see available orgs
- **Expired session**: Provides reconnection instructions with example command
- **Query/API errors**: Catches exceptions and displays formatted error messages
- **Keyboard interrupt**: Gracefully exits session with success message

## Security Considerations

- Credentials are never exposed in the session
- Uses existing keyring storage for tokens
- OAuth tokens are refreshed automatically when possible
- No credentials stored in session history or IPython history files

## IPython vs Standard Console

### With IPython (Recommended)
- Syntax highlighting
- Tab completion
- Multi-line editing
- Rich output formatting
- Command history with persistent storage

### Without IPython (Fallback)
- Standard Python REPL
- Basic line editing
- No syntax highlighting
- All helper functions still work

To install IPython:
```bash
pip install ipython
```

## Example Session

```python
═══════════════════════════════════════════════════════════
Simple Salesforce Interactive Session
═══════════════════════════════════════════════════════════

Connected to: production
Instance URL: https://mycompany.my.salesforce.com

Available objects:
  sf          - Authenticated Salesforce client
  query       - Execute SOQL query: query('SELECT Id FROM Account LIMIT 10')
  describe    - Describe an object: describe('Account')
  get_record - Get a record: get_record('Account', record_id)
  search      - Execute SOSL search: search('FIND {John} IN ALL FIELDS')

Examples:
  # Query records
  >>> query('SELECT Id, Name FROM Account LIMIT 5')

  # Describe object
  >>> describe('Contact')

  # Access SObject directly
  >>> sf.Account.create({'Name': 'Test Account'})

  # Get metadata
  >>> sf.Account.describe()

Type 'exit()' or Ctrl+D to quit
═══════════════════════════════════════════════════════════

>>> # Start interacting with Salesforce!
```

## Future Enhancements

Potential improvements for this feature:

- Auto-completion for SObject names and field names
- Query history persistence across sessions
- Export query results to CSV/JSON files
- Bulk operation helpers (bulk_create, bulk_update)
- Session recording and playback
- SOQL query builder/validator
- Pre-loaded common queries based on org metadata
- Integration with metadata sync for offline field validation
- Custom REPL commands (e.g., `.tables`, `.fields Account`)
- Query performance metrics and optimization suggestions
