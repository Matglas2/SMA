"""
Shell completion functions for SMA CLI commands.

Provides dynamic autocomplete for:
- Salesforce object names
- Field names (context-aware based on selected object)
- Flow names
- Org aliases
"""

import click
from pathlib import Path
from typing import List
import sqlite3


def get_database_path() -> Path:
    """Get the database file path."""
    return Path.home() / ".sma" / "sma.db"


def complete_salesforce_objects(ctx, param, incomplete: str) -> List[click.shell_completion.CompletionItem]:
    """
    Autocomplete Salesforce object names from database.

    Returns object API names with labels as help text.
    Limited to 50 results for performance.
    """
    db_path = get_database_path()

    # Return empty list if database doesn't exist
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query objects with prefix matching
        cursor.execute("""
            SELECT api_name, label
            FROM sobjects
            WHERE api_name LIKE ? OR label LIKE ?
            ORDER BY api_name
            LIMIT 50
        """, (f"{incomplete}%", f"{incomplete}%"))

        results = []
        for row in cursor.fetchall():
            api_name = row['api_name']
            label = row['label']
            help_text = label if label != api_name else None
            results.append(click.shell_completion.CompletionItem(api_name, help=help_text))

        conn.close()
        return results

    except Exception:
        # Return empty list on any error
        return []


def complete_salesforce_fields(ctx, param, incomplete: str) -> List[click.shell_completion.CompletionItem]:
    """
    Autocomplete Salesforce field names (context-aware).

    If an object_name was provided earlier in the command, only show fields for that object.
    Otherwise, show all fields.

    Returns field API names with type and label as help text.
    Limited to 50 results for performance.
    """
    db_path = get_database_path()

    # Return empty list if database doesn't exist
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try to get object_name from context (if provided as earlier argument)
        object_name = ctx.params.get('object_name')

        if object_name:
            # Context-aware: Filter by object
            cursor.execute("""
                SELECT api_name, label, type
                FROM fields
                WHERE sobject_name = ?
                  AND (api_name LIKE ? OR label LIKE ?)
                ORDER BY api_name
                LIMIT 50
            """, (object_name, f"{incomplete}%", f"{incomplete}%"))
        else:
            # Show all fields
            cursor.execute("""
                SELECT api_name, label, type, sobject_name
                FROM fields
                WHERE api_name LIKE ? OR label LIKE ?
                ORDER BY api_name
                LIMIT 50
            """, (f"{incomplete}%", f"{incomplete}%"))

        results = []
        for row in cursor.fetchall():
            api_name = row['api_name']
            label = row['label']
            field_type = row['type']

            # Build help text
            if object_name:
                help_text = f"{label} ({field_type})" if label != api_name else f"({field_type})"
            else:
                sobject = row['sobject_name']
                help_text = f"{sobject}.{label} ({field_type})"

            results.append(click.shell_completion.CompletionItem(api_name, help=help_text))

        conn.close()
        return results

    except Exception:
        # Return empty list on any error
        return []


def complete_flow_names(ctx, param, incomplete: str) -> List[click.shell_completion.CompletionItem]:
    """
    Autocomplete Flow names from database.

    Returns flow API names with active/inactive status and version info.
    Limited to 50 results for performance.
    """
    db_path = get_database_path()

    # Return empty list if database doesn't exist
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query flows with prefix matching
        cursor.execute("""
            SELECT api_name, label, process_type, status
            FROM sf_flow_metadata
            WHERE api_name LIKE ? OR label LIKE ?
            ORDER BY api_name
            LIMIT 50
        """, (f"{incomplete}%", f"{incomplete}%"))

        results = []
        for row in cursor.fetchall():
            api_name = row['api_name']
            label = row['label']
            process_type = row['process_type'] or 'Flow'
            status = row['status'] or 'Unknown'

            # Build help text with type and status
            help_text = f"{label} ({process_type}, {status})" if label != api_name else f"({process_type}, {status})"
            results.append(click.shell_completion.CompletionItem(api_name, help=help_text))

        conn.close()
        return results

    except Exception:
        # Return empty list on any error
        return []


def complete_org_aliases(ctx, param, incomplete: str) -> List[click.shell_completion.CompletionItem]:
    """
    Autocomplete Salesforce org aliases from database.

    Returns org aliases with type (Production/Sandbox) and instance URL.
    Limited to 50 results for performance.
    """
    db_path = get_database_path()

    # Return empty list if database doesn't exist
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query org aliases with prefix matching
        cursor.execute("""
            SELECT alias, org_type, instance_url
            FROM salesforce_orgs
            WHERE alias LIKE ?
            ORDER BY alias
            LIMIT 50
        """, (f"{incomplete}%",))

        results = []
        for row in cursor.fetchall():
            alias = row['alias']
            org_type = row['org_type'] or 'Production'
            instance_url = row['instance_url']

            # Build help text with type and URL
            help_text = f"{org_type} - {instance_url}" if instance_url else org_type
            results.append(click.shell_completion.CompletionItem(alias, help=help_text))

        conn.close()
        return results

    except Exception:
        # Return empty list on any error
        return []
