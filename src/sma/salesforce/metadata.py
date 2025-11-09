"""Salesforce metadata synchronization module."""

import json
from datetime import datetime
from typing import Dict, List, Optional
from simple_salesforce import Salesforce
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..parsers.flow_parser import FlowParser

console = Console()


class MetadataSync:
    """Handles synchronization of Salesforce metadata to local database."""

    def __init__(self, sf_client: Salesforce, db_connection, org_id: str, connection_alias: str = None):
        """Initialize metadata sync.

        Args:
            sf_client: Authenticated Salesforce client
            db_connection: Database connection
            org_id: Salesforce org ID
            connection_alias: Connection alias for dependency tracking
        """
        self.sf = sf_client
        self.conn = db_connection
        self.org_id = org_id
        self.connection_alias = connection_alias or org_id
        self.flow_parser = FlowParser()

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

            # Phase 3: Sync flows with dependencies
            task3 = progress.add_task("[cyan]Retrieving flow metadata and dependencies...", total=None)
            flow_count = self.sync_flows_with_dependencies()
            progress.update(task3, completed=True)
            console.print(f"[green]✓[/green] Synced {flow_count} flows with field references")

            # Phase 3: Sync triggers
            task4 = progress.add_task("[cyan]Retrieving trigger inventory...", total=None)
            trigger_count = self.sync_trigger_metadata()
            progress.update(task4, completed=True)
            console.print(f"[green]✓[/green] Synced {trigger_count} triggers")

            # Phase 3: Extract field relationships
            task5 = progress.add_task("[cyan]Extracting field relationships...", total=None)
            relationship_count = self.sync_field_relationships()
            progress.update(task5, completed=True)
            console.print(f"[green]✓[/green] Extracted {relationship_count} field relationships")

        # Update last sync timestamp
        self._update_last_sync()

        console.print(f"\n[bold green]✓ Synchronization complete![/bold green]\n")

        return {
            'objects': sobject_count,
            'fields': field_count,
            'flows': flow_count,
            'triggers': trigger_count,
            'relationships': relationship_count
        }

    def sync_sobjects(self) -> int:
        """Sync Salesforce object (sobject) metadata.

        Returns:
            Number of objects synced
        """
        # Get all sobjects from Salesforce
        sobjects_desc = self.sf.describe()
        sobjects = sobjects_desc['sobjects']

        # Query EntityDefinition to get DurableIds for all objects
        entity_durable_ids = self._get_entity_durable_ids()

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

            # Get Salesforce DurableId for this object
            salesforce_id = entity_durable_ids.get(api_name, api_name)  # Fallback to api_name if not found

            # Store full metadata as JSON
            metadata_json = json.dumps(sobject)

            # Use UPSERT based on org_id and salesforce_id
            cursor.execute("""
                INSERT INTO sobjects
                (salesforce_id, org_id, api_name, label, plural_label, is_custom, key_prefix,
                 is_queryable, is_createable, is_updateable, is_deletable,
                 metadata, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(org_id, salesforce_id) DO UPDATE SET
                    api_name = excluded.api_name,
                    label = excluded.label,
                    plural_label = excluded.plural_label,
                    is_custom = excluded.is_custom,
                    key_prefix = excluded.key_prefix,
                    is_queryable = excluded.is_queryable,
                    is_createable = excluded.is_createable,
                    is_updateable = excluded.is_updateable,
                    is_deletable = excluded.is_deletable,
                    metadata = excluded.metadata,
                    synced_at = excluded.synced_at
            """, (
                salesforce_id, self.org_id, api_name, label, plural_label, is_custom, key_prefix,
                is_queryable, is_createable, is_updateable, is_deletable,
                metadata_json, datetime.now().isoformat()
            ))

            synced_count += 1

        self.conn.commit()
        return synced_count

    def _get_entity_durable_ids(self) -> Dict[str, str]:
        """Query EntityDefinition to get DurableIds for all objects.

        Returns:
            Dictionary mapping QualifiedApiName to DurableId
        """
        durable_ids = {}
        try:
            # Query EntityDefinition for all entities
            query = "SELECT QualifiedApiName, DurableId FROM EntityDefinition"
            result = self.sf.query_all(query)

            for record in result.get('records', []):
                api_name = record.get('QualifiedApiName')
                durable_id = record.get('DurableId')
                if api_name and durable_id:
                    durable_ids[api_name] = durable_id

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not query EntityDefinition: {e}")
            console.print("[yellow]⚠[/yellow] Falling back to using API names as identifiers")

        return durable_ids

    def sync_fields(self) -> int:
        """Sync field metadata for all objects.

        Returns:
            Number of fields synced
        """
        cursor = self.conn.cursor()

        # Query FieldDefinition to get DurableIds for all fields
        field_durable_ids = self._get_field_durable_ids()

        # Get all sobjects from database
        cursor.execute("""
            SELECT id, salesforce_id, org_id, api_name
            FROM sobjects
            WHERE org_id = ?
        """, (self.org_id,))

        sobjects = cursor.fetchall()
        total_fields = 0

        for sobject_row in sobjects:
            sobject_id = sobject_row['id']
            sobject_salesforce_id = sobject_row['salesforce_id']
            sobject_api_name = sobject_row['api_name']

            # Get detailed object description with fields
            try:
                obj_desc = getattr(self.sf, sobject_api_name).describe()
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Could not describe {sobject_api_name}: {e}")
                continue

            fields = obj_desc.get('fields', [])

            for field in fields:
                field_count = self._sync_field(sobject_id, sobject_salesforce_id, sobject_api_name, field, field_durable_ids)
                total_fields += field_count

        self.conn.commit()
        return total_fields

    def _get_field_durable_ids(self) -> Dict[str, str]:
        """Query FieldDefinition to get DurableIds for all fields.

        Returns:
            Dictionary mapping QualifiedApiName (Object.Field) to DurableId
        """
        durable_ids = {}

        try:
            # Get all EntityDefinition DurableIds first
            entity_durable_ids = self._get_entity_durable_ids()

            if not entity_durable_ids:
                console.print("[yellow]⚠[/yellow] No EntityDefinition IDs available for field query")
                return durable_ids

            # Query FieldDefinition for each entity
            # Salesforce requires filtering by EntityDefinitionId or DurableId
            for entity_name, entity_durable_id in entity_durable_ids.items():
                try:
                    query = f"SELECT QualifiedApiName, DurableId, EntityDefinitionId FROM FieldDefinition WHERE EntityDefinitionId = '{entity_durable_id}'"
                    result = self.sf.query_all(query)

                    for record in result.get('records', []):
                        qualified_name = record.get('QualifiedApiName')
                        durable_id = record.get('DurableId')
                        if qualified_name and durable_id:
                            durable_ids[qualified_name] = durable_id
                except Exception as entity_error:
                    # Skip entities that fail (some might not have queryable fields)
                    pass

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not query FieldDefinition: {e}")
            console.print("[yellow]⚠[/yellow] Falling back to using qualified names as identifiers")

        return durable_ids

    def _sync_field(self, sobject_id: int, sobject_salesforce_id: str, sobject_api_name: str,
                    field_data: Dict, field_durable_ids: Dict[str, str]) -> int:
        """Sync a single field.

        Args:
            sobject_id: Database ID of the parent sobject (legacy, for backwards compatibility)
            sobject_salesforce_id: Salesforce DurableId of the parent sobject
            sobject_api_name: API name of the parent sobject
            field_data: Field metadata from Salesforce
            field_durable_ids: Dictionary of field qualified names to DurableIds

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

        # Get Salesforce DurableId for this field
        qualified_name = f"{sobject_api_name}.{api_name}"
        salesforce_id = field_durable_ids.get(qualified_name, qualified_name)  # Fallback to qualified name

        # Use UPSERT based on org_id and salesforce_id
        cursor.execute("""
            INSERT INTO fields
            (salesforce_id, org_id, sobject_salesforce_id, sobject_id, api_name, label, type, length, is_custom,
             is_required, is_unique, reference_to, relationship_name, formula,
             default_value, help_text, metadata, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id, salesforce_id) DO UPDATE SET
                sobject_salesforce_id = excluded.sobject_salesforce_id,
                sobject_id = excluded.sobject_id,
                api_name = excluded.api_name,
                label = excluded.label,
                type = excluded.type,
                length = excluded.length,
                is_custom = excluded.is_custom,
                is_required = excluded.is_required,
                is_unique = excluded.is_unique,
                reference_to = excluded.reference_to,
                relationship_name = excluded.relationship_name,
                formula = excluded.formula,
                default_value = excluded.default_value,
                help_text = excluded.help_text,
                metadata = excluded.metadata,
                synced_at = excluded.synced_at
        """, (
            salesforce_id, self.org_id, sobject_salesforce_id, sobject_id, api_name, label, field_type, length,
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

    # ===== Phase 3: Enhanced Sync Methods =====

    def sync_flows_with_dependencies(self) -> int:
        """Sync Flow metadata and extract field dependencies.

        Returns:
            Number of flows synced
        """
        cursor = self.conn.cursor()
        synced_count = 0

        try:
            # Query for Flow definitions using Tooling API
            # Note: ProcessType is not available on FlowDefinition, it comes from Flow metadata
            query = """
                SELECT Id, DeveloperName, MasterLabel, ActiveVersionId, LatestVersionId, Description
                FROM FlowDefinition
                WHERE IsActive = true
            """
            result = self.sf.toolingexecute(f"query/?q={query}")
            flow_definitions = result.get('records', [])

            for flow_def in flow_definitions:
                # Get the active version's metadata
                if flow_def.get('ActiveVersionId'):
                    flow_version = self._get_flow_version(flow_def['ActiveVersionId'])
                    if flow_version:
                        # Parse the flow and extract dependencies
                        self._process_flow_version(flow_def, flow_version)
                        synced_count += 1

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error syncing flows: {e}")

        self.conn.commit()
        return synced_count

    def _get_flow_version(self, version_id: str) -> Optional[Dict]:
        """Get Flow version details including XML metadata.

        Args:
            version_id: Flow version ID

        Returns:
            Flow version record with metadata
        """
        try:
            query = f"""
                SELECT Id, Definition.DeveloperName, VersionNumber, Status, Metadata
                FROM Flow
                WHERE Id = '{version_id}'
            """
            result = self.sf.toolingexecute(f"query/?q={query}")
            records = result.get('records', [])
            return records[0] if records else None
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error getting flow version {version_id}: {e}")
            return None

    def _process_flow_version(self, flow_def: Dict, flow_version: Dict):
        """Process a flow version and extract dependencies.

        Args:
            flow_def: Flow definition record
            flow_version: Flow version record with XML
        """
        cursor = self.conn.cursor()

        flow_id = flow_version['Id']
        flow_api_name = flow_def['DeveloperName']
        version_number = flow_version.get('VersionNumber', 1)

        # Parse Flow XML if available
        metadata_xml = flow_version.get('Metadata')
        if not metadata_xml:
            return

        # Parse the Flow XML
        parsed = self.flow_parser.parse_flow_xml(metadata_xml)

        if 'error' in parsed:
            console.print(f"[yellow]⚠[/yellow] Error parsing flow {flow_api_name}: {parsed['error']}")
            return

        metadata = parsed['metadata']
        field_refs = parsed['field_references']
        element_counts = parsed['element_counts']

        # Insert flow metadata
        cursor.execute("""
            INSERT OR REPLACE INTO sf_flow_metadata
            (flow_id, flow_api_name, flow_label, process_type, trigger_type, trigger_object,
             is_active, version_number, status, element_count, decision_count,
             has_record_lookups, has_record_updates, has_record_creates, has_record_deletes,
             synced_at, xml_parsed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flow_id, flow_api_name, flow_def.get('MasterLabel'), metadata.get('process_type'),
            metadata.get('trigger_type'), metadata.get('trigger_object'),
            metadata.get('is_active', False), version_number, metadata.get('status'),
            element_counts.get('total_elements', 0), element_counts.get('decisions', 0),
            element_counts.get('record_lookups', 0) > 0,
            element_counts.get('record_updates', 0) > 0,
            element_counts.get('record_creates', 0) > 0,
            element_counts.get('record_deletes', 0) > 0,
            datetime.now().isoformat(), datetime.now().isoformat()
        ))

        # Insert field references
        for ref in field_refs:
            # Insert into detailed flow references table
            cursor.execute("""
                INSERT OR REPLACE INTO sf_flow_field_references
                (flow_id, flow_api_name, flow_version, object_name, field_name,
                 element_name, element_type, is_input, is_output, variable_name,
                 extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                flow_id, flow_api_name, version_number, ref.object_name, ref.field_name,
                ref.element_name, ref.element_type, ref.is_input, ref.is_output,
                ref.variable_name, datetime.now().isoformat()
            ))

            # Insert into central dependencies table
            reference_type = 'read' if ref.is_input else 'write' if ref.is_output else 'reference'
            cursor.execute("""
                INSERT OR REPLACE INTO sf_field_dependencies
                (connection_alias, object_name, field_name, dependent_type, dependent_id,
                 dependent_name, reference_type, created_at, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.connection_alias, ref.object_name, ref.field_name, 'flow',
                flow_id, flow_api_name, reference_type,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))

    def sync_trigger_metadata(self) -> int:
        """Sync Apex trigger inventory metadata.

        Returns:
            Number of triggers synced
        """
        cursor = self.conn.cursor()
        synced_count = 0

        try:
            # Query for active Apex triggers using Tooling API
            query = """
                SELECT Id, Name, TableEnumOrId, Status, ApiVersion, CreatedDate, LastModifiedDate, Body
                FROM ApexTrigger
                WHERE Status = 'Active'
            """
            result = self.sf.toolingexecute(f"query/?q={query}")
            triggers = result.get('records', [])

            for trigger in triggers:
                # Parse trigger events from the body (basic extraction)
                trigger_events = self._parse_trigger_events(trigger.get('Body', ''))

                # Insert trigger metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO sf_trigger_metadata
                    (trigger_id, trigger_name, object_name, is_before_insert, is_before_update,
                     is_before_delete, is_after_insert, is_after_update, is_after_delete,
                     is_after_undelete, is_active, created_date, last_modified_date, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trigger['Id'], trigger['Name'], trigger['TableEnumOrId'],
                    trigger_events.get('before insert', False),
                    trigger_events.get('before update', False),
                    trigger_events.get('before delete', False),
                    trigger_events.get('after insert', False),
                    trigger_events.get('after update', False),
                    trigger_events.get('after delete', False),
                    trigger_events.get('after undelete', False),
                    trigger['Status'] == 'Active',
                    trigger.get('CreatedDate'), trigger.get('LastModifiedDate'),
                    datetime.now().isoformat()
                ))

                synced_count += 1

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error syncing triggers: {e}")

        self.conn.commit()
        return synced_count

    def _parse_trigger_events(self, trigger_body: str) -> Dict[str, bool]:
        """Parse trigger events from trigger body.

        Args:
            trigger_body: Apex trigger code

        Returns:
            Dictionary of trigger events (e.g., {'before insert': True})
        """
        events = {}
        trigger_body_lower = trigger_body.lower()

        # Look for trigger event patterns
        event_patterns = [
            'before insert', 'before update', 'before delete',
            'after insert', 'after update', 'after delete', 'after undelete'
        ]

        for pattern in event_patterns:
            events[pattern] = pattern in trigger_body_lower

        return events

    def sync_field_relationships(self) -> int:
        """Extract and store field relationships from existing field metadata.

        Returns:
            Number of relationships extracted
        """
        cursor = self.conn.cursor()
        relationship_count = 0

        # Get all fields with reference_to (lookup/master-detail)
        cursor.execute("""
            SELECT f.api_name as field_name, f.reference_to, f.relationship_name,
                   f.type, f.metadata, s.api_name as object_name
            FROM fields f
            JOIN sobjects s ON f.sobject_salesforce_id = s.salesforce_id
            WHERE f.org_id = ? AND f.reference_to IS NOT NULL
        """, (self.org_id,))

        fields = cursor.fetchall()

        for field in fields:
            # Parse reference_to (can be comma-separated for polymorphic lookups)
            target_objects = field['reference_to'].split(',')

            for target_object in target_objects:
                target_object = target_object.strip()

                # Determine relationship type
                field_type = field['type']
                metadata_str = field['metadata'] if field['metadata'] else '{}'
                metadata = json.loads(metadata_str)

                is_master_detail = (field_type == 'MasterDetail')
                is_lookup = (field_type == 'Lookup')
                is_external = metadata.get('externalId', False)

                if is_master_detail:
                    rel_type = 'master_detail'
                elif is_external:
                    rel_type = 'external_lookup'
                else:
                    rel_type = 'lookup'

                # Extract cascade delete info
                is_cascade_delete = metadata.get('cascadeDelete', False)
                is_reparentable = metadata.get('reparentableMasterDetail', False)

                # Insert field relationship
                cursor.execute("""
                    INSERT OR REPLACE INTO sf_field_relationships
                    (connection_alias, source_object, source_field, relationship_type,
                     target_object, relationship_name, is_cascade_delete, is_reparentable,
                     created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.connection_alias, field['object_name'], field['field_name'],
                    rel_type, target_object, field['relationship_name'],
                    is_cascade_delete, is_reparentable,
                    datetime.now().isoformat()
                ))

                # Insert object-level relationship
                cursor.execute("""
                    INSERT OR REPLACE INTO sf_object_relationships
                    (connection_alias, parent_object, child_object, relationship_field,
                     relationship_type, relationship_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.connection_alias, target_object, field['object_name'],
                    field['field_name'], rel_type, field['relationship_name']
                ))

                relationship_count += 1

        self.conn.commit()
        return relationship_count
