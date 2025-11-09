# SMA Requirements & Features Tracking

This document maintains a complete history of all requirements, features, and changes to the SMA project.

**Last Updated:** 2025-11-09

---

## Project Vision

**SMA (Salesforce Metadata Assistant)** - A CLI-based tool to help troubleshoot and analyze Salesforce environments by querying metadata, automations, and code dependencies.

### Primary Goal
Save time during Salesforce troubleshooting by providing quick answers to metadata and dependency questions that normally require manual exploration through the Salesforce UI or metadata files.

---

## Feature Status Legend

- ✅ **Implemented** - Feature is complete and merged
- 🚧 **In Progress** - Currently being developed
- 📋 **Planned** - Approved for future implementation
- 💭 **Proposed** - Under consideration

---

## Evolution Timeline

### Phase 0: Initial Prototype (2025-11-08)
**Status:** ✅ Completed

Initial proof-of-concept with basic CLI functionality.

#### User Requests:
1. Created basic CLI application with Click framework
2. Added SQLite database for persistent storage
3. Implemented hello command as a demo feature
4. Moved quote storage from hardcoded list to database

#### Features Implemented:
- ✅ **Hello Command** - Greeting system with time-based messages, random quotes from database, and ASCII art
- ✅ **SQLite Database** - Local database at `~/.sma/sma.db` with automatic schema initialization
- ✅ **Quote Management** - Quotes stored in database, retrieved randomly, auto-seeded on first run
- ✅ **Development Workflow** - PR-based workflow with feature branches

#### Technical Decisions:
- Python with Click framework for CLI
- SQLite for local data storage
- Windows-first approach (cross-platform compatible via pathlib)

---

### Phase 1: Authentication & Tools (2025-11-08)
**Status:** ✅ Completed

Implemented OAuth authentication system and database management tools.

#### Features Implemented:
- ✅ **OAuth 2.0 Authentication** - Secure connection to Salesforce orgs using Connected App
- ✅ **Multi-org Support** - Connect to multiple orgs (production, sandbox, custom domains)
- ✅ **Credential Management** - Secure storage using OS keyring (Windows Credential Manager, macOS Keychain)
- ✅ **Connection Management** - Status checking, org switching, disconnect functionality
- ✅ **Database Browser** - Web-based SQLite browser using datasette
- ✅ **Database Commands** - Browse, stats, path commands for database management

#### Commands Added:
- `sma sf connect` - Connect to Salesforce with OAuth
- `sma sf status` - Check connection status
- `sma sf list` - List all connected orgs
- `sma sf switch <alias>` - Switch active org
- `sma sf disconnect` - Disconnect from org
- `sma db browse` - Open database in web browser
- `sma db stats` - Show database statistics
- `sma db path` - Display database file path

#### Technical Implementations:
- OAuth 2.0 Web Server Flow with local callback server
- simple-salesforce for Salesforce API integration
- keyring for secure credential storage
- rich library for beautiful CLI output
- datasette for database browsing
- salesforce_orgs database table with indexes

---

### Phase 2: Metadata Retrieval (2025-11-09)
**Status:** ✅ Completed

Implemented metadata synchronization for Salesforce objects and fields.

#### Features Implemented:
- ✅ **Object Metadata Sync** - Download all Salesforce object metadata
- ✅ **Field Metadata Sync** - Download all field metadata for each object
- ✅ **Local Caching** - Store metadata in local database for fast querying
- ✅ **Incremental Updates** - Replace old metadata with fresh data
- ✅ **Progress Indicators** - Rich progress display during sync

#### Commands Added:
- `sma sf sync` - Sync all metadata (objects and fields)
- `sma sf sync --objects-only` - Sync only objects

#### Database Schema:
- **sobjects table** - Stores Salesforce object metadata (api_name, label, flags, etc.)
- **fields table** - Stores field metadata (api_name, label, type, references, formulas, etc.)
- **Indexes** - Optimized for fast lookup by name, label, type, and relationships

#### Technical Implementations:
- MetadataSync class for sync operations
- Salesforce describe() API for global metadata
- Object.describe() API for field metadata
- JSON storage for complete metadata preservation
- Foreign key relationships between objects and fields

#### What Gets Synced:
- All standard and custom objects
- All fields including: text, number, picklist, lookup, master-detail, formula, etc.
- Object properties: queryable, createable, updateable, deletable flags
- Field properties: required, unique, length, references, formulas, help text
- Timestamps for sync tracking

---

## Current Requirements

### MVP (Minimum Viable Product)
**Status:** 🚧 In Progress (Phase 1-2 Complete)

#### Core Functionality

**Authentication & Connection**
- ✅ OAuth 2.0 integration with Salesforce
- ✅ Support for multiple Salesforce environments (sandbox, production, dev)
- ✅ Secure credential storage
- ✅ Connection status verification

**Metadata Retrieval**
- ✅ Real-time metadata retrieval via Salesforce APIs
- ✅ Cache metadata locally for offline querying
- 🚧 Support for metadata types:
  - ✅ Custom fields and objects
  - 📋 Flows (Process Builder, Flow Builder)
  - 📋 Workflows and Process Builders
  - 📋 Apex triggers
  - 📋 Validation rules
  - 📋 Permission sets and profiles

**Code Repository Integration**
- 📋 Import Apex code from Azure DevOps repositories
- 📋 Parse and index Apex code references
- 📋 Track code dependencies

**Query Capabilities**
User should be able to ask:
- 📋 "Which triggers are connected to this field?"
- 📋 "Which flows use this field?"
- 📋 "Which automations are linked to this field?"
- 📋 "Find all fields used by a specific flow"
- 📋 "Find all objects used by a specific flow"
- 📋 "Find all users who have access to certain fields or objects"
- 📋 General troubleshooting queries for operational issues

**CLI Features**
- 📋 Autocomplete for Salesforce objects and fields
- 📋 Interactive command mode
- 📋 Export results to various formats (JSON, CSV, etc.)

**Local-First Architecture**
- 📋 Runs entirely on local machine
- 📋 No cloud hosting dependencies
- 📋 Fast querying via local database cache

---

## Future Enhancements

### Phase 2: Advanced Features
**Status:** 💭 Proposed

- 💭 **UI Implementation** - Web-based or desktop GUI
- 💭 **MCP Server Integration** - Model Context Protocol server for Claude/LLM integration
- 💭 **Advanced Analytics** - Dependency graphs, impact analysis
- 💭 **Multi-org Support** - Manage multiple Salesforce orgs simultaneously
- 💭 **Change Tracking** - Monitor metadata changes over time
- 💭 **Smart Suggestions** - AI-powered troubleshooting recommendations

---

## Technical Stack (Planned)

### Core Technologies
- **Language:** Python 3.8+
- **CLI Framework:** Click
- **Database:** SQLite (local caching)
- **Salesforce Integration:**
  - Research: simple-salesforce, salesforce-python-toolkit, or pyforce
  - Salesforce Metadata API
  - Salesforce REST API
  - Salesforce Tooling API (for code analysis)
- **OAuth:** Research Python OAuth libraries compatible with Salesforce
- **Azure DevOps:** azure-devops Python package
- **Autocomplete:** Click's built-in autocomplete or prompt_toolkit

### APIs to Integrate
- Salesforce Metadata API (describe, retrieve metadata)
- Salesforce Tooling API (Apex code, triggers)
- Salesforce REST API (records, permissions)
- Azure DevOps REST API (repository access)

---

## Database Design Requirements

### Metadata to Store
1. **Salesforce Objects & Fields**
   - Object API names, labels, types
   - Field API names, labels, types, references

2. **Automations**
   - Flows (Flow Builder)
   - Process Builders
   - Workflows
   - Triggers (Apex)

3. **Code References**
   - Apex classes and methods
   - Apex triggers
   - Field usage in code

4. **Permissions**
   - Field-level security
   - Object permissions
   - User/profile/permission set associations

5. **Dependencies**
   - Field → Automation mappings
   - Object → Flow mappings
   - Code → Field references

See [database-design.md](database-design.md) for detailed schema.

---

## User Feedback & Change Log

### 2025-11-08

**Change:** Store quotes in database
- **Request:** "Update the app to store the available quotes in the database too and get one randomly"
- **Implementation:** Added quotes table, seeding mechanism, and `get_random_quote()` method
- **Outcome:** Quotes now persistent and manageable in database

**Change:** Add PR workflow
- **Request:** "Make pull requests after these changes too, and make that the standard approach after i approve the results"
- **Implementation:** Updated development workflow in CLAUDE.md, created feature branch process
- **Outcome:** All future changes go through PR review before merging

**Change:** Track requirements and database design
- **Request:** "Please keep a file with a constantly updated overview of the requirements and features of the app so far including what i asked and changed over time"
- **Implementation:** Created requirements.md and database-design.md
- **Outcome:** Complete lineage tracking for project evolution

**Change:** Salesforce troubleshooting vision
- **Request:** Defined complete vision for Salesforce metadata assistant tool
- **Implementation:** Documented MVP requirements, future enhancements, and technical approach
- **Outcome:** Clear roadmap for building Salesforce troubleshooting capabilities

---

## Open Questions & Research Needed

1. **Salesforce Python Libraries**
   - Which library provides best Metadata API access?
   - Performance comparison for large metadata retrieval
   - OAuth flow implementation examples

2. **Database Schema**
   - How to model Flow dependencies efficiently?
   - Best way to store code references for fast querying?
   - Indexing strategy for autocomplete performance

3. **Azure DevOps Integration**
   - Authentication method for repository access
   - How to keep code in sync with repository changes?

4. **Autocomplete Implementation**
   - Real-time vs cached object/field lists
   - User experience design for large numbers of fields

---

## Success Metrics (Future)

- Time saved per troubleshooting session
- Query response time (target: <1 second for cached data)
- Metadata freshness (how often to sync)
- User satisfaction and adoption

---

## References

- [Salesforce Metadata API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/)
- [Salesforce Tooling API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/)
- [Click Documentation](https://click.palletsprojects.com/)
