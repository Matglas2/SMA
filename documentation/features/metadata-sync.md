# Metadata Synchronization (Phase 2)

**Feature Status:** ✅ Implemented
**Version:** 0.3.0
**Date Added:** 2025-11-09
**Phase:** MVP - Phase 2

## Overview

Metadata synchronization feature that downloads Salesforce object and field metadata to the local database for fast offline querying. This enables quick answers to metadata questions without making repeated API calls to Salesforce.

## Prerequisites

1. You must be connected to a Salesforce org (see [Salesforce Authentication](salesforce-authentication.md))
2. Run `sma sf status` to verify active connection
3. Ensure you have sufficient API limits available

## Commands

### Sync All Metadata

```bash
# Sync objects and all their fields
sma sf sync
```

**What it does:**
1. Retrieves all sobject metadata from Salesforce
2. Stores object information in `sobjects` table
3. For each object, retrieves all field metadata
4. Stores field information in `fields` table
5. Updates `last_sync` timestamp on org record

**Progress Output:**
```
Starting metadata synchronization...

⠋ Retrieving object metadata...
✓ Synced 347 objects
⠋ Retrieving field metadata...
✓ Synced 8,243 fields

✓ Synchronization complete!

Sync Summary

Objects synced: 347
Fields synced:  8,243

You can now query metadata using future commands or browse the database:
  sma db browse
```

### Selective Sync Options

You can selectively sync specific metadata types using the following options:

#### Sync Objects Only

```bash
# Sync only object metadata (skip fields, flows, etc.)
sma sf sync --objects-only
```

**Use cases:**
- Quick refresh of object list
- Testing sync functionality
- Checking what objects exist before full sync

**Example Output:**
```
Starting selective metadata sync...

Syncing objects...
✓ Synced 347 objects

✓ Selective sync complete!

Synced:
  Objects:       347
```

#### Sync Fields Only

```bash
# Sync only field metadata (requires objects to exist)
sma sf sync --fields-only
```

**Use cases:**
- Refresh field metadata without re-syncing objects
- Quick field metadata update after schema changes
- Faster sync when only field changes occurred

**Note:** Objects must already be synced for this to work.

#### Sync Flows Only

```bash
# Sync only Flow definitions and field references
sma sf sync --flows-only
```

**Use cases:**
- Refresh Flow metadata after Flow changes
- Re-parse Flows after fixing extraction issues
- Quick Flow-only sync without full metadata refresh

**Example Output:**
```
Starting selective metadata sync...

Syncing flows...
Found 45 active flows to process
Processing flow 1/45: Account_Email_Validation
Processing flow 2/45: Contact_Update_Process
...
✓ Synced 45 flows

✓ Selective sync complete!

Synced:
  Flows:         45
```

#### Sync Triggers Only

```bash
# Sync only Apex trigger metadata
sma sf sync --triggers-only
```

**Use cases:**
- Refresh trigger inventory after deployment
- Quick trigger metadata update
- Verify trigger activation status

#### Sync Relationships Only

```bash
# Sync only field relationship mappings
sma sf sync --relationships-only
```

**Use cases:**
- Refresh relationship graph after schema changes
- Update lookup/master-detail mappings
- Quick relationship metadata refresh

#### Combine Multiple Options

```bash
# Sync flows and triggers together
sma sf sync --flows-only --triggers-only

# Sync fields and relationships
sma sf sync --fields-only --relationships-only

# Sync everything except objects
sma sf sync --fields-only --flows-only --triggers-only --relationships-only
```

**Use cases:**
- Granular control over what gets synced
- Faster partial updates after specific changes
- Troubleshooting sync issues with individual components

## What Gets Synced

### Object Metadata

For each Salesforce object (standard and custom):
- API name (e.g., `Account`, `Custom_Object__c`)
- Label (e.g., "Account", "Custom Object")
- Plural label
- Custom object flag
- Key prefix (3-character ID prefix)
- Queryable, createable, updateable, deletable flags
- Full metadata JSON for future reference

### Field Metadata

For each field on every object:
- API name (e.g., `Email`, `Custom_Field__c`)
- Label
- Field type (Text, Number, Lookup, Formula, etc.)
- Length constraints
- Custom field flag
- Required, unique flags
- Reference information (for lookup/master-detail)
- Relationship name
- Formula (for formula fields)
- Default value
- Help text
- Full metadata JSON

## Database Schema

### sobjects Table

```sql
CREATE TABLE sobjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    api_name TEXT NOT NULL,
    label TEXT,
    plural_label TEXT,
    is_custom BOOLEAN,
    key_prefix TEXT,
    is_queryable BOOLEAN,
    is_createable BOOLEAN,
    is_updateable BOOLEAN,
    is_deletable BOOLEAN,
    metadata TEXT,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, api_name)
)
```

**Indexes:**
- `idx_sobject_org_api` on `(org_id, api_name)` - Fast lookup by object name
- `idx_sobject_custom` on `is_custom` - Filter custom objects
- `idx_sobject_label` on `label` - Search by label

### fields Table

```sql
CREATE TABLE fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    sobject_id INTEGER NOT NULL,
    api_name TEXT NOT NULL,
    label TEXT,
    type TEXT,
    length INTEGER,
    is_custom BOOLEAN,
    is_required BOOLEAN,
    is_unique BOOLEAN,
    reference_to TEXT,
    relationship_name TEXT,
    formula TEXT,
    default_value TEXT,
    help_text TEXT,
    metadata TEXT,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sobject_id) REFERENCES sobjects(id) ON DELETE CASCADE,
    UNIQUE(org_id, sobject_id, api_name)
)
```

**Indexes:**
- `idx_field_org_sobject` on `(org_id, sobject_id)` - Find fields by object
- `idx_field_api_name` on `api_name` - Search fields by name
- `idx_field_label` on `label` - Search fields by label
- `idx_field_type` on `type` - Filter by field type
- `idx_field_reference` on `reference_to` - Find lookup relationships

## Technical Implementation

### Files Created/Modified

**Created:**
- `src/sma/salesforce/metadata.py` - Metadata synchronization logic

**Modified:**
- `src/sma/database.py` - Added sobjects and fields tables
- `src/sma/cli.py` - Added `sma sf sync` command

### Architecture

**MetadataSync Class:**
```python
class MetadataSync:
    def __init__(self, sf_client: Salesforce, db_connection, org_id: str)

    def sync_all(self) -> Dict[str, int]:
        """Sync all metadata (objects and fields)"""

    def sync_sobjects(self) -> int:
        """Sync Salesforce object metadata"""

    def sync_fields(self) -> int:
        """Sync field metadata for all objects"""

    def get_sync_stats(self) -> Dict[str, any]:
        """Get synchronization statistics"""
```

**Sync Flow:**
1. Get active org from database
2. Retrieve Salesforce client from connection manager
3. Create MetadataSync instance
4. Call `sf.describe()` to get all sobjects
5. Store each object in database
6. For each object, call `sf.{ObjectName}.describe()` to get fields
7. Store each field in database
8. Update org's `last_sync` timestamp

### API Usage

**Salesforce APIs Used:**
- `Salesforce.describe()` - Global describe (all objects)
- `Salesforce.{ObjectName}.describe()` - Object describe (all fields)

**API Call Estimates:**
- Global describe: 1 call
- Object describes: 1 call per object (347 calls for typical org)
- **Total:** ~350 API calls for full sync

## Usage Examples

### First-Time Sync

```bash
# 1. Connect to Salesforce
sma sf connect --alias production --client-id ... --client-secret ...

# 2. Verify connection
sma sf status

# 3. Run first sync
sma sf sync

# Wait for completion (may take 2-5 minutes for large orgs)

# 4. Browse synced metadata
sma db browse
```

### Browsing Synced Data

After syncing, you can browse the data using datasette:

```bash
# Open database browser
sma db browse

# In browser, run queries like:

# Find all custom objects
SELECT api_name, label
FROM sobjects
WHERE is_custom = 1

# Find all lookup fields
SELECT s.api_name as object, f.api_name as field, f.reference_to
FROM fields f
JOIN sobjects s ON f.sobject_id = s.id
WHERE f.type = 'reference'

# Find all required custom fields
SELECT s.api_name as object, f.api_name as field, f.label
FROM fields f
JOIN sobjects s ON f.sobject_id = s.id
WHERE f.is_required = 1 AND f.is_custom = 1
```

### Refreshing Metadata

```bash
# Re-run sync to update metadata
sma sf sync

# This will replace old metadata with fresh data
```

## Performance Considerations

### Sync Time

Approximate sync times based on org size:
- **Small org** (~50 objects, 500 fields): 30-60 seconds
- **Medium org** (~200 objects, 3,000 fields): 2-3 minutes
- **Large org** (~500 objects, 10,000 fields): 5-10 minutes
- **Enterprise org** (~1000+ objects, 50,000+ fields): 15-30 minutes

**Factors affecting speed:**
- Number of objects (each requires separate API call)
- Network latency
- Salesforce API response time
- Database write speed

### Database Size

Approximate database sizes after sync:
- **Small org:** ~2-5 MB
- **Medium org:** ~10-20 MB
- **Large org:** ~50-100 MB
- **Enterprise org:** ~200-500 MB

### API Limits

**API calls consumed:**
- Global describe: 1 call
- Per-object describe: 1 call per object
- **Total:** 1 + (number of objects) calls

**Example:** Org with 347 objects = 348 API calls

**Daily limits:**
- Developer Edition: 15,000 calls/day (plenty for multiple syncs)
- Enterprise Edition: 100,000+ calls/day

## Error Handling

### Common Errors

**"No active Salesforce connection"**
```bash
# Solution: Connect first
sma sf connect --alias production --client-id ... --client-secret ...
```

**"Could not connect to Salesforce"**
```
Possible causes:
- Session expired (tokens expire after timeout)
- Network connectivity issues
- Invalid credentials

Solution: Reconnect
sma sf connect --alias production --client-id ... --client-secret ...
```

**"Could not describe {ObjectName}"**
```
Possible causes:
- Object deleted or renamed in Salesforce
- Insufficient permissions
- Custom object not accessible

The sync continues with other objects
```

### Progress Indicators

The sync command shows progress:
- Spinner animation during API calls
- Success checkmarks after each phase
- Final summary with counts

## Troubleshooting

### Sync takes too long

**For large orgs (500+ objects):**
```bash
# Run objects-only sync first to see object count
sma sf sync --objects-only

# Then run full sync (or wait until needed)
sma sf sync
```

### Database locked error

```bash
# Close database browser if open
# Close other applications accessing the database
# Retry sync
sma sf sync
```

### Partial sync completed

If sync fails mid-way:
- Objects and fields synced before failure are saved
- Re-running sync will update/replace all records
- No duplicate data created (UNIQUE constraints prevent it)

## Data Freshness

### When to Re-sync

Re-run sync when:
- You've made schema changes in Salesforce (new fields, objects)
- Switching to different org
- Data is older than 1 week (for active development orgs)
- Before major analysis or troubleshooting sessions

### Checking Last Sync

```bash
sma sf status

# Shows:
# Last Sync: 2025-11-09 14:30:22
```

### Incremental Sync (Future Enhancement)

Currently, sync replaces all metadata. Future versions will support:
- Incremental sync (only changed metadata)
- Selective sync (specific objects only)
- Scheduled auto-sync

## Querying Synced Metadata

### SQL Examples

**Find all objects with a specific prefix:**
```sql
SELECT api_name, label
FROM sobjects
WHERE key_prefix = 'a0X'
```

**Find fields by type:**
```sql
SELECT s.api_name as object, f.api_name as field, f.label
FROM fields f
JOIN sobjects s ON f.sobject_id = s.id
WHERE f.type = 'percent'
```

**Find all master-detail relationships:**
```sql
SELECT s.api_name as child_object,
       f.api_name as field,
       f.reference_to as parent_object
FROM fields f
JOIN sobjects s ON f.sobject_id = s.id
WHERE f.type = 'masterrecord'
```

**Count fields per object:**
```sql
SELECT s.api_name, COUNT(f.id) as field_count
FROM sobjects s
LEFT JOIN fields f ON s.id = f.sobject_id
GROUP BY s.id
ORDER BY field_count DESC
```

## Future Enhancements

### Planned (Phase 3+)

- Flow and automation metadata sync
- Apex trigger and class sync
- Dependency tracking (which flows use which fields)
- Incremental sync (only changed metadata)
- Selective sync (choose specific objects)
- Sync scheduling (auto-sync on schedule)

### Possible Additions

- Validation rule sync
- Workflow rule sync
- Permission set and profile sync
- Page layout sync
- Record type sync
- Sync progress bar with percentage
- Parallel object describes (faster sync)
- Compression for metadata JSON

## Related Commands

- `sma sf connect` - Connect to Salesforce org
- `sma sf status` - Check connection and last sync time
- `sma sf switch` - Switch to different org
- `sma db browse` - Browse synced metadata
- `sma db stats` - See database statistics

## Next Phase

Phase 3 will implement:
- Flow metadata retrieval
- Automation (triggers, process builder) sync
- Dependency analysis
- Query commands (e.g., "which triggers use this field?")
