# Analyse Commands

**Feature Status:** ✅ Implemented
**Version:** 0.3.0
**Date Added:** 2025-01-09
**Phase:** Phase 3 - Dependency Tracking

## Overview

The `sma sf analyse` command group provides powerful analysis capabilities for understanding Salesforce metadata dependencies and relationships. These commands query the local database to answer common troubleshooting questions about field usage, automation coverage, and object relationships.

**Key Capabilities:**
- Identify which Flows use specific fields
- Show which Triggers run on specific objects
- Display all dependencies for a field
- List all fields used by a Flow
- Map object relationships (lookup, master-detail)

## Prerequisites

Before using analyse commands, you must:

1. **Connect to Salesforce:**
   ```bash
   sma sf connect --alias production --client-id YOUR_ID --client-secret YOUR_SECRET
   ```

2. **Sync metadata:**
   ```bash
   sma sf sync
   ```
   This populates the local database with metadata, including Flow definitions, Trigger metadata, and field relationships.

## Command Syntax

All analyse commands are subcommands of `sma sf analyse`:

```bash
sma sf analyse <command> [OPTIONS] [ARGUMENTS]
```

## Available Commands

### 1. field-flows

**Purpose:** Show which Flows use a specific field

**Syntax:**
```bash
sma sf analyse field-flows <OBJECT_NAME> <FIELD_NAME> [OPTIONS]
```

**Options:**
- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--format [table|json]`: Output format (default: table)

**Examples:**
```bash
# Show which flows use the Account Email field
sma sf analyse field-flows Account Email

# Query specific org
sma sf analyse field-flows Opportunity StageName --alias production

# Get JSON output for scripting
sma sf analyse field-flows Contact Phone --format json
```

**Output:**
- Table format: Shows Flow name, element name, element type, usage (Read/Write), and status
- JSON format: Structured data including flow metadata and field reference details

**What it shows:**
- Flow name and active status
- Specific Flow element using the field (e.g., "Get_Account_Record", "Update_Contact")
- Element type (recordLookup, recordUpdate, recordCreate, decision, assignment)
- Whether the field is read (input) or written (output)
- Flow process type and trigger type

### 2. field-triggers

**Purpose:** Show which Apex Triggers reference a specific field

**Syntax:**
```bash
sma sf analyse field-triggers <OBJECT_NAME> <FIELD_NAME> [OPTIONS]
```

**Options:**
- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--format [table|json]`: Output format (default: table)

**Examples:**
```bash
# Show triggers on Account object
sma sf analyse field-triggers Account Email

# Get JSON output
sma sf analyse field-triggers Opportunity Amount --format json
```

**Output:**
- Trigger name
- DML events (BI=Before Insert, BU=Before Update, AI=After Insert, etc.)
- Last modified date

**Note:** This currently shows all active triggers on the object. Field-level Apex code parsing will be added in Phase 4 to show exactly which triggers reference specific fields.

### 3. field-deps

**Purpose:** Show all dependencies for a specific field (comprehensive view)

**Syntax:**
```bash
sma sf analyse field-deps <OBJECT_NAME> <FIELD_NAME> [OPTIONS]
```

**Options:**
- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--format [table|json]`: Output format (default: table)

**Examples:**
```bash
# Show all dependencies for Account Email
sma sf analyse field-deps Account Email

# Query specific org with JSON output
sma sf analyse field-deps Contact Phone --alias sandbox --format json
```

**Output:**
- Dependency type (flow, trigger, validation_rule, etc.)
- Dependency name
- Reference type (read, write, filter)
- Last verified timestamp

**Summary section** shows count by type:
```
Summary:
  flow: 3
  trigger: 1
  validation_rule: 2
```

**Use Cases:**
- Impact analysis before field deletion
- Understanding field usage across automation
- Identifying unused fields

### 4. flow-fields

**Purpose:** Show all fields used by a specific Flow

**Syntax:**
```bash
sma sf analyse flow-fields <FLOW_NAME> [OPTIONS]
```

**Options:**
- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--format [table|json]`: Output format (default: table)

**Arguments:**
- `FLOW_NAME`: Flow API name or label (supports partial matching)

**Examples:**
```bash
# Show fields used in a flow
sma sf analyse flow-fields "Account Update Flow"

# Partial name matching
sma sf analyse flow-fields MyFlow

# JSON output
sma sf analyse flow-fields OpportunityScoring --format json
```

**Output:**
- Object.Field combinations
- Element name using the field
- Element type (recordLookup, recordUpdate, etc.)
- Usage (Read, Write, or both)
- Variable name (if field is assigned to a variable)

**Use Cases:**
- Understanding Flow complexity and field dependencies
- Documenting Flow behavior
- Field impact analysis before changes

### 5. object-relationships

**Purpose:** Show relationship graph for a Salesforce object

**Syntax:**
```bash
sma sf analyse object-relationships <OBJECT_NAME> [OPTIONS]
```

**Options:**
- `--alias TEXT`: Salesforce org alias (uses active org if not specified)
- `--direction [all|parent|child]`: Relationship direction (default: all)
- `--format [table|json]`: Output format (default: table)

**Examples:**
```bash
# Show all relationships for Account
sma sf analyse object-relationships Account

# Show only parent relationships (lookups/master-details pointing up)
sma sf analyse object-relationships Contact --direction parent

# Show only child relationships (objects that reference this one)
sma sf analyse object-relationships Opportunity --direction child

# JSON output for API integration
sma sf analyse object-relationships Case --format json
```

**Output:**
- Direction icon (⬆ Parent / ⬇ Child)
- Field name
- Relationship type (lookup, master_detail, external_lookup)
- Related object
- Relationship name (for SOQL queries)
- Cascade delete setting

**Use Cases:**
- Understanding object dependencies
- Data modeling and ERD documentation
- Planning data migration or deletion
- SOQL query planning (knowing relationship names)

## Output Formats

### Table Format (Default)

Formatted table output optimized for terminal display:
- Color-coded columns
- Aligned rows
- Summary statistics
- Easy to read

### JSON Format

Structured data output for:
- Scripting and automation
- Integration with other tools
- Programmatic processing
- CI/CD pipelines

Example JSON output:
```json
[
  {
    "flow_name": "Account_Email_Validation",
    "element_name": "Get_Account",
    "element_type": "recordLookup",
    "is_input": true,
    "is_output": false,
    "is_active": true
  }
]
```

## Technical Implementation

### Database Tables Used

The analyse commands query Phase 3 database tables:

1. **sf_field_dependencies**: Central dependency tracking
2. **sf_flow_field_references**: Detailed flow-field mappings
3. **sf_flow_metadata**: Flow metadata and status
4. **sf_trigger_metadata**: Trigger inventory
5. **sf_field_relationships**: Field-level relationships
6. **sf_object_relationships**: Object-level relationships

### Performance

- All queries use indexed columns for fast lookups
- Queries typically complete in <100ms even with large metadata sets
- No Salesforce API calls required (queries local database)

### Data Freshness

Analyse commands query the local database synced via `sma sf sync`. To ensure accuracy:

```bash
# Sync metadata to get latest changes
sma sf sync

# Then run analyse commands
sma sf analyse field-flows Account Email
```

## Common Workflows

### Impact Analysis Before Field Deletion

```bash
# Check all dependencies
sma sf analyse field-deps Account CustomField__c

# Check specific automation types
sma sf analyse field-flows Account CustomField__c
sma sf analyse field-triggers Account CustomField__c
```

### Documenting a Flow

```bash
# List all fields used
sma sf analyse flow-fields "My Complex Flow"

# Understand object relationships involved
sma sf analyse object-relationships Account
sma sf analyse object-relationships Contact
```

### Understanding Object Data Model

```bash
# See all relationships
sma sf analyse object-relationships Account

# See only parent lookups
sma sf analyse object-relationships Contact --direction parent

# See child relationships
sma sf analyse object-relationships Account --direction child
```

### Finding Unused Fields

Combine with field list queries:
```bash
# 1. Get all fields for an object (using db browse or direct query)
# 2. For each field, check dependencies:
sma sf analyse field-deps Account Field1__c
sma sf analyse field-deps Account Field2__c
# 3. Fields with no dependencies may be candidates for cleanup
```

## Error Handling

### "No active Salesforce connection"
```bash
# Connect first
sma sf connect --alias production --client-id ID --client-secret SECRET
```

### "No dependencies found" or "No flows found"
```bash
# Sync metadata first
sma sf sync

# Verify object/field names are correct (case-sensitive)
sma sf analyse field-flows Account Email  # Correct
sma sf analyse field-flows account email  # May not work
```

### "Flow may not exist, or hasn't been synced"
- Flow name may be incorrect
- Flow may be inactive (only active flows are synced)
- Run `sma sf sync` to ensure latest flows are indexed

## Future Enhancements

Phase 4 (Planned):
- **Apex Code Parsing**: Field-level analysis of Apex classes and triggers
- **Formula Field Analysis**: Identify formula dependencies
- **Validation Rule Tracking**: Show which validation rules reference fields
- **Process Builder Support**: Analyze legacy Process Builder processes
- **Workflow Rule Support**: Track classic Workflow Rule dependencies
- **Impact Visualization**: Generate dependency graphs and diagrams

## Files Modified

- `src/sma/cli.py`: Added `sf_analyse` command group and all subcommands
- `src/sma/database.py`: Phase 3 schema tables
- `src/sma/salesforce/metadata.py`: Phase 3 sync logic
- `src/sma/parsers/flow_parser.py`: Flow XML parsing

## Database Schema Reference

See [database-design.md](../database-design.md) for complete Phase 3 schema documentation.

## Related Commands

- `sma sf connect`: Connect to Salesforce org
- `sma sf sync`: Sync metadata to local database
- `sma sf status`: Check connection status
- `sma db browse`: Browse database in web interface
- `sma db stats`: View database statistics

## MCP Integration (Future)

The analyse commands are designed with MCP (Model Context Protocol) in mind. Future AI integrations will be able to:

```
User: "What flows use the Account Email field?"
AI: [Automatically translates to] sma sf analyse field-flows Account Email
    [Returns structured results to user in natural language]
```

See [database-design.md](../database-design.md) MCP Integration section for architecture details.
