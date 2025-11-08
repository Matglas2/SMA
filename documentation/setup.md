# SMA Setup Guide

## Prerequisites

- Python 3.8 or higher
- Windows operating system
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Matglas2/SMA.git
cd SMA
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install SMA in Development Mode

```bash
pip install -e .
```

This installs SMA as an editable package, allowing you to run `sma` commands from anywhere.

## Verification

Test the installation:

```bash
sma --help
```

You should see the help message with available commands.

## Database Location

The SQLite database will be automatically created at:
```
C:\Users\<YourUsername>\.sma\sma.db
```

The database and all necessary tables are created automatically on first use.

## Troubleshooting

### Command not found

If `sma` command is not found after installation:
1. Make sure you activated the virtual environment
2. Reinstall with `pip install -e .`
3. Check that Python Scripts directory is in your PATH

### Permission errors

Run your terminal as Administrator if you encounter permission issues during installation.

### Import errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Next Steps

- See [Feature Documentation](features/) for usage guides
- Check [CLAUDE.md](../CLAUDE.md) for development guidelines
