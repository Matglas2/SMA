"""Salesforce metadata synchronization module."""

import json
from datetime import datetime
from typing import Dict, List, Optional
from simple_salesforce import Salesforce
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class MetadataSync:
    """Handles synchronization of Salesforce metadata to local database."""

    def __init__(self, sf_client: Salesforce, db_connection, org_id: str):
        """Initialize metadata sync.

        Args:
            sf_client: Authenticated Salesforce client
            db_connection: Database connection
            org_id: Salesforce org ID
        """
        self.sf = sf_client
        self.conn = db_connection
        self.org_id = org_id

    def sync_all(self) -> Dict[str, int]:
        """Sync all metadata (objects and fields).

        Returns:
            Dictionary with counts of synced objects and fields
        """
        console.print("\n[bold cyan]Starting metadata synchronization...[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Sync objects
            task1 = progress.add_task("[cyan]Retrieving object metadata...", total=None)
            sobject_count = self.sync_sobjects()
            progress.update(task1, completed=True)
            console.print(f"[green]✓[/green] Synced {sobject_count} objects")

            # Sync fields for each object
            task2 = progress.add_task("[cyan]Retrieving field metadata...", total=None)
            field_count = self.sync_fields()
            progress.update(task2, completed=True)
            console.print(f"[green]✓[/green] Synced {field_count} fields")

        # Update last sync timestamp
        self._update_last_sync()

        console.print(f"\n[bold green]✓ Synchronization complete![/bold green]\n")

        return {
            'objects': sobject_count,
            'fields': field_count
        }

    def sync_sobjects(self) -> int:
        """Sync Salesforce object (sobject) metadata.

        Returns:
            Number of objects synced
        """
        # Get all sobjects from Salesforce
        sobjects_desc = self.sf.describe()
        sobjects = sobjects_desc['sobjects']

        cursor = self.conn.cursor()
        synced_count = 0

        for sobject in sobjects:
            # Extract key metadata
            api_name = sobject['name']
            label = sobject['label']
            plural_label = sobject['labelPlural']
            is_custom = sobject['custom']
            key_prefix = sobject.get('keyPrefix')
            is_queryable = sobject['queryable']
            is_createable = sobject['createable']
            is_updateable = sobject['updateable']
            is_deletable = sobject['deletable']

            # Store full metadata as JSON
            metadata_json = json.dumps(sobject)

            # Insert or update sobject
            cursor.execute("""
                INSERT OR REPLACE INTO sobjects
                (org_id, api_name, label, plural_label, is_custom, key_prefix,
                 is_queryable, is_createable, is_updateable, is_deletable,
                 metadata, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.org_id, api_name, label, plural_label, is_custom, key_prefix,
                is_queryable, is_createable, is_updateable, is_deletable,
                metadata_json, datetime.now().isoformat()
            ))

            synced_count += 1

        self.conn.commit()
        return synced_count

    def sync_fields(self) -> int:
        """Sync field metadata for all objects.

        Returns:
            Number of fields synced
        """
        cursor = self.conn.cursor()

        # Get all sobjects from database
        cursor.execute("""
            SELECT id, org_id, api_name
            FROM sobjects
            WHERE org_id = ?
        """, (self.org_id,))

        sobjects = cursor.fetchall()
        total_fields = 0

        for sobject_row in sobjects:
            sobject_id = sobject_row['id']
            sobject_api_name = sobject_row['api_name']

            # Get detailed object description with fields
            try:
                obj_desc = getattr(self.sf, sobject_api_name).describe()
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Could not describe {sobject_api_name}: {e}")
                continue

            fields = obj_desc.get('fields', [])

            for field in fields:
                field_count = self._sync_field(sobject_id, field)
                total_fields += field_count

        self.conn.commit()
        return total_fields

    def _sync_field(self, sobject_id: int, field_data: Dict) -> int:
        """Sync a single field.

        Args:
            sobject_id: Database ID of the parent sobject
            field_data: Field metadata from Salesforce

        Returns:
            1 if field was synced, 0 otherwise
        """
        cursor = self.conn.cursor()

        # Extract field metadata
        api_name = field_data['name']
        label = field_data['label']
        field_type = field_data['type']
        length = field_data.get('length')
        is_custom = field_data['custom']
        is_required = not field_data['nillable']
        is_unique = field_data.get('unique', False)

        # For lookup/master-detail fields
        reference_to = None
        relationship_name = None
        if field_data.get('referenceTo'):
            reference_to = ','.join(field_data['referenceTo'])
            relationship_name = field_data.get('relationshipName')

        # Formula and default value
        formula = field_data.get('calculatedFormula')
        default_value = field_data.get('defaultValue')
        if default_value and not isinstance(default_value, str):
            default_value = str(default_value)

        help_text = field_data.get('inlineHelpText')

        # Store full metadata as JSON
        metadata_json = json.dumps(field_data)

        # Insert or update field
        cursor.execute("""
            INSERT OR REPLACE INTO fields
            (org_id, sobject_id, api_name, label, type, length, is_custom,
             is_required, is_unique, reference_to, relationship_name, formula,
             default_value, help_text, metadata, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.org_id, sobject_id, api_name, label, field_type, length,
            is_custom, is_required, is_unique, reference_to, relationship_name,
            formula, default_value, help_text, metadata_json,
            datetime.now().isoformat()
        ))

        return 1

    def _update_last_sync(self):
        """Update the last_sync timestamp for the org."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE salesforce_orgs
            SET last_sync = ?, updated_at = ?
            WHERE org_id = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), self.org_id))
        self.conn.commit()

    def get_sync_stats(self) -> Dict[str, any]:
        """Get synchronization statistics.

        Returns:
            Dictionary with sync stats
        """
        cursor = self.conn.cursor()

        # Get object count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sobjects
            WHERE org_id = ?
        """, (self.org_id,))
        object_count = cursor.fetchone()['count']

        # Get field count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM fields
            WHERE org_id = ?
        """, (self.org_id,))
        field_count = cursor.fetchone()['count']

        # Get last sync time
        cursor.execute("""
            SELECT last_sync
            FROM salesforce_orgs
            WHERE org_id = ?
        """, (self.org_id,))
        row = cursor.fetchone()
        last_sync = row['last_sync'] if row else None

        # Get custom object/field counts
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sobjects
            WHERE org_id = ? AND is_custom = 1
        """, (self.org_id,))
        custom_objects = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM fields
            WHERE org_id = ? AND is_custom = 1
        """, (self.org_id,))
        custom_fields = cursor.fetchone()['count']

        return {
            'total_objects': object_count,
            'total_fields': field_count,
            'custom_objects': custom_objects,
            'custom_fields': custom_fields,
            'last_sync': last_sync
        }
