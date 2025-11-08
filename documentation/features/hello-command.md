# Hello Command

**Feature Status:** ✅ Implemented
**Version:** 0.1.0
**Date Added:** 2025-11-08

## Overview

The `hello` command greets users with a personalized message, an inspiring quote (retrieved from database), and fun ASCII art. It demonstrates the CLI's ability to provide an engaging user experience with persistent data storage.

## Command Syntax

```bash
sma hello [OPTIONS]
```

### Options

- `--name TEXT`: Your name for a personalized greeting (optional)
  - If not provided, uses the system username (USERNAME or USER environment variable)
  - Falls back to "Friend" if no username is available

### Examples

```bash
# Basic greeting with system username
sma hello

# Personalized greeting
sma hello --name "Alice"
```

## Features

1. **Time-based greeting**: Displays "Good morning", "Good afternoon", or "Good evening" based on current time
2. **Random quotes from database**: Retrieves random inspiring quotes stored in SQLite database
3. **ASCII art**: Shows random ASCII art from a collection of 5 designs
4. **Database logging**: Records each greeting in the SQLite database with timestamp
5. **Greeting counter**: Displays total number of greetings issued
6. **Colorized output**: Uses terminal colors for enhanced visual appeal

## Technical Implementation

### Files Modified/Created

- `src/sma/cli.py`: Main CLI implementation with the `hello` command
- `src/sma/database.py`: Database management with greetings and quotes tables

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS greetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username TEXT
)

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Dependencies

- `click`: CLI framework for command handling and styling
- `sqlite3`: Built-in Python module for database operations
- `random`: For selecting random ASCII art
- `datetime`: For time-based greetings

### Quote Management

**Initial Quotes** (10 total):
- Automatically seeded on first database initialization
- Stored in `quotes` table with text and author
- Retrieved using SQL `ORDER BY RANDOM() LIMIT 1`

**ASCII Art** (5 total):
- Simple text-based art designs
- Stored in `ASCII_ART` list in cli.py
- Windows-compatible ASCII characters only (no emojis for console compatibility)

## Database Storage

Each greeting is logged with:
- Auto-incremented ID
- Timestamp (automatic)
- Username (from command option or environment)

Quotes are stored with:
- Auto-incremented ID
- Quote text
- Author name
- Creation timestamp

Database location: `~/.sma/sma.db` (user's home directory)

## Error Handling

- If database operations fail, the greeting still displays (graceful degradation)
- Missing username defaults to "Friend"
- Database directory created automatically if it doesn't exist
- Fallback quote provided if database quote retrieval fails

## Future Enhancements

Potential improvements for this feature:
- User preferences for favorite quotes
- Add new quotes via CLI command
- Custom ASCII art uploads
- Greeting statistics (daily/weekly counts)
- Multi-language support
- Quote categories (motivation, humor, wisdom, etc.)
- Edit/delete quotes functionality
