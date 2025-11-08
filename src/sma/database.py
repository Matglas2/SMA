"""Database management for SMA."""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """SQLite database manager for SMA."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.
                    Defaults to 'sma.db' in the user's home directory.
        """
        if db_path is None:
            db_path = str(Path.home() / ".sma" / "sma.db")

        self.db_path = db_path
        self._ensure_db_directory()
        self.conn = None

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()
        return self.conn

    def _initialize_schema(self):
        """Initialize database schema if not exists."""
        cursor = self.conn.cursor()

        # Example table for tracking greetings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                username TEXT
            )
        """)

        # Table for storing quotes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for Salesforce organizations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salesforce_orgs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT UNIQUE NOT NULL,
                instance_url TEXT NOT NULL,
                org_name TEXT NOT NULL,
                org_type TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_sync DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for Salesforce orgs
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_org_id ON salesforce_orgs(org_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_active ON salesforce_orgs(is_active)
        """)

        self.conn.commit()
        self._seed_quotes(cursor)

    def _seed_quotes(self, cursor):
        """Seed initial quotes if the table is empty."""
        cursor.execute("SELECT COUNT(*) as count FROM quotes")
        count = cursor.fetchone()[0]

        if count == 0:
            # Initial quotes collection
            initial_quotes = [
                ("The only way to do great work is to love what you do.", "Steve Jobs"),
                ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
                ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
                ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
                ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
                ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
                ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
                ("It is never too late to be what you might have been.", "George Eliot"),
                ("The only impossible journey is the one you never begin.", "Tony Robbins"),
                ("Life is 10% what happens to you and 90% how you react to it.", "Charles R. Swindoll"),
            ]

            cursor.executemany(
                "INSERT INTO quotes (text, author) VALUES (?, ?)",
                initial_quotes
            )
            self.conn.commit()

    def get_random_quote(self):
        """Get a random quote from the database.

        Returns:
            dict: A quote dictionary with 'text' and 'author' keys, or None if no quotes exist.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT text, author FROM quotes ORDER BY RANDOM() LIMIT 1")
        result = cursor.fetchone()

        if result:
            return {"text": result["text"], "author": result["author"]}
        return None

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
