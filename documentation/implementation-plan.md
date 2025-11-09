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
**Status:** ✅ Completed (2025-11-09)

**Tasks:**
1. ✅ Retrieve Flow definitions via Tooling API
2. ✅ Retrieve Apex Triggers via Tooling API
3. ✅ Parse Flow XML to extract field references
4. ✅ Store automations and dependencies in database
5. ✅ Create analyse command group for querying dependencies

**Files Created/Modified:**
- `src/sma/parsers/flow_parser.py` - Parse Flow XML
- `src/sma/salesforce/metadata.py` - Enhanced with Phase 3 sync methods
- `src/sma/database.py` - Added 7 Phase 3 tables
- `src/sma/cli.py` - Added `sma sf analyse` command group

**API Calls:**
- Tooling API: `query/?q=SELECT ... FROM FlowDefinition`
- Tooling API: `query/?q=SELECT ... FROM Flow`
- Tooling API: `query/?q=SELECT ... FROM ApexTrigger`

**Success Criteria:**
- ✅ Flows stored in database (sf_flow_metadata, sf_flow_field_references)
- ✅ Triggers stored in database (sf_trigger_metadata)
- ✅ Field dependencies extracted and stored (sf_field_dependencies)
- ✅ Flow XML parsing working (FlowParser class)
- ✅ Field relationships tracked (sf_field_relationships, sf_object_relationships)

**Implemented Commands:**
- `sma sf analyse field-flows <object> <field>` - Find flows using field
- `sma sf analyse field-triggers <object> <field>` - Find triggers on object
- `sma sf analyse field-deps <object> <field>` - All dependencies for field
- `sma sf analyse flow-fields <flow>` - Find fields used by flow
- `sma sf analyse object-relationships <object>` - Show relationship graph

---

### Phase 4: Shell Autocomplete (MVP - Step 4)
**Goal:** Add intelligent shell autocomplete for commands and data
**Status:** ✅ Completed (2025-11-09)

**Overview:**
Implement multi-shell autocomplete support using Click 8.x native completion and click-pwsh for PowerShell 7. Autocomplete will be powered by dynamic database queries to suggest object names, field names, flow names, and org aliases while typing.

**Technology Stack:**
- **Click 8.x** - Native completion for Bash, Zsh, Fish (already available)
- **click-pwsh** - PowerShell 7+ support (new dependency)

**Supported Shells:**
- Bash 4.4+ (Linux, Mac, WSL)
- Zsh (Mac, Linux)
- Fish (Linux, Mac)
- PowerShell 7+ (Windows, Mac, Linux)

**Tasks:**

**4.1 Add Dependencies**
1. Add `click-pwsh>=0.9.5` to requirements.txt and pyproject.toml
2. Initialize PowerShell completion support in cli.py

**4.2 Create Completion Module**
Create `src/sma/completion.py` with completion functions:
1. `complete_salesforce_objects()` - Autocomplete object names from database
2. `complete_salesforce_fields()` - Autocomplete field names (context-aware)
3. `complete_flow_names()` - Autocomplete flow names with status
4. `complete_org_aliases()` - Autocomplete org aliases with type

**4.3 Apply Completion to Commands**
Add `shell_complete` parameter to:
- All `analyse` command arguments (object_name, field_name, flow_name)
- `--alias` options across all commands
- `sma sf switch` command
- `sma sf disconnect` command

**4.4 Add Helper Commands**
Create `sma completion` command group:
- `sma completion install <shell>` - Install completion for specified shell
- `sma completion show <shell>` - Display completion script

**4.5 Documentation**
Create `documentation/features/shell-completion.md` with:
- Installation instructions for each shell
- Usage examples
- Troubleshooting guide
- Technical implementation details

**Files to Create/Modify:**
- `requirements.txt` - Add click-pwsh dependency
- `pyproject.toml` - Add click-pwsh dependency
- `src/sma/completion.py` - NEW: Completion functions
- `src/sma/cli.py` - Initialize PowerShell support, add shell_complete parameters
- `documentation/features/shell-completion.md` - NEW: Feature documentation

**Database Queries:**
All completion functions will query local database with:
- LIMIT 50 for performance
- Prefix matching with LIKE
- CompletionItem objects with help text
- Error handling (return empty list on failure)

**Example Autocomplete Behavior:**
```bash
# Object name completion
sma sf analyse field-flows Acc<TAB>
→ Account, AccountContactRole, AccountHistory...

# Field name completion (context-aware)
sma sf analyse field-flows Account Em<TAB>
→ Email (Text), Employee_Number__c (Number)...

# Flow name completion with status
sma sf analyse flow-fields Update<TAB>
→ Update_Account_Flow (Active), Update_Contact_Flow (Inactive)...

# Org alias completion
sma sf switch prod<TAB>
→ production (Production), prod-sandbox (Sandbox)...
```

**Performance Requirements:**
- Completion queries: < 50ms
- Results limited to 50 items
- Database queries use indexes (object_name, field_name, api_name)
- Optional caching for frequently accessed data

**Windows Considerations:**
- PowerShell 7+ required (not PowerShell 5.1)
- cmd.exe not supported natively
- Installation helper for users: `sma completion install powershell`

**Success Criteria:**
- ✅ Autocomplete works in Bash, Zsh, Fish, PowerShell 7
- ✅ Object names autocomplete from database
- ✅ Field names autocomplete (filtered by selected object)
- ✅ Flow names autocomplete with active/inactive status
- ✅ Org aliases autocomplete with type info
- ✅ Help text displayed in supported shells (Zsh, Fish, PowerShell)
- ✅ Fast response (< 50ms per query)
- ✅ Easy installation via `sma completion install`
- ✅ Comprehensive documentation

**Alternative Considered:**
- **prompt-toolkit** - Requires rewriting CLI to use custom input loop
- **argcomplete** - Requires argparse instead of Click
- **Custom PowerShell module** - Too much maintenance overhead
- **Decision:** Use Click 8.x + click-pwsh for maximum compatibility

**Implemented Commands:**
- `sma completion install <shell>` - Show installation instructions for shell
- `sma completion show <shell>` - Display completion script

**Completion Applied To:**
- All analyse commands (object_name, field_name, flow_name arguments)
- All --alias options across SF commands
- sma sf switch command (alias argument)

---

### Phase 5: Apex Code Analysis (Future)
**Goal:** Parse Apex code to identify field usage at code level
**Status:** 📋 Planned (post-MVP)

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
