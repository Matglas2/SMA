# Salesforce Authentication (Phase 1)

**Feature Status:** ✅ Implemented
**Version:** 0.2.0
**Date Added:** 2025-11-08
**Phase:** MVP - Phase 1

## Overview

OAuth 2.0 authentication system for securely connecting to Salesforce organizations. Supports multiple orgs (production, sandbox, custom domains) with secure credential storage.

## Prerequisites

Before using SMA with Salesforce, you need to create a Connected App:

1. Log in to Salesforce
2. Go to **Setup → App Manager**
3. Click **New Connected App**
4. Fill in basic information:
   - Connected App Name: `SMA` (or your choice)
   - API Name: `SMA`
   - Contact Email: Your email
5. Enable OAuth Settings:
   - **Callback URL:** `http://localhost:8765/oauth/callback`
   - **OAuth Scopes:**
     - Full access (full)
     - Perform requests at any time (refresh_token, offline_access)
6. Save and note your **Consumer Key** (Client ID) and **Consumer Secret** (Client Secret)

## Commands

### Connect to Salesforce

```bash
# Connect to production
sma sf connect --alias production --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET

# Connect to sandbox
sma sf connect --alias sandbox --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --sandbox

# Connect to custom domain
sma sf connect --alias custom --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --instance-url https://custom.my.salesforce.com
```

**Options:**
- `--alias` (required): Friendly name for this org
- `--client-id` (required): Connected App Consumer Key
- `--client-secret` (required): Connected App Consumer Secret
- `--sandbox`: Use test.salesforce.com for sandbox orgs
- `--instance-url`: Custom Salesforce instance URL

**Authentication Flow:**
1. Command opens browser to Salesforce login page
2. User logs in and authorizes the app
3. Salesforce redirects to local callback server
4. SMA receives authorization code
5. SMA exchanges code for access token
6. Credentials stored securely in OS keyring
7. Org info stored in local database

### Check Connection Status

```bash
sma sf status
```

Shows:
- Org name/alias
- Org type (Production/Sandbox)
- Org ID
- Instance URL
- Last metadata sync time

### List All Connected Orgs

```bash
sma sf list
```

Displays table of all connected orgs with:
- Active indicator (●)
- Alias
- Type
- Org ID
- Last sync time

### Switch Active Org

```bash
sma sf switch <alias>
```

Examples:
```bash
sma sf switch production
sma sf switch sandbox
```

### Disconnect from Org

```bash
# Disconnect active org (prompts for confirmation)
sma sf disconnect

# Disconnect specific org
sma sf disconnect --alias sandbox
```

This removes:
- Credentials from OS keyring
- Org record from database

## Technical Implementation

### Files Created

- `src/sma/salesforce/__init__.py` - Package initialization
- `src/sma/salesforce/auth.py` - OAuth authentication logic
- `src/sma/salesforce/connection.py` - Connection management
- `src/sma/cli.py` - Updated with `sf` command group
- `src/sma/database.py` - Added `salesforce_orgs` table

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS salesforce_orgs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT UNIQUE NOT NULL,           -- 18-character Salesforce org ID
    instance_url TEXT NOT NULL,            -- Instance URL
    org_name TEXT NOT NULL,                -- User's alias for org
    org_type TEXT,                         -- Production or Sandbox
    is_active BOOLEAN DEFAULT 1,           -- Currently active org
    last_sync DATETIME,                    -- Last metadata sync
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_org_id` on `org_id`
- `idx_is_active` on `is_active`

### Authentication Architecture

**OAuth 2.0 Web Server Flow:**
1. Generate authorization URL with client_id and callback URL
2. Open browser to Salesforce login
3. Start local HTTP server on port 8765
4. Receive authorization code from callback
5. Exchange code for access_token and refresh_token
6. Store tokens securely

**Credential Storage:**
- Uses Python `keyring` library
- Credentials stored in OS-specific secure storage:
  - Windows: Windows Credential Manager
  - macOS: Keychain
  - Linux: Secret Service/Keyring
- Service name: `SMA_Salesforce`
- Account name: Org alias

**Stored Credentials:**
```json
{
    "access_token": "00D...",
    "refresh_token": "5Aep...",
    "instance_url": "https://...",
    "id": "https://login.salesforce.com/id/{orgId}/{userId}",
    "issued_at": "1699..."
}
```

### Security Features

1. **No password storage** - Uses OAuth only
2. **Secure credential storage** - OS keyring, not database
3. **Token refresh support** - Refresh tokens for long-term access
4. **Local callback server** - No external dependencies
5. **HTTPS only** - All Salesforce communication over HTTPS

### Dependencies

- `simple-salesforce` - Salesforce API client
- `keyring` - Secure credential storage
- `requests` - HTTP client for OAuth flow
- `rich` - Enhanced CLI output

### Error Handling

- **Network errors:** Clear error messages about connectivity
- **Authentication timeout:** 5-minute timeout for OAuth callback
- **Invalid credentials:** Helpful error messages
- **Expired tokens:** Prompts to reconnect (refresh token support coming)
- **Port conflicts:** Error if port 8765 already in use

## Usage Examples

### First-Time Setup

```bash
# 1. Create Connected App in Salesforce (see Prerequisites)

# 2. Connect to your org
sma sf connect --alias myorg --client-id 3MVG9... --client-secret ABC123...

# Browser opens for login → Authenticate → Return to terminal

# 3. Check connection
sma sf status

# 4. You're ready to sync metadata!
```

### Working with Multiple Orgs

```bash
# Connect to production
sma sf connect --alias prod --client-id ... --client-secret ...

# Connect to sandbox
sma sf connect --alias sandbox --client-id ... --client-secret ... --sandbox

# List all orgs
sma sf list

# Switch to sandbox
sma sf switch sandbox

# Check which is active
sma sf status

# Switch back to prod
sma sf switch prod
```

## Limitations & Future Enhancements

### Current Limitations
- Manual token refresh (no automatic refresh yet)
- No token expiration handling
- Cannot edit Connected App credentials after connection
- Port 8765 must be available

### Planned Enhancements
- Automatic token refresh using refresh_token
- Token expiration detection and auto-refresh
- Support for device flow (for environments without browser)
- Support for JWT bearer flow (server-to-server)
- Ability to update Connected App credentials
- Configurable callback port
- Connection testing command (`sma sf test`)

## Troubleshooting

### Browser doesn't open
- Manually copy the URL from terminal and paste in browser
- Check if default browser is set

### Callback timeout
- Make sure you complete authentication within 5 minutes
- Check firewall isn't blocking port 8765
- Ensure you're using the correct callback URL in Connected App

### "No credentials found"
- Run `sma sf connect` to authenticate again
- Check OS keyring/credential manager is working

### "Port already in use"
- Another application is using port 8765
- Close other applications or wait and try again

### Access token expired
- Run `sma sf connect` again to re-authenticate
- Future: Will implement automatic token refresh

## Next Phase

Phase 2 will implement metadata retrieval:
- Sync Salesforce objects and fields
- Store metadata in local database
- Enable offline querying
