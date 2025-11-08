# SMA

A SQLite-powered CLI application for Windows built with Python.

## Features

- **Interactive CLI** - Built with Click framework for an intuitive command-line experience
- **SQLite Database** - Persistent data storage in your home directory
- **Colorful Output** - Terminal styling for enhanced readability
- **Greeting Command** - Start your day with inspiring quotes (stored in database) and ASCII art

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install SMA
pip install -e .
```

### Usage

```bash
# Get help
sma --help

# Get a friendly greeting
sma hello

# Personalized greeting
sma hello --name "Your Name"
```

## Documentation

Full documentation is available in the `documentation/` folder:
- [Setup Guide](documentation/setup.md)
- [Feature Documentation](documentation/features/)

## Project Structure

- `src/sma/` - Main application code
  - `cli.py` - CLI commands and interface
  - `database.py` - SQLite database management
- `documentation/` - Feature documentation and guides

## Development

When adding new features:
1. Implement in `src/sma/`
2. Add CLI commands in `cli.py`
3. Update database schema in `database.py` if needed
4. **Document in `documentation/features/`** (required!)

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
