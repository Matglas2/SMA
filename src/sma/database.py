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

    def _run_migrations(self, cursor):
        """Run database migrations to fix schema issues.

        Args:
            cursor: Database cursor
        """
        # Migration 1: Remove duplicates from sobjects
        self._remove_sobject_duplicates(cursor)

        # Migration 2: Remove duplicates from fields
        self._remove_field_duplicates(cursor)

        # Migration 3: Remove duplicates from sf_flow_field_references
        self._remove_flow_field_duplicates(cursor)

        # Migration 4: Remove duplicates from sf_field_dependencies
        self._remove_field_dependency_duplicates(cursor)

    def _remove_sobject_duplicates(self, cursor):
        """Remove duplicate entries from sobjects table.

        Keeps the most recent entry based on id (auto-increment).
        """
        try:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sobjects'
            """)
            if not cursor.fetchone():
                return  # Table doesn't exist yet

            # Remove duplicates, keeping the one with the highest id (most recent)
            cursor.execute("""
                DELETE FROM sobjects
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM sobjects
                    GROUP BY org_id, api_name
                )
            """)

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} duplicate sobjects")

            self.conn.commit()
        except Exception as e:
            # Silently handle if the table structure is different
            pass

    def _remove_field_duplicates(self, cursor):
        """Remove duplicate entries from fields table.

        Keeps the most recent entry based on id (auto-increment).
        """
        try:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='fields'
            """)
            if not cursor.fetchone():
                return  # Table doesn't exist yet

            # Remove duplicates, keeping the one with the highest id (most recent)
            cursor.execute("""
                DELETE FROM fields
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM fields
                    GROUP BY org_id, sobject_id, api_name
                )
            """)

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} duplicate fields")

            self.conn.commit()
        except Exception as e:
            # Silently handle if the table structure is different
            pass

    def _remove_flow_field_duplicates(self, cursor):
        """Remove duplicate entries from sf_flow_field_references table.

        Keeps the most recent entry based on id (auto-increment).
        """
        try:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sf_flow_field_references'
            """)
            if not cursor.fetchone():
                return  # Table doesn't exist yet

            # Remove duplicates, keeping the one with the highest id (most recent)
            cursor.execute("""
                DELETE FROM sf_flow_field_references
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM sf_flow_field_references
                    GROUP BY flow_id, flow_version, object_name, field_name, element_name, element_type
                )
            """)

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} duplicate flow field references")

            self.conn.commit()
        except Exception as e:
            # Silently handle if the table structure is different
            pass

    def _remove_field_dependency_duplicates(self, cursor):
        """Remove duplicate entries from sf_field_dependencies table.

        Keeps the most recent entry based on id (auto-increment).
        """
        try:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sf_field_dependencies'
            """)
            if not cursor.fetchone():
                return  # Table doesn't exist yet

            # Remove duplicates, keeping the one with the highest id (most recent)
            cursor.execute("""
                DELETE FROM sf_field_dependencies
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM sf_field_dependencies
                    GROUP BY connection_alias, object_name, field_name, dependent_type, dependent_id, reference_type
                )
            """)

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} duplicate field dependencies")

            self.conn.commit()
        except Exception as e:
            # Silently handle if the table structure is different
            pass

    def _initialize_schema(self):
        """Initialize database schema if not exists."""
        cursor = self.conn.cursor()

        # Run migrations to clean up duplicates before adding constraints
        self._run_migrations(cursor)

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

        # Table for Salesforce objects (sobjects)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sobjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                api_name TEXT NOT NULL,
                label TEXT,
                plural_label TEXT,
                is_custom BOOLEAN,
                key_prefix TEXT,
                is_queryable BOOLEAN,
                is_createable BOOLEAN,
                is_updateable BOOLEAN,
                is_deletable BOOLEAN,
                metadata TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(org_id, api_name)
            )
        """)

        # Create indexes for sobjects
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sobject_org_api ON sobjects(org_id, api_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sobject_custom ON sobjects(is_custom)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sobject_label ON sobjects(label)
        """)

        # Table for Salesforce fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                sobject_id INTEGER NOT NULL,
                api_name TEXT NOT NULL,
                label TEXT,
                type TEXT,
                length INTEGER,
                is_custom BOOLEAN,
                is_required BOOLEAN,
                is_unique BOOLEAN,
                reference_to TEXT,
                relationship_name TEXT,
                formula TEXT,
                default_value TEXT,
                help_text TEXT,
                metadata TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sobject_id) REFERENCES sobjects(id) ON DELETE CASCADE,
                UNIQUE(org_id, sobject_id, api_name)
            )
        """)

        # Create indexes for fields
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_org_sobject ON fields(org_id, sobject_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_api_name ON fields(api_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_label ON fields(label)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_type ON fields(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_reference ON fields(reference_to)
        """)

        # ===== Phase 3: Dependency and Relationship Tables =====

        # Table for field dependencies (central dependency tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_field_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_alias TEXT NOT NULL,
                object_name TEXT NOT NULL,
                field_name TEXT NOT NULL,
                dependent_type TEXT NOT NULL,
                dependent_id TEXT NOT NULL,
                dependent_name TEXT,
                reference_type TEXT,
                line_number INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_verified DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(connection_alias, object_name, field_name, dependent_type, dependent_id, reference_type)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_dep_object_field
            ON sf_field_dependencies(object_name, field_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_dep_dependent
            ON sf_field_dependencies(dependent_type, dependent_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_dep_alias
            ON sf_field_dependencies(connection_alias)
        """)

        # Table for detailed flow field references
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_flow_field_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                flow_api_name TEXT NOT NULL,
                flow_version INTEGER,
                object_name TEXT NOT NULL,
                field_name TEXT NOT NULL,
                element_name TEXT,
                element_type TEXT,
                is_input BOOLEAN DEFAULT 0,
                is_output BOOLEAN DEFAULT 0,
                variable_name TEXT,
                xpath_location TEXT,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(flow_id, flow_version, object_name, field_name, element_name, element_type)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_ref_flow
            ON sf_flow_field_references(flow_id, flow_version)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_ref_field
            ON sf_flow_field_references(object_name, field_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_ref_element_type
            ON sf_flow_field_references(element_type)
        """)

        # Table for field relationships (lookups, master-detail, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_field_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_alias TEXT NOT NULL,
                source_object TEXT NOT NULL,
                source_field TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                target_object TEXT,
                target_field TEXT,
                relationship_name TEXT,
                is_cascade_delete BOOLEAN DEFAULT 0,
                is_reparentable BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_rel_source
            ON sf_field_relationships(source_object, source_field)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_rel_target
            ON sf_field_relationships(target_object)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_rel_type
            ON sf_field_relationships(relationship_type)
        """)

        # Table for object-level relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_object_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_alias TEXT NOT NULL,
                parent_object TEXT NOT NULL,
                child_object TEXT NOT NULL,
                relationship_field TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                relationship_name TEXT,
                child_count_estimate INTEGER
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_obj_rel_parent
            ON sf_object_relationships(parent_object)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_obj_rel_child
            ON sf_object_relationships(child_object)
        """)

        # Table for enhanced trigger metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_trigger_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id TEXT UNIQUE NOT NULL,
                trigger_name TEXT NOT NULL,
                object_name TEXT NOT NULL,
                is_before_insert BOOLEAN DEFAULT 0,
                is_before_update BOOLEAN DEFAULT 0,
                is_before_delete BOOLEAN DEFAULT 0,
                is_after_insert BOOLEAN DEFAULT 0,
                is_after_update BOOLEAN DEFAULT 0,
                is_after_delete BOOLEAN DEFAULT 0,
                is_after_undelete BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_date DATETIME,
                last_modified_date DATETIME,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trigger_meta_object
            ON sf_trigger_metadata(object_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trigger_meta_active
            ON sf_trigger_metadata(is_active)
        """)

        # Table for enhanced flow metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_flow_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                flow_api_name TEXT NOT NULL,
                flow_label TEXT,
                process_type TEXT,
                trigger_type TEXT,
                trigger_object TEXT,
                is_active BOOLEAN DEFAULT 0,
                is_template BOOLEAN DEFAULT 0,
                version_number INTEGER,
                status TEXT,
                element_count INTEGER,
                decision_count INTEGER,
                has_record_lookups BOOLEAN DEFAULT 0,
                has_record_updates BOOLEAN DEFAULT 0,
                has_record_creates BOOLEAN DEFAULT 0,
                has_record_deletes BOOLEAN DEFAULT 0,
                last_modified_date DATETIME,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                xml_parsed_at DATETIME,
                UNIQUE(flow_api_name, version_number)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_meta_api_version
            ON sf_flow_metadata(flow_api_name, version_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_meta_trigger_obj
            ON sf_flow_metadata(trigger_object)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flow_meta_active
            ON sf_flow_metadata(is_active)
        """)

        # Table for automation coverage summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sf_automation_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_alias TEXT NOT NULL,
                object_name TEXT NOT NULL,
                field_name TEXT,
                has_flows BOOLEAN DEFAULT 0,
                flow_count INTEGER DEFAULT 0,
                has_triggers BOOLEAN DEFAULT 0,
                trigger_count INTEGER DEFAULT 0,
                has_validation_rules BOOLEAN DEFAULT 0,
                validation_rule_count INTEGER DEFAULT 0,
                has_process_builders BOOLEAN DEFAULT 0,
                process_builder_count INTEGER DEFAULT 0,
                total_automation_count INTEGER DEFAULT 0,
                last_computed DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(connection_alias, object_name, field_name)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auto_cov_object
            ON sf_automation_coverage(object_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auto_cov_field
            ON sf_automation_coverage(object_name, field_name)
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
