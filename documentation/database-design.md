# SMA Database Design

This document describes the database schema for SMA (Salesforce Metadata Assistant).

**Last Updated:** 2025-11-08

---

## Overview

SMA uses SQLite for local metadata caching and querying. The database stores:
1. Current implementation: Demo features (greetings, quotes)
2. Planned: Salesforce metadata, automations, code references, and dependencies

---

## Database Location

- **Path:** `~/.sma/sma.db`
- **Windows:** `C:\Users\<Username>\.sma\sma.db`
- **Type:** SQLite 3
- **Initialization:** Automatic on first run

---

## Current Schema (v0.1.0)

### Table: `greetings`
**Status:** ✅ Implemented
**Purpose:** Track hello command usage for demo purposes

```sql
CREATE TABLE IF NOT EXISTS greetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username TEXT
)
```

**Columns:**
- `id` - Unique greeting identifier
- `timestamp` - When greeting was issued (auto-generated)
- `username` - Who was greeted (from CLI option or environment)

**Indexes:** None (table is small)

---

### Table: `quotes`
**Status:** ✅ Implemented
**Purpose:** Store inspirational quotes for hello command

```sql
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `id` - Unique quote identifier
- `text` - Quote text content
- `author` - Quote author name
- `created_at` - When quote was added (auto-generated)

**Indexes:** None (random selection doesn't benefit from indexing)

**Seeding:** Automatically seeded with 10 initial quotes on first run

---

## Planned Schema (MVP)

The following tables are planned for Salesforce metadata storage.

### Core Metadata Tables

#### Table: `salesforce_orgs`
**Status:** ✅ Implemented (Phase 1)
**Purpose:** Store connected Salesforce organizations

```sql
CREATE TABLE IF NOT EXISTS salesforce_orgs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT UNIQUE NOT NULL,           -- Salesforce org ID (18-char)
    instance_url TEXT NOT NULL,            -- Instance URL (e.g., https://na1.salesforce.com)
    org_name TEXT,                         -- Friendly org name
    org_type TEXT,                         -- Sandbox, Production, Developer
    is_active BOOLEAN DEFAULT 1,           -- Current active org
    last_sync DATETIME,                    -- Last metadata sync timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_org_id` on `org_id`
- `idx_is_active` on `is_active`

---

#### Table: `sobjects`
**Status:** ✅ Implemented (Phase 2)
**Purpose:** Store Salesforce object metadata

```sql
CREATE TABLE IF NOT EXISTS sobjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,                  -- Foreign key to salesforce_orgs.org_id
    api_name TEXT NOT NULL,                -- Object API name (e.g., Account, Custom__c)
    label TEXT,                            -- Object label
    plural_label TEXT,                     -- Plural label
    is_custom BOOLEAN,                     -- Custom object flag
    key_prefix TEXT,                       -- 3-char key prefix
    is_queryable BOOLEAN,                  -- Can be queried
    is_createable BOOLEAN,                 -- Can create records
    is_updateable BOOLEAN,                 -- Can update records
    is_deletable BOOLEAN,                  -- Can delete records
    metadata JSON,                         -- Full metadata JSON blob
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, api_name)
)
```

**Indexes:**
- `idx_sobject_org_api` on `(org_id, api_name)` - Primary lookup
- `idx_sobject_custom` on `is_custom` - Filter custom objects
- `idx_sobject_label` on `label` - Autocomplete support

---

#### Table: `fields`
**Status:** ✅ Implemented (Phase 2)
**Purpose:** Store Salesforce field metadata

```sql
CREATE TABLE IF NOT EXISTS fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    sobject_id INTEGER NOT NULL,           -- Foreign key to sobjects.id
    api_name TEXT NOT NULL,                -- Field API name
    label TEXT,                            -- Field label
    type TEXT,                             -- Field type (Text, Number, Lookup, etc.)
    length INTEGER,                        -- Max length for text fields
    is_custom BOOLEAN,                     -- Custom field flag
    is_required BOOLEAN,                   -- Required flag
    is_unique BOOLEAN,                     -- Unique constraint
    reference_to TEXT,                     -- For lookup/master-detail (object name)
    relationship_name TEXT,                -- Relationship name
    formula TEXT,                          -- Formula if formula field
    default_value TEXT,                    -- Default value
    help_text TEXT,                        -- Field help text
    metadata JSON,                         -- Full metadata JSON blob
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sobject_id) REFERENCES sobjects(id) ON DELETE CASCADE,
    UNIQUE(org_id, sobject_id, api_name)
)
```

**Indexes:**
- `idx_field_org_sobject` on `(org_id, sobject_id)` - Lookup fields by object
- `idx_field_api_name` on `api_name` - Autocomplete support
- `idx_field_label` on `label` - Autocomplete support
- `idx_field_type` on `type` - Filter by field type
- `idx_field_reference` on `reference_to` - Find lookups

---

### Automation & Code Tables

#### Table: `flows`
**Status:** 📋 Planned
**Purpose:** Store Flow metadata

```sql
CREATE TABLE IF NOT EXISTS flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    api_name TEXT NOT NULL,                -- Flow API name
    label TEXT,                            -- Flow label
    process_type TEXT,                     -- Flow, Workflow, ProcessBuilder, etc.
    status TEXT,                           -- Active, Draft, Obsolete
    description TEXT,                      -- Flow description
    trigger_type TEXT,                     -- Record change, Schedule, etc.
    sobject_type TEXT,                     -- Triggered object (if applicable)
    definition XML,                        -- Full Flow definition XML
    metadata JSON,                         -- Parsed metadata
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, api_name)
)
```

**Indexes:**
- `idx_flow_org_api` on `(org_id, api_name)`
- `idx_flow_status` on `status`
- `idx_flow_sobject` on `sobject_type`

---

#### Table: `apex_classes`
**Status:** 📋 Planned
**Purpose:** Store Apex class metadata and code

```sql
CREATE TABLE IF NOT EXISTS apex_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    api_name TEXT NOT NULL,                -- Class name
    body TEXT,                             -- Full class code
    status TEXT,                           -- Active, Inactive, Deleted
    is_test BOOLEAN,                       -- Test class flag
    api_version TEXT,                      -- API version
    source TEXT,                           -- Salesforce or AzureDevOps
    repository_path TEXT,                  -- Path in repo (if from Azure)
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, api_name)
)
```

**Indexes:**
- `idx_apex_org_api` on `(org_id, api_name)`
- `idx_apex_is_test` on `is_test`

---

#### Table: `apex_triggers`
**Status:** 📋 Planned
**Purpose:** Store Apex trigger metadata

```sql
CREATE TABLE IF NOT EXISTS apex_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    api_name TEXT NOT NULL,                -- Trigger name
    sobject_id INTEGER NOT NULL,           -- Foreign key to sobjects.id
    sobject_api_name TEXT NOT NULL,        -- Cached for quick reference
    body TEXT,                             -- Full trigger code
    status TEXT,                           -- Active, Inactive
    is_before BOOLEAN,                     -- Before trigger
    is_after BOOLEAN,                      -- After trigger
    is_insert BOOLEAN,                     -- Insert event
    is_update BOOLEAN,                     -- Update event
    is_delete BOOLEAN,                     -- Delete event
    is_undelete BOOLEAN,                   -- Undelete event
    api_version TEXT,                      -- API version
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sobject_id) REFERENCES sobjects(id) ON DELETE CASCADE,
    UNIQUE(org_id, api_name)
)
```

**Indexes:**
- `idx_trigger_org_api` on `(org_id, api_name)`
- `idx_trigger_sobject` on `sobject_id`
- `idx_trigger_status` on `status`

---

### Dependency & Reference Tables

#### Table: `field_flow_dependencies`
**Status:** 📋 Planned
**Purpose:** Track which flows use which fields

```sql
CREATE TABLE IF NOT EXISTS field_flow_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,             -- Foreign key to fields.id
    flow_id INTEGER NOT NULL,              -- Foreign key to flows.id
    usage_type TEXT,                       -- Read, Write, Filter, etc.
    context TEXT,                          -- Where in flow (decision, assignment, etc.)
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
    UNIQUE(org_id, field_id, flow_id, usage_type)
)
```

**Indexes:**
- `idx_field_flow_field` on `field_id` - Find flows by field
- `idx_field_flow_flow` on `flow_id` - Find fields by flow

---

#### Table: `field_trigger_dependencies`
**Status:** 📋 Planned
**Purpose:** Track which triggers reference which fields

```sql
CREATE TABLE IF NOT EXISTS field_trigger_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,             -- Foreign key to fields.id
    trigger_id INTEGER NOT NULL,           -- Foreign key to apex_triggers.id
    usage_type TEXT,                       -- Read, Write, oldMap, newMap, etc.
    line_number INTEGER,                   -- Line in code (if parseable)
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_id) REFERENCES apex_triggers(id) ON DELETE CASCADE,
    UNIQUE(org_id, field_id, trigger_id, line_number)
)
```

**Indexes:**
- `idx_field_trigger_field` on `field_id`
- `idx_field_trigger_trigger` on `trigger_id`

---

#### Table: `field_code_references`
**Status:** 📋 Planned
**Purpose:** Track field references in Apex classes

```sql
CREATE TABLE IF NOT EXISTS field_code_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,             -- Foreign key to fields.id
    apex_class_id INTEGER NOT NULL,        -- Foreign key to apex_classes.id
    usage_type TEXT,                       -- Read, Write, SOQL, etc.
    line_number INTEGER,                   -- Line in code
    context TEXT,                          -- Surrounding code snippet
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    FOREIGN KEY (apex_class_id) REFERENCES apex_classes(id) ON DELETE CASCADE
)
```

**Indexes:**
- `idx_field_code_field` on `field_id`
- `idx_field_code_class` on `apex_class_id`

---

### Permission Tables

#### Table: `permission_sets`
**Status:** 📋 Planned
**Purpose:** Store permission set metadata

```sql
CREATE TABLE IF NOT EXISTS permission_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    api_name TEXT NOT NULL,                -- Permission set API name
    label TEXT,                            -- Permission set label
    description TEXT,                      -- Description
    is_custom BOOLEAN,                     -- Custom permission set
    metadata JSON,                         -- Full permission set metadata
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, api_name)
)
```

---

#### Table: `field_permissions`
**Status:** 📋 Planned
**Purpose:** Track field-level security settings

```sql
CREATE TABLE IF NOT EXISTS field_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,             -- Foreign key to fields.id
    permission_set_id INTEGER NOT NULL,    -- Foreign key to permission_sets.id
    can_read BOOLEAN,                      -- Read permission
    can_edit BOOLEAN,                      -- Edit permission
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_set_id) REFERENCES permission_sets(id) ON DELETE CASCADE,
    UNIQUE(org_id, field_id, permission_set_id)
)
```

**Indexes:**
- `idx_field_perm_field` on `field_id`
- `idx_field_perm_permset` on `permission_set_id`

---

## Query Patterns

### Example Queries

**Q: Which triggers are connected to this field?**
```sql
SELECT t.api_name, t.sobject_api_name, ftd.usage_type
FROM apex_triggers t
JOIN field_trigger_dependencies ftd ON t.id = ftd.trigger_id
JOIN fields f ON ftd.field_id = f.id
WHERE f.api_name = 'Email' AND f.sobject_id = (
    SELECT id FROM sobjects WHERE api_name = 'Account'
)
```

**Q: Which flows use this field?**
```sql
SELECT fl.api_name, fl.label, ffd.usage_type, ffd.context
FROM flows fl
JOIN field_flow_dependencies ffd ON fl.id = ffd.flow_id
JOIN fields f ON ffd.field_id = f.id
WHERE f.api_name = 'Custom_Field__c'
```

**Q: Find all fields used by a specific flow**
```sql
SELECT f.api_name, s.api_name as object_name, ffd.usage_type
FROM fields f
JOIN sobjects s ON f.sobject_id = s.id
JOIN field_flow_dependencies ffd ON f.id = ffd.field_id
JOIN flows fl ON ffd.flow_id = fl.id
WHERE fl.api_name = 'Account_Update_Flow'
```

---

## Data Management

### Synchronization Strategy
1. **Initial Sync:** Full metadata download from Salesforce
2. **Incremental Sync:** Update only changed metadata (compare timestamps)
3. **Manual Refresh:** User-triggered full refresh
4. **Cache Invalidation:** Configurable TTL (time-to-live)

### Data Freshness
- Store `synced_at` timestamp for each record
- Track `last_sync` at org level
- Display data age in query results

### Cleanup & Maintenance
- Periodic cleanup of obsolete metadata
- Remove deleted flows, triggers, fields
- Archive old sync data

---

## Performance Considerations

### Indexing Strategy
- Index all foreign keys
- Index frequently queried columns (api_name, labels)
- Composite indexes for common query patterns
- Full-text search indexes for code searching (future)

### Storage Estimates
- Small org (~100 objects, 1000 fields): ~5-10 MB
- Medium org (~500 objects, 10,000 fields): ~50-100 MB
- Large org (~1000+ objects, 50,000+ fields): ~500 MB - 1 GB

### Query Optimization
- Use prepared statements
- Limit result sets
- Cache frequently accessed data in memory
- Use EXPLAIN QUERY PLAN for slow queries

---

## Schema Evolution

### Migration Strategy
1. Version table schema in code
2. Use Alembic or custom migration system
3. Backup database before migrations
4. Support rollback for failed migrations

### Future Enhancements
- Full-text search on code (FTS5 extension)
- Graph database for dependency visualization
- Time-series data for change tracking
- Compression for large XML/JSON blobs

---

## Backup & Recovery

### Backup Strategy
- Automatic backup before major operations
- Manual backup command in CLI
- Backup location: `~/.sma/backups/`
- Retention policy: Keep last 10 backups

### Recovery
- Restore from backup command
- Re-sync from Salesforce if corrupted

---

## Security Considerations

### Sensitive Data
- Do NOT store OAuth tokens in database
- Use OS keychain/credential manager for tokens
- Encrypt sensitive fields if needed (future)

### Access Control
- Database is local to user (file permissions)
- No network access to database
- Secure deletion of old org data

---

## Database Maintenance Commands (Planned)

```bash
# View database statistics
sma db stats

# Refresh metadata from Salesforce
sma db sync [--full]

# Backup database
sma db backup

# Restore from backup
sma db restore <backup_file>

# Clean up old data
sma db cleanup [--days 30]

# Vacuum and optimize
sma db optimize
```

---

## Change Log

### 2025-11-09
- ✅ Implemented Phase 3: Flow Dependencies & Relationship Tracking
- Added 7 new tables for comprehensive dependency and relationship modeling
- Integrated Flow XML parser for field reference extraction
- Added trigger inventory with event tracking
- Created central field dependency tracking system
- Designed MCP-ready data model for future AI integration

### 2025-11-08
- Created initial database design documentation
- Defined current schema (greetings, quotes)
- Planned complete Salesforce metadata schema
- Added query patterns and examples

---

## Phase 3 Schema (v0.3.0) - ✅ Implemented

### Overview
Phase 3 implements comprehensive dependency tracking and relationship modeling specifically designed for MCP (Model Context Protocol) integration and AI-powered analysis.

**Design Principles:**
1. **Relationship-First**: Model all relationships between entities explicitly
2. **Future-Proof**: Optimize for graph queries and MCP integration
3. **Denormalized Where Useful**: Store computed relationships for fast queries
4. **Audit Trail**: Track sync times, data freshness, and changes
5. **Queryable**: Optimize for common troubleshooting questions

---

### Phase 3 Tables

#### Table: `sf_field_dependencies`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Central dependency tracking - Links fields to all automations that reference them

```sql
CREATE TABLE IF NOT EXISTS sf_field_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_alias TEXT NOT NULL,        -- Which org this is from
    object_name TEXT NOT NULL,             -- Object API name (e.g., 'Account')
    field_name TEXT NOT NULL,              -- Field API name (e.g., 'Email__c')
    dependent_type TEXT NOT NULL,          -- Type: 'flow', 'trigger', 'validation_rule', 'process_builder'
    dependent_id TEXT NOT NULL,            -- ID of the dependent automation
    dependent_name TEXT,                   -- Name of automation (for easy querying)
    reference_type TEXT,                   -- How it's used: 'read', 'write', 'filter', 'assignment'
    line_number INTEGER,                   -- Line/position in source (if applicable)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_field_dep_object_field` on `(object_name, field_name)` - Find all dependencies for a field
- `idx_field_dep_dependent` on `(dependent_type, dependent_id)` - Find all fields used by an automation
- `idx_field_dep_alias` on `connection_alias` - Filter by org

**Example Queries:**
```sql
-- What flows use Account.Email?
SELECT dependent_name, reference_type
FROM sf_field_dependencies
WHERE object_name = 'Account'
  AND field_name = 'Email'
  AND dependent_type = 'flow';

-- What fields does "Lead Conversion Flow" touch?
SELECT object_name, field_name, reference_type
FROM sf_field_dependencies
WHERE dependent_name = 'Lead_Conversion_Flow';
```

---

#### Table: `sf_flow_field_references`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Detailed flow field references with context from Flow XML

```sql
CREATE TABLE IF NOT EXISTS sf_flow_field_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id TEXT NOT NULL,                 -- Flow record ID from sf_flows
    flow_api_name TEXT NOT NULL,           -- Flow API name (denormalized for queries)
    flow_version INTEGER,                  -- Flow version number
    object_name TEXT NOT NULL,             -- Object being referenced
    field_name TEXT NOT NULL,              -- Field being referenced
    element_name TEXT,                     -- Flow element name (e.g., 'Get_Account_Record')
    element_type TEXT,                     -- 'recordLookup', 'recordUpdate', 'assignment', 'decision'
    is_input BOOLEAN DEFAULT 0,            -- Is this field used as input?
    is_output BOOLEAN DEFAULT 0,           -- Is this field being set/updated?
    variable_name TEXT,                    -- Flow variable name if assigned
    xpath_location TEXT,                   -- XPath to element in Flow XML
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_flow_ref_flow` on `(flow_id, flow_version)` - All references for a specific flow version
- `idx_flow_ref_field` on `(object_name, field_name)` - Find flows using a specific field
- `idx_flow_ref_element_type` on `element_type` - Group by operation type

---

#### Table: `sf_field_relationships`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Model all field-level relationships (lookups, master-detail, formula references)

```sql
CREATE TABLE IF NOT EXISTS sf_field_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_alias TEXT NOT NULL,        -- Which org
    source_object TEXT NOT NULL,           -- Object where the relationship field exists
    source_field TEXT NOT NULL,            -- The relationship field name
    relationship_type TEXT NOT NULL,       -- 'lookup', 'master_detail', 'external_lookup', 'formula_reference'
    target_object TEXT,                    -- Object being referenced
    target_field TEXT,                     -- Field on target object (if specific)
    relationship_name TEXT,                -- API relationship name (e.g., 'Account.Contacts')
    is_cascade_delete BOOLEAN DEFAULT 0,   -- For master-detail
    is_reparentable BOOLEAN DEFAULT 1,     -- Can the parent be changed?
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_field_rel_source` on `(source_object, source_field)` - Find relationship details
- `idx_field_rel_target` on `target_object` - Find all fields pointing TO an object
- `idx_field_rel_type` on `relationship_type` - Filter by relationship type

**Example Queries:**
```sql
-- What objects have lookups to Account?
SELECT DISTINCT source_object, source_field
FROM sf_field_relationships
WHERE target_object = 'Account'
  AND relationship_type IN ('lookup', 'master_detail');

-- Is Opportunity.AccountId a master-detail?
SELECT relationship_type, is_cascade_delete
FROM sf_field_relationships
WHERE source_object = 'Opportunity'
  AND source_field = 'AccountId';
```

---

#### Table: `sf_object_relationships`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** High-level object-to-object relationship summary

```sql
CREATE TABLE IF NOT EXISTS sf_object_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_alias TEXT NOT NULL,        -- Which org
    parent_object TEXT NOT NULL,           -- Parent in the relationship
    child_object TEXT NOT NULL,            -- Child in the relationship
    relationship_field TEXT NOT NULL,      -- Field that creates the relationship
    relationship_type TEXT NOT NULL,       -- 'lookup', 'master_detail', 'hierarchy'
    relationship_name TEXT,                -- API relationship name
    child_count_estimate INTEGER           -- Approximate number of child records (if known)
)
```

**Indexes:**
- `idx_obj_rel_parent` on `parent_object` - Find all children of an object
- `idx_obj_rel_child` on `child_object` - Find all parents of an object

---

#### Table: `sf_trigger_metadata`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Enhanced trigger inventory with structured event tracking

```sql
CREATE TABLE IF NOT EXISTS sf_trigger_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_id TEXT UNIQUE NOT NULL,       -- ApexTrigger.Id from Salesforce
    trigger_name TEXT NOT NULL,            -- Trigger API name
    object_name TEXT NOT NULL,             -- Object (denormalized)
    is_before_insert BOOLEAN DEFAULT 0,    -- Runs on before insert
    is_before_update BOOLEAN DEFAULT 0,    -- Runs on before update
    is_before_delete BOOLEAN DEFAULT 0,    -- Runs on before delete
    is_after_insert BOOLEAN DEFAULT 0,     -- Runs on after insert
    is_after_update BOOLEAN DEFAULT 0,     -- Runs on after update
    is_after_delete BOOLEAN DEFAULT 0,     -- Runs on after delete
    is_after_undelete BOOLEAN DEFAULT 0,   -- Runs on after undelete
    is_active BOOLEAN DEFAULT 1,           -- Is the trigger active?
    created_date DATETIME,                 -- When trigger was created in SF
    last_modified_date DATETIME,           -- When trigger was last modified in SF
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_trigger_meta_object` on `object_name` - All triggers for an object
- `idx_trigger_meta_active` on `is_active` - Only active triggers

**Example Queries:**
```sql
-- What triggers run on Account after update?
SELECT trigger_name
FROM sf_trigger_metadata
WHERE object_name = 'Account'
  AND is_after_update = TRUE
  AND is_active = TRUE;

-- How many triggers are there per object?
SELECT object_name, COUNT(*) as trigger_count
FROM sf_trigger_metadata
WHERE is_active = TRUE
GROUP BY object_name
ORDER BY trigger_count DESC;
```

---

#### Table: `sf_flow_metadata`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Enhanced flow metadata with element counts and complexity metrics

```sql
CREATE TABLE IF NOT EXISTS sf_flow_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id TEXT NOT NULL,                 -- Flow.Id from Salesforce
    flow_api_name TEXT NOT NULL,           -- Unique API name
    flow_label TEXT,                       -- User-friendly label
    process_type TEXT,                     -- 'Flow', 'Workflow', 'AutoLaunchedFlow', etc.
    trigger_type TEXT,                     -- 'RecordAfterSave', 'RecordBeforeSave', 'Scheduled', etc.
    trigger_object TEXT,                   -- Object that triggers the flow (if applicable)
    is_active BOOLEAN DEFAULT 0,           -- Is this the active version?
    is_template BOOLEAN DEFAULT 0,         -- Is this a template flow?
    version_number INTEGER,                -- Flow version
    status TEXT,                           -- 'Active', 'Draft', 'Obsolete'
    element_count INTEGER,                 -- Number of elements in flow
    decision_count INTEGER,                -- Number of decision elements
    has_record_lookups BOOLEAN DEFAULT 0,  -- Contains Get Records
    has_record_updates BOOLEAN DEFAULT 0,  -- Contains Update Records
    has_record_creates BOOLEAN DEFAULT 0,  -- Contains Create Records
    has_record_deletes BOOLEAN DEFAULT 0,  -- Contains Delete Records
    last_modified_date DATETIME,           -- When modified in SF
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    xml_parsed_at DATETIME,                -- When we last parsed the XML
    UNIQUE(flow_api_name, version_number)
)
```

**Indexes:**
- `idx_flow_meta_api_version` on `(flow_api_name, version_number)` - Specific version lookup
- `idx_flow_meta_trigger_obj` on `trigger_object` - Flows triggered by object
- `idx_flow_meta_active` on `is_active` - Active flows only

---

#### Table: `sf_automation_coverage`
**Status:** ✅ Implemented (Phase 3)
**Purpose:** Summary view of what objects/fields are covered by automations

```sql
CREATE TABLE IF NOT EXISTS sf_automation_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_alias TEXT NOT NULL,        -- Which org
    object_name TEXT NOT NULL,             -- Salesforce object
    field_name TEXT,                       -- Field on object (NULL for object-level)
    has_flows BOOLEAN DEFAULT 0,           -- Any flows reference this?
    flow_count INTEGER DEFAULT 0,          -- Number of flows
    has_triggers BOOLEAN DEFAULT 0,        -- Any triggers reference this?
    trigger_count INTEGER DEFAULT 0,       -- Number of triggers
    has_validation_rules BOOLEAN DEFAULT 0,-- Any validation rules?
    validation_rule_count INTEGER DEFAULT 0,-- Number of validation rules
    has_process_builders BOOLEAN DEFAULT 0,-- Any process builders?
    process_builder_count INTEGER DEFAULT 0,-- Number of process builders
    total_automation_count INTEGER DEFAULT 0,-- Total automations
    last_computed DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connection_alias, object_name, field_name)
)
```

**Indexes:**
- `idx_auto_cov_object` on `object_name` - Coverage for an object
- `idx_auto_cov_field` on `(object_name, field_name)` - Coverage for a field

**Example Queries:**
```sql
-- Show me the most automated fields
SELECT object_name, field_name, total_automation_count
FROM sf_automation_coverage
WHERE field_name IS NOT NULL
ORDER BY total_automation_count DESC
LIMIT 20;
```

---

## MCP Integration Design

Phase 3 tables are specifically designed to support Model Context Protocol (MCP) queries for AI-powered analysis:

### Example MCP Queries

**User Query:** "What flows use the Account Email field?"
```sql
-- MCP translates to:
SELECT dependent_name, reference_type, element_type
FROM sf_field_dependencies d
JOIN sf_flow_field_references f ON d.dependent_id = f.flow_id
WHERE d.object_name='Account'
  AND d.field_name='Email'
  AND d.dependent_type='flow'
```

**User Query:** "Show me all automations on Opportunity"
```sql
-- MCP translates to:
SELECT * FROM sf_automation_coverage
WHERE object_name='Opportunity'
```

**User Query:** "What objects have master-detail relationships to Account?"
```sql
-- MCP translates to:
SELECT source_object, source_field, is_cascade_delete
FROM sf_field_relationships
WHERE target_object='Account'
  AND relationship_type='master_detail'
```

---

## Storage Estimates (Updated)

Typical org (~1000 custom objects, ~10000 fields, ~200 flows):
- Core metadata (objects, fields): ~50 MB
- Flow metadata and dependencies: ~2 MB
- Trigger metadata: ~100 KB
- Field relationships: ~100 KB
- Automation coverage: ~200 KB
- **Total Phase 3 overhead:** ~3 MB (negligible)

---

## Performance Optimizations

### Phase 3 Specific Optimizations:
1. **Denormalized Names**: Store automation names in dependency table for fast lookups without joins
2. **Composite Indexes**: Multi-column indexes for common query patterns
3. **Summary Tables**: Pre-computed automation coverage for dashboard queries
4. **Selective Parsing**: Only parse active flow versions
5. **Batch Inserts**: Use transactions for bulk dependency insertion

---
