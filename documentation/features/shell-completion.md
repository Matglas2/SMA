# Shell Completion Feature

**Feature Status:** ✅ Implemented
**Version:** 0.1.0
**Date Added:** 2025-11-09
**Phase:** 4 (MVP - Step 4)

---

## Overview

Shell autocomplete provides intelligent tab-completion for SMA CLI commands across multiple shells. When you start typing a command and press TAB, the shell will suggest completions based on:

- **Object names** from your synced Salesforce metadata
- **Field names** (context-aware, filtered by selected object)
- **Flow names** with active/inactive status
- **Org aliases** with environment type

This dramatically speeds up command usage by eliminating the need to remember exact API names and reducing typing errors.

---

## Supported Shells

| Shell | Minimum Version | Platform Support | Help Text |
|-------|----------------|------------------|-----------|
| **Bash** | 4.4+ | Linux, Mac, WSL | No |
| **Zsh** | 5.0+ | Mac, Linux | Yes |
| **Fish** | 3.0+ | Linux, Mac | Yes |
| **PowerShell** | 7.0+ | Windows, Mac, Linux | Yes |

**Note:** PowerShell 5.1 (Windows default) is NOT supported. You must use PowerShell 7+ (PowerShell Core).

---

## Installation

### Quick Setup

Use the built-in installation helper:

```bash
sma completion install <shell>
```

Examples:
```bash
sma completion install bash
sma completion install zsh
sma completion install fish
sma completion install powershell
```

This command will display shell-specific instructions for your environment.

---

### Manual Installation

#### Bash

Add to `~/.bashrc`:

```bash
eval "$(_SMA_COMPLETE=bash_source sma)"
```

Reload:
```bash
source ~/.bashrc
```

#### Zsh

Add to `~/.zshrc`:

```zsh
eval "$(_SMA_COMPLETE=zsh_source sma)"
```

Reload:
```zsh
source ~/.zshrc
```

#### Fish

Create/edit `~/.config/fish/completions/sma.fish`:

```fish
eval (env _SMA_COMPLETE=fish_source sma)
```

Fish will automatically load completions on next launch.

#### PowerShell 7+

Add to your PowerShell profile (find with `$PROFILE`):

```powershell
Invoke-Expression (& sma completion show powershell)
```

Reload:
```powershell
. $PROFILE
```

**Important:** PowerShell 5.1 is NOT supported. Install PowerShell 7+:
- Windows: `winget install Microsoft.PowerShell`
- Mac: `brew install powershell`
- Linux: Follow [official guide](https://docs.microsoft.com/powershell/scripting/install/installing-powershell)

---

## Usage Examples

### Object Name Completion

Start typing an object name and press TAB:

```bash
$ sma sf analyse field-flows Acc<TAB>
Account  AccountContactRole  AccountHistory  Acc_Custom__c
```

### Field Name Completion (Context-Aware)

After selecting an object, field completions are filtered to that object:

```bash
$ sma sf analyse field-flows Account Em<TAB>
Email  Employee_Number__c  Emergency_Contact__c
```

In Zsh, Fish, and PowerShell, you'll see help text:
```
Email (Text)
Employee_Number__c (Number)
Emergency_Contact__c (Text)
```

### Flow Name Completion

```bash
$ sma sf analyse flow-fields Update<TAB>
Update_Account_Flow  Update_Contact_Flow  Update_Opportunity_Flow
```

With help text (Zsh/Fish/PowerShell):
```
Update_Account_Flow (Flow, Active)
Update_Contact_Flow (Flow, Inactive)
Update_Opportunity_Flow (Process, Active)
```

### Org Alias Completion

```bash
$ sma sf switch prod<TAB>
production  prod-sandbox  prod-dev
```

With help text:
```
production (Production - https://login.salesforce.com)
prod-sandbox (Sandbox - https://test.salesforce.com)
prod-dev (Developer - https://mycompany.my.salesforce.com)
```

---

## Commands with Autocomplete

### Salesforce Commands

| Command | Autocomplete For |
|---------|------------------|
| `sma sf switch <alias>` | Org aliases |
| `sma sf disconnect --alias <alias>` | Org aliases |
| `sma sf search <query> --alias <alias>` | Org aliases |

### Analysis Commands

| Command | Autocomplete For |
|---------|------------------|
| `sma sf analyse field-flows <object> <field>` | Objects, Fields (context-aware), Org aliases |
| `sma sf analyse field-triggers <object> <field>` | Objects, Fields (context-aware), Org aliases |
| `sma sf analyse field-deps <object> <field>` | Objects, Fields (context-aware), Org aliases |
| `sma sf analyse flow-fields <flow>` | Flow names, Org aliases |
| `sma sf analyse object-relationships <object>` | Objects, Org aliases |

---

## Technical Implementation

### Architecture

**Completion Module:** `src/sma/completion.py`

Provides four main completion functions:
1. `complete_salesforce_objects()` - Object API names from `sobjects` table
2. `complete_salesforce_fields()` - Field API names from `fields` table (context-aware)
3. `complete_flow_names()` - Flow names from `sf_flow_metadata` table
4. `complete_org_aliases()` - Org aliases from `salesforce_orgs` table

### Database Queries

All completion functions query the local SQLite database with:
- **Prefix matching:** `WHERE api_name LIKE ?` with `"{incomplete}%"`
- **Performance limit:** `LIMIT 50` to ensure fast response
- **Indexes:** Leverages existing database indexes on API names
- **Error handling:** Returns empty list on any error (graceful degradation)

### Context-Aware Field Completion

The `complete_salesforce_fields()` function checks the Click context for a previously entered `object_name` parameter:

```python
object_name = ctx.params.get('object_name')
```

If found, it filters fields to only that object. Otherwise, shows all fields across all objects.

### Help Text

Completion items include help text where supported (Zsh, Fish, PowerShell):

```python
click.shell_completion.CompletionItem(
    value=api_name,
    help=f"{label} ({field_type})"
)
```

---

## Performance

### Target Metrics

- **Query time:** < 50ms per completion request
- **Results limit:** 50 items max
- **Database access:** Direct SQLite queries (no ORM overhead)
- **Caching:** Browser-level caching (shell manages completion cache)

### Optimization Strategies

1. **LIMIT 50** - Prevents slow queries on large datasets
2. **Prefix matching only** - Uses indexes efficiently (`LIKE 'prefix%'`)
3. **Direct SQL queries** - No ORM overhead
4. **Graceful errors** - Returns empty list instead of crashing

---

## Dependencies

### Required

- `click>=8.0.0` - Native completion for Bash, Zsh, Fish
- `click-pwsh>=0.9.5` - PowerShell 7 completion support

### Installation

Already included in `requirements.txt` and `pyproject.toml`:

```txt
click>=8.0.0
click-pwsh>=0.9.5
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Troubleshooting

### Completion Not Working

**Check shell version:**
```bash
# Bash
bash --version  # Need 4.4+

# Zsh
zsh --version  # Need 5.0+

# Fish
fish --version  # Need 3.0+

# PowerShell
$PSVersionTable  # Need 7.0+
```

**Verify installation:**
```bash
# Show completion script
sma completion show <shell>

# Should output completion script, not an error
```

**Check database exists:**
```bash
sma db path

# Database should exist and have data
# Run 'sma sf sync' if needed
```

### No Suggestions Appearing

**Possible causes:**

1. **Database not synced:**
   ```bash
   sma sf sync
   ```

2. **Not connected to Salesforce:**
   ```bash
   sma sf status
   ```

3. **Shell completion not loaded:**
   - Restart terminal
   - Re-source config file (`source ~/.bashrc`, etc.)

### PowerShell Issues

**Error: "click-pwsh not installed"**

```powershell
pip install click-pwsh
```

**Error: "Command not found"**

Ensure PowerShell 7+ is in your PATH:
```powershell
$PSVersionTable.PSVersion  # Should be 7.0 or higher
```

If using Windows PowerShell 5.1, install PowerShell 7:
```powershell
winget install Microsoft.PowerShell
```

---

## Limitations

1. **Completion requires synced data:**
   - Must run `sma sf sync` first
   - Completions reflect last sync state
   - Won't show metadata added since last sync

2. **50 result limit:**
   - Only first 50 matches shown
   - Type more characters to narrow results

3. **No fuzzy matching:**
   - Prefix matching only (e.g., "Acc" matches "Account")
   - Does not match in middle of words (e.g., "count" won't match "Account")

4. **Context-awareness limitations:**
   - Field completion only context-aware within same command
   - Cannot detect object from previous command in shell history

---

## Future Enhancements

Potential improvements for future versions:

1. **Caching layer:**
   - In-memory cache for frequently accessed completions
   - Reduce database queries for better performance

2. **Fuzzy matching:**
   - Use RapidFuzz for smarter matching
   - Match anywhere in string (e.g., "cont" → "AccountContactRole")

3. **Descriptions from metadata:**
   - Show field help text in completions
   - Display object descriptions

4. **Recently used items:**
   - Prioritize recently accessed objects/fields
   - Track usage statistics

5. **Smart filtering:**
   - Hide deprecated fields
   - Show only queryable/updateable fields based on context

---

## Related Commands

- `sma completion install <shell>` - Show installation instructions
- `sma completion show <shell>` - Display completion script
- `sma sf sync` - Sync metadata for completions
- `sma db browse` - Browse available metadata

---

## Files Modified/Created

### New Files
- `src/sma/completion.py` - Completion functions module
- `documentation/features/shell-completion.md` - This documentation

### Modified Files
- `src/sma/cli.py` - Added shell_complete parameters to commands, completion command group
- `requirements.txt` - Added click-pwsh dependency
- `pyproject.toml` - Added click-pwsh dependency

---

## References

- [Click Shell Completion Documentation](https://click.palletsprojects.com/shell-completion/)
- [click-pwsh GitHub Repository](https://github.com/click-contrib/click-pwsh)
- [PowerShell Installation Guide](https://docs.microsoft.com/powershell/scripting/install/installing-powershell)
