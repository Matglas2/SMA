# Salesforce Integration Implementation Plan

**Feature Branch:** `feature/salesforce-integration`
**Created:** 2025-11-08
**Status:** 🚧 In Progress

---

## Overview

This document outlines the implementation plan for integrating Salesforce metadata retrieval and querying capabilities into SMA.

---

## Library Selection

### Primary Library: simple-salesforce
**Rationale:**
- ✅ Active maintenance (supports Python 3.9-3.13)
- ✅ Built-in Metadata API support (CRUD operations)
- ✅ OAuth 2.0 authentication support
- ✅ Bulk API support for large data retrieval
- ✅ Well-documented and widely used
- ✅ Supports Tooling API (for Apex code analysis)

**Installation:** `pip install simple-salesforce`

**Additional Dependencies:**
- `keyring` - Secure credential storage
- `python-dotenv` - Environment variable management
- `prompt_toolkit` - CLI autocomplete functionality

---

## Implementation Phases

### Phase 1: Authentication & Connection (MVP - Step 1)
**Goal:** Establish secure OAuth connection to Salesforce

**Tasks:**
1. Set up Connected App in Salesforce (user setup)
2. Implement OAuth 2.0 Web Server Flow
3. Store credentials securely using `keyring`
4. Create connection management commands:
   - `sma sf connect` - Initiate OAuth flow
   - `sma sf status` - Check connection status
   - `sma sf disconnect` - Remove credentials
5. Handle multiple orgs (sandbox, production)

**Files to Create/Modify:**
- `src/sma/salesforce/auth.py` - OAuth implementation
- `src/sma/salesforce/connection.py` - Connection manager
- `src/sma/cli.py` - Add SF commands
- `src/sma/database.py` - Add `salesforce_orgs` table

**Success Criteria:**
- ✅ User can authenticate via OAuth
- ✅ Credentials stored securely
- ✅ Connection status visible
- ✅ Support multiple org connections

---

### Phase 2: Metadata Retrieval (MVP - Step 2)
**Goal:** Retrieve and cache Salesforce metadata

**Tasks:**
1. Implement metadata sync functionality
2. Retrieve object metadata (sobjects)
3. Retrieve field metadata for each object
4. Store in local SQLite database
5. Implement incremental sync (only changed metadata)
6. Create sync commands:
   - `sma sf sync` - Sync all metadata
   - `sma sf sync --objects Account,Contact` - Sync specific objects
   - `sma sf sync --full` - Force full refresh

**Files to Create/Modify:**
- `src/sma/salesforce/metadata.py` - Metadata retrieval logic
- `src/sma/salesforce/sync.py` - Sync orchestration
- `src/sma/database.py` - Add metadata tables (sobjects, fields)
- `src/sma/cli.py` - Add sync commands

**API Calls:**
- `sf.describe()` - Get all objects
- `sf.{Object}.describe()` - Get fields for each object
- Metadata API for additional details

**Success Criteria:**
- ✅ Metadata synced to local database
- ✅ Incremental sync working
- ✅ Progress indicator during sync
- ✅ Error handling for API failures

---

### Phase 3: Flow & Automation Retrieval (MVP - Step 3)
**Goal:** Retrieve flows, triggers, and automation metadata

**Tasks:**
1. Retrieve Flow definitions via Metadata API
2. Retrieve Apex Triggers via Tooling API
3. Parse XML/code to extract field references
4. Store automations and dependencies in database
5. Create automation commands:
   - `sma sf sync-flows` - Sync flow metadata
   - `sma sf sync-triggers` - Sync trigger metadata

**Files to Create/Modify:**
- `src/sma/salesforce/flows.py` - Flow retrieval and parsing
- `src/sma/salesforce/triggers.py` - Trigger retrieval
- `src/sma/parsers/flow_parser.py` - Parse Flow XML
- `src/sma/parsers/apex_parser.py` - Parse Apex code
- `src/sma/database.py` - Add flow/trigger tables

**API Calls:**
- Metadata API: `listMetadata(type='Flow')`
- Metadata API: `retrieve(Flow definitions)`
- Tooling API: Query ApexTrigger, ApexClass

**Success Criteria:**
- ✅ Flows stored in database
- ✅ Triggers stored in database
- ✅ Field dependencies extracted and stored
- ✅ XML/code parsing working

---

### Phase 4: Query Commands (MVP - Step 4)
**Goal:** Implement query commands to answer troubleshooting questions

**Tasks:**
1. Implement query engine
2. Create query commands:
   - `sma query field-triggers <field>` - Find triggers using field
   - `sma query field-flows <field>` - Find flows using field
   - `sma query flow-fields <flow>` - Find fields used by flow
   - `sma query field-automations <field>` - All automations for field
3. Add output formatting (table, JSON, CSV)
4. Implement fuzzy search for field/object names

**Files to Create/Modify:**
- `src/sma/query/engine.py` - Query logic
- `src/sma/query/formatters.py` - Output formatting
- `src/sma/cli.py` - Add query commands

**Success Criteria:**
- ✅ All planned queries working
- ✅ Fast query response (<1 second)
- ✅ Multiple output formats
- ✅ Helpful error messages

---

### Phase 5: Autocomplete (MVP - Step 5)
**Goal:** Add autocomplete for object and field names

**Tasks:**
1. Implement autocomplete using `prompt_toolkit`
2. Load object/field names from database
3. Enable fuzzy matching
4. Add autocomplete to query commands

**Files to Create/Modify:**
- `src/sma/autocomplete.py` - Autocomplete logic
- `src/sma/cli.py` - Integrate autocomplete

**Success Criteria:**
- ✅ Object names autocomplete
- ✅ Field names autocomplete (filtered by object)
- ✅ Fuzzy matching works
- ✅ Fast response

---

### Phase 6: Azure DevOps Integration (Future)
**Goal:** Import Apex code from Azure DevOps repositories

**Status:** 📋 Planned (post-MVP)

**Tasks:**
1. Authenticate with Azure DevOps
2. Clone/pull repositories
3. Parse Apex files for field references
4. Store code references in database

---

### Phase 7: Permission Analysis (Future)
**Goal:** Query user/profile permissions for fields and objects

**Status:** 📋 Planned (post-MVP)

**Tasks:**
1. Retrieve permission sets and profiles
2. Extract field-level security settings
3. Implement permission query commands

---

## Technical Architecture

### Project Structure
```
src/sma/
├── __init__.py
├── cli.py                    # Main CLI entry point
├── database.py               # Database management
├── salesforce/
│   ├── __init__.py
│   ├── auth.py              # OAuth authentication
│   ├── connection.py        # Connection manager
│   ├── metadata.py          # Metadata retrieval
│   ├── sync.py              # Sync orchestration
│   ├── flows.py             # Flow retrieval
│   └── triggers.py          # Trigger retrieval
├── parsers/
│   ├── __init__.py
│   ├── flow_parser.py       # Parse Flow XML
│   └── apex_parser.py       # Parse Apex code
├── query/
│   ├── __init__.py
│   ├── engine.py            # Query logic
│   └── formatters.py        # Output formatting
└── autocomplete.py          # Autocomplete functionality
```

### Authentication Flow
1. User runs `sma sf connect`
2. CLI provides Salesforce OAuth URL
3. User authenticates in browser
4. Callback receives authorization code
5. Exchange code for access token & refresh token
6. Store tokens securely in OS keyring
7. Use refresh token for subsequent connections

### Data Flow
1. **Sync:** Salesforce API → simple-salesforce → Database
2. **Query:** Database → Query Engine → Formatter → CLI Output
3. **Autocomplete:** Database → Cache → Autocomplete Engine → CLI

---

## Security Considerations

1. **Never store tokens in database** - Use OS keyring
2. **OAuth only** - No username/password flow
3. **Secure token refresh** - Auto-refresh expired tokens
4. **Scoped access** - Request minimal OAuth scopes
5. **Encrypted credentials** - Keyring handles encryption

---

## Error Handling Strategy

1. **Network errors:** Retry with exponential backoff
2. **API rate limits:** Queue requests, respect limits
3. **Authentication errors:** Prompt re-authentication
4. **Parsing errors:** Log and continue (don't fail entire sync)
5. **Database errors:** Graceful degradation, show cached data

---

## Testing Strategy

1. **Unit tests:** Each module independently
2. **Integration tests:** End-to-end flows
3. **Mock Salesforce API:** Use test fixtures
4. **Manual testing:** Real Salesforce org (sandbox)

---

## Dependencies to Add

```
# Core Salesforce
simple-salesforce>=1.12.0

# Security
keyring>=24.0.0
cryptography>=41.0.0

# CLI Enhancements
prompt-toolkit>=3.0.0
rich>=13.0.0              # Better CLI output

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0

# Parsing
lxml>=4.9.0              # XML parsing for Flows
```

---

## Milestones & Timeline

**Note:** This is a rough estimate, adjust based on progress

- **Week 1:** Phase 1 - Authentication (3-5 days)
- **Week 2:** Phase 2 - Metadata Retrieval (5-7 days)
- **Week 3:** Phase 3 - Flows & Triggers (5-7 days)
- **Week 4:** Phase 4 - Query Commands (3-5 days)
- **Week 5:** Phase 5 - Autocomplete (2-3 days)

**MVP Target:** 4-5 weeks

---

## Success Metrics

1. **Performance:**
   - Full sync: < 5 minutes for typical org
   - Query response: < 1 second
   - Autocomplete: < 100ms

2. **Reliability:**
   - 99% success rate for API calls (with retries)
   - Graceful handling of all error cases

3. **User Experience:**
   - Clear progress indicators
   - Helpful error messages
   - Intuitive command structure

---

## Next Steps

1. ✅ Set up dependencies in requirements.txt
2. ✅ Implement Phase 1 (Authentication)
3. Test with real Salesforce sandbox
4. Iterate based on user feedback
5. Continue to Phase 2

---

## Questions & Decisions Needed

1. **OAuth Callback:** Use local HTTP server or device flow?
   - **Decision:** Local HTTP server (simpler UX)

2. **Sync frequency:** How often to refresh metadata?
   - **Decision:** Manual sync, show data age in queries

3. **Object filtering:** Sync all objects or let user choose?
   - **Decision:** Sync all by default, allow filtering

4. **Progress indicator:** How to show sync progress?
   - **Decision:** Use `rich` library progress bars

---

## Change Log

### 2025-11-08
- Created implementation plan
- Selected simple-salesforce as primary library
- Defined 5-phase MVP approach
- Outlined technical architecture
