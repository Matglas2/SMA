# Fuzzy Search for Fields

**Feature Status:** ✅ Implemented
**Version:** 0.1.0
**Date Added:** 2025-11-09

## Overview

The `sma sf search` command provides fuzzy search capabilities for finding Salesforce fields by name or label. It uses intelligent string matching algorithms to find relevant fields even when you don't know the exact field name, making it easy to quickly locate fields across all objects in your Salesforce org.

## Command Syntax

```bash
sma sf search QUERY [OPTIONS]
```

### Arguments

- `QUERY` (required): The search term to match against field names and labels

### Options

- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--limit INTEGER`: Maximum number of results to display (default: 20)
- `--threshold INTEGER`: Minimum match score threshold from 0-100 (default: 60)
- `--format [table|json]`: Output format (default: table)
- `--search-in [all|name|label]`: Where to search - field name, label, or both (default: all)

### Examples

```bash
# Find all email-related fields
sma sf search email

# Find date fields
sma sf search "created date"

# Show only top 10 matches
sma sf search phone --limit 10

# Only show matches above 70% similarity
sma sf search addr --threshold 70

# Search only in field labels
sma sf search name --search-in label

# Output as JSON
sma sf search acc --format json

# Search in a specific org
sma sf search status --alias production
```

## Features

1. **Fuzzy matching**: Finds fields even with typos or partial matches
2. **Score-based ranking**: Results sorted by relevance (100% = perfect match)
3. **Flexible search**: Search in field names, labels, or both
4. **Customizable threshold**: Filter out low-quality matches
5. **Multi-format output**: Table view for humans, JSON for scripts
6. **Context information**: Shows object name, field type, and whether field is custom
7. **Color-coded scores**: Visual indication of match quality (green = excellent, yellow = good, dim = marginal)

## Technical Implementation

### Files Modified/Created

- `src/sma/cli.py`: Added `sf_search` command function with fuzzy matching logic
- `requirements.txt`: Added `rapidfuzz>=3.0.0` dependency

### Dependencies

- `rapidfuzz`: Fast fuzzy string matching library
- `click`: CLI framework for command handling
- `rich`: Beautiful terminal formatting and tables
- `sqlite3`: Database queries for field metadata

### Algorithm

The search uses **partial ratio matching** from the rapidfuzz library:

1. Fetches all fields from the database for the specified org
2. Constructs search text from field names and/or labels based on `--search-in` option
3. Calculates similarity score using `fuzz.partial_ratio()` (case-insensitive)
4. Filters results based on threshold (default 60%)
5. Sorts results by score (descending)
6. Limits output to top N results (default 20)

### Database Queries

The command queries the following tables:
- `fields`: Field metadata (api_name, label, type, is_custom, help_text)
- `sobjects`: Object metadata (joined for object names and labels)

Query joins fields with sobjects to provide complete context:
```sql
SELECT
    f.api_name,
    f.label,
    f.type,
    s.api_name as object_name,
    s.label as object_label,
    f.is_custom,
    f.help_text
FROM fields f
JOIN sobjects s ON f.sobject_salesforce_id = s.salesforce_id
WHERE f.org_id = ?
```

### Match Scoring

- **90-100%**: Perfect or near-perfect match (bold green)
- **75-89%**: Very good match (green)
- **60-74%**: Good match (yellow)
- **0-59%**: Below threshold (filtered out by default)

## Output Format

### Table Format (Default)

Displays results in a formatted table with:
- **Score**: Match quality percentage (color-coded)
- **Object**: Salesforce object API name
- **Field Name**: Field API name
- **Label**: Human-readable field label
- **Type**: Field data type (Text, Number, DateTime, etc.)
- **Custom**: Checkmark (✓) if custom field

Summary information includes:
- Total matches found
- Total fields searched
- Search query
- Threshold percentage

### JSON Format

Machine-readable output for scripting/automation:
```json
[
  {
    "object_name": "Account",
    "object_label": "Account",
    "field_name": "Email__c",
    "field_label": "Email Address",
    "type": "Email",
    "is_custom": true,
    "help_text": "Primary contact email",
    "match_score": 95
  }
]
```

## Error Handling

- **No active connection**: Prompts user to run `sma sf connect`
- **Unknown org alias**: Displays error message with org name
- **No fields in database**: Instructs user to run `sma sf sync`
- **No matches**: Suggests lowering threshold with `--threshold` option
- **Database errors**: Displays error with traceback for debugging

## Use Cases

1. **Quick field lookup**: Find fields when you only remember part of the name
2. **Discovery**: Explore what fields exist related to a concept (e.g., "address", "date")
3. **Documentation**: Identify fields mentioned in requirements or documentation
4. **Impact analysis**: Find all fields related to a feature before making changes
5. **Automation**: Script field searches with JSON output for downstream processing

## Performance Considerations

- Search is performed in-memory after loading all fields from database
- For large orgs (10,000+ fields), search may take 1-2 seconds
- Results are limited to prevent overwhelming output
- Database query uses indexes on `org_id` and `sobject_salesforce_id`

## Future Enhancements

Potential improvements for this feature:
- Search across other metadata types (objects, flows, classes)
- Save frequent searches as aliases
- Search history with recent queries
- Export results to CSV or Excel
- Regex pattern matching support
- Search within field help text and descriptions
- Cross-object relationship search
- Integration with `analyse` commands to show dependencies for search results
- Cached search results for faster repeated queries
- Highlight matched portions of field names/labels in results
