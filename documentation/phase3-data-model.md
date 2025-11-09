# Phase 3: Comprehensive Data Model Design

**Created:** 2025-11-09
**Status:** 🚧 Planning
**Purpose:** Design a comprehensive, MCP-ready data model for Salesforce metadata and dependencies

---

## Design Principles

1. **Relationship-First:** Model all relationships between entities explicitly
2. **Future-Proof:** Design for MCP queries and graph analysis
3. **Denormalized Where Useful:** Store computed relationships for fast queries
4. **Audit Trail:** Track sync times, data freshness, and changes
5. **Queryable:** Optimize for common troubleshooting questions

---

## New Tables for Phase 3

### 1. Field Dependency Tables

#### `sf_field_dependencies`
**Purpose:** Central table linking fields to all automations that reference them

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| connection_alias | TEXT | Which org this is from |
| object_name | TEXT | Object API name (e.g., 'Account') |
| field_name | TEXT | Field API name (e.g., 'Email__c') |
| dependent_type | TEXT | Type: 'flow', 'trigger', 'validation_rule', 'process_builder' |
| dependent_id | TEXT | ID of the dependent automation |
| dependent_name | TEXT | Name of automation (for easy querying) |
| reference_type | TEXT | How it's used: 'read', 'write', 'filter', 'assignment' |
| line_number | INTEGER | Line/position in source (if applicable) |
| created_at | TIMESTAMP | When this dependency was discovered |
| last_verified | TIMESTAMP | Last time we confirmed it still exists |

**Indexes:**
- `(object_name, field_name)` - Find all dependencies for a field
- `(dependent_type, dependent_id)` - Find all fields used by an automation
- `(connection_alias)` - Filter by org

**Example Queries This Enables:**
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
WHERE dependent_name = 'Lead Conversion Flow';
```

---

#### `sf_flow_field_references`
**Purpose:** Detailed flow field references with context from Flow XML

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| flow_id | TEXT | Flow record ID from sf_flows |
| flow_api_name | TEXT | Flow API name (denormalized for queries) |
| flow_version | INTEGER | Flow version number |
| object_name | TEXT | Object being referenced |
| field_name | TEXT | Field being referenced |
| element_name | TEXT | Flow element name (e.g., 'Get_Account_Record') |
| element_type | TEXT | 'recordLookup', 'recordUpdate', 'assignment', 'decision' |
| is_input | BOOLEAN | Is this field used as input? |
| is_output | BOOLEAN | Is this field being set/updated? |
| variable_name | TEXT | Flow variable name if assigned |
| xpath_location | TEXT | XPath to element in Flow XML |
| extracted_at | TIMESTAMP | When we parsed this |

**Indexes:**
- `(flow_id, flow_version)` - All references for a specific flow version
- `(object_name, field_name)` - Find flows using a specific field
- `(element_type)` - Group by operation type

---

### 2. Object Relationship Tables

#### `sf_field_relationships`
**Purpose:** Model all field-level relationships (lookups, master-detail, formula references)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| connection_alias | TEXT | Which org |
| source_object | TEXT | Object where the relationship field exists |
| source_field | TEXT | The relationship field name |
| relationship_type | TEXT | 'lookup', 'master_detail', 'external_lookup', 'formula_reference' |
| target_object | TEXT | Object being referenced |
| target_field | TEXT | Field on target object (if specific) |
| relationship_name | TEXT | API relationship name (e.g., 'Account.Contacts') |
| is_cascade_delete | BOOLEAN | For master-detail |
| is_reparentable | BOOLEAN | Can the parent be changed? |
| created_at | TIMESTAMP | When discovered |

**Indexes:**
- `(source_object, source_field)` - Find relationship details
- `(target_object)` - Find all fields pointing TO an object
- `(relationship_type)` - Filter by relationship type

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

#### `sf_object_relationships`
**Purpose:** High-level object-to-object relationship summary

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| connection_alias | TEXT | Which org |
| parent_object | TEXT | Parent in the relationship |
| child_object | TEXT | Child in the relationship |
| relationship_field | TEXT | Field that creates the relationship |
| relationship_type | TEXT | 'lookup', 'master_detail', 'hierarchy' |
| relationship_name | TEXT | API relationship name |
| child_count_estimate | INTEGER | Approximate number of child records (if known) |

**Indexes:**
- `(parent_object)` - Find all children of an object
- `(child_object)` - Find all parents of an object

---

### 3. Enhanced Trigger Tables

#### `sf_apex_triggers` (Enhancement)
**Current columns remain, add:**

| New Column | Type | Description |
|------------|------|-------------|
| trigger_events | TEXT | JSON: ['before insert', 'after update'] |
| trigger_object | TEXT | Object the trigger runs on (extracted from TableEnumOrId) |
| has_field_references | BOOLEAN | Have we parsed for field refs yet? |
| field_reference_count | INTEGER | How many fields it touches (estimated) |
| parsing_attempted_at | TIMESTAMP | Last time we tried to parse |
| parsing_status | TEXT | 'pending', 'success', 'failed', 'skipped' |
| parsing_error | TEXT | Error message if parsing failed |

**Purpose:** Track trigger inventory and readiness for future Apex analysis

---

#### `sf_trigger_metadata`
**Purpose:** Structured trigger metadata for better querying

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| trigger_id | TEXT | ApexTrigger.Id from Salesforce |
| trigger_name | TEXT | Trigger API name |
| object_name | TEXT | Object (denormalized) |
| is_before_insert | BOOLEAN | Runs on before insert |
| is_before_update | BOOLEAN | Runs on before update |
| is_before_delete | BOOLEAN | Runs on before delete |
| is_after_insert | BOOLEAN | Runs on after insert |
| is_after_update | BOOLEAN | Runs on after update |
| is_after_delete | BOOLEAN | Runs on after delete |
| is_after_undelete | BOOLEAN | Runs on after undelete |
| is_active | BOOLEAN | Is the trigger active? |
| created_date | TIMESTAMP | When trigger was created in SF |
| last_modified_date | TIMESTAMP | When trigger was last modified in SF |
| synced_at | TIMESTAMP | When we synced this |

**Indexes:**
- `(object_name)` - All triggers for an object
- `(is_active)` - Only active triggers

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

### 4. Flow Enhancement Tables

#### `sf_flow_metadata`
**Purpose:** Enhanced flow metadata (supplement existing sf_flows table)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| flow_id | TEXT | Flow.Id from Salesforce |
| flow_api_name | TEXT | Unique API name |
| flow_label | TEXT | User-friendly label |
| process_type | TEXT | 'Flow', 'Workflow', 'AutoLaunchedFlow', etc. |
| trigger_type | TEXT | 'RecordAfterSave', 'RecordBeforeSave', 'Scheduled', etc. |
| trigger_object | TEXT | Object that triggers the flow (if applicable) |
| is_active | BOOLEAN | Is this the active version? |
| is_template | BOOLEAN | Is this a template flow? |
| version_number | INTEGER | Flow version |
| status | TEXT | 'Active', 'Draft', 'Obsolete' |
| element_count | INTEGER | Number of elements in flow |
| decision_count | INTEGER | Number of decision elements |
| has_record_lookups | BOOLEAN | Contains Get Records |
| has_record_updates | BOOLEAN | Contains Update Records |
| has_record_creates | BOOLEAN | Contains Create Records |
| has_record_deletes | BOOLEAN | Contains Delete Records |
| last_modified_date | TIMESTAMP | When modified in SF |
| synced_at | TIMESTAMP | When we synced this |
| xml_parsed_at | TIMESTAMP | When we last parsed the XML |

**Indexes:**
- `(flow_api_name, version_number)` - Specific version lookup
- `(trigger_object)` - Flows triggered by object
- `(is_active)` - Active flows only

---

### 5. Cross-Reference Tables

#### `sf_automation_coverage`
**Purpose:** Summary view of what objects/fields are covered by automations

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| connection_alias | TEXT | Which org |
| object_name | TEXT | Salesforce object |
| field_name | TEXT | Field on object (NULL for object-level) |
| has_flows | BOOLEAN | Any flows reference this? |
| flow_count | INTEGER | Number of flows |
| has_triggers | BOOLEAN | Any triggers reference this? |
| trigger_count | INTEGER | Number of triggers |
| has_validation_rules | BOOLEAN | Any validation rules? |
| validation_rule_count | INTEGER | Number of validation rules |
| has_process_builders | BOOLEAN | Any process builders? |
| process_builder_count | INTEGER | Number of process builders |
| total_automation_count | INTEGER | Total automations |
| last_computed | TIMESTAMP | When this summary was computed |

**Purpose:** Fast queries for "what automations exist for this field?"

**Example Query:**
```sql
-- Show me the most automated fields
SELECT object_name, field_name, total_automation_count
FROM sf_automation_coverage
WHERE field_name IS NOT NULL
ORDER BY total_automation_count DESC
LIMIT 20;
```

---

## Enhanced Existing Tables

### `sf_custom_fields` (Add columns)

| New Column | Type | Description |
|------------|------|-------------|
| is_lookup | BOOLEAN | Is this a lookup field? |
| lookup_object | TEXT | Object it looks up to |
| relationship_name | TEXT | API relationship name |
| is_master_detail | BOOLEAN | Is this master-detail? |
| is_formula | BOOLEAN | Is this a formula field? |
| formula_references | TEXT | JSON array of fields referenced in formula |
| is_rollup_summary | BOOLEAN | Is this a rollup summary? |
| rollup_object | TEXT | Child object being rolled up |

---

## Implementation Priority

### Week 1: Core Dependencies
1. ✅ Create `sf_field_dependencies` table
2. ✅ Create `sf_flow_field_references` table
3. ✅ Implement Flow XML parser
4. ✅ Extract field references from flows
5. ✅ Populate dependency tables

### Week 2: Relationships & Triggers
1. ✅ Create `sf_field_relationships` table
2. ✅ Create `sf_object_relationships` table
3. ✅ Enhance `sf_custom_fields` with relationship columns
4. ✅ Create `sf_trigger_metadata` table
5. ✅ Enhance trigger sync to populate metadata

### Week 3: Enhancement & Coverage
1. ✅ Create `sf_flow_metadata` table
2. ✅ Enhance flow sync with element counting
3. ✅ Create `sf_automation_coverage` summary table
4. ✅ Build coverage computation logic

---

## MCP Query Examples (Future)

This data model will enable MCP to answer:

```
User: "What flows use the Account Email field?"
MCP: SELECT dependent_name FROM sf_field_dependencies
     WHERE object_name='Account' AND field_name='Email' AND dependent_type='flow'

User: "Show me all automations on Opportunity"
MCP: SELECT * FROM sf_automation_coverage WHERE object_name='Opportunity'

User: "What objects have master-detail relationships to Account?"
MCP: SELECT source_object, source_field FROM sf_field_relationships
     WHERE target_object='Account' AND relationship_type='master_detail'

User: "Which triggers run after Opportunity is updated?"
MCP: SELECT trigger_name FROM sf_trigger_metadata
     WHERE object_name='Opportunity' AND is_after_update=TRUE AND is_active=TRUE
```

---

## Storage Estimates

Typical org (~1000 custom objects, ~10000 fields, ~200 flows):
- `sf_field_dependencies`: ~50,000 rows (500KB)
- `sf_flow_field_references`: ~100,000 rows (2MB)
- `sf_field_relationships`: ~5,000 rows (100KB)
- `sf_trigger_metadata`: ~500 rows (50KB)
- `sf_automation_coverage`: ~10,000 rows (200KB)

**Total additional storage:** ~3MB (negligible)

---

## Next Steps

1. Implement schema in `src/sma/database.py`
2. Create Flow XML parser in `src/sma/parsers/flow_parser.py`
3. Update sync logic in `src/sma/salesforce/metadata.py`
4. Add dependency extraction during flow sync
5. Build trigger inventory collection
6. Test with real Salesforce org
7. Document query patterns

---

## Success Criteria

- ✅ Can query: "What flows use field X?"
- ✅ Can query: "What fields does flow Y use?"
- ✅ Can query: "What triggers exist for object Z?"
- ✅ Relationship data model is complete and queryable
- ✅ Data model supports future MCP integration
- ✅ Sync time remains reasonable (<15 min for typical org)
