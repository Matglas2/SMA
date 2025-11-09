"""Flow XML parser for extracting field references and dependencies."""

import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FieldReference:
    """Represents a field reference found in a Flow."""

    object_name: str
    field_name: str
    element_name: str
    element_type: str
    is_input: bool = False
    is_output: bool = False
    variable_name: Optional[str] = None
    xpath_location: Optional[str] = None


class FlowParser:
    """Parser for Salesforce Flow XML to extract metadata and field references."""

    # Flow namespace
    FLOW_NS = '{http://soap.sforce.com/2006/04/metadata}'

    # Element types that can contain field references
    RECORD_ELEMENT_TYPES = {
        'recordLookups': 'recordLookup',
        'recordCreates': 'recordCreate',
        'recordUpdates': 'recordUpdate',
        'recordDeletes': 'recordDelete',
    }

    def __init__(self):
        """Initialize Flow parser."""
        self.field_pattern = re.compile(r'^([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)$')

    def parse_flow_xml(self, xml_content: str) -> Dict:
        """Parse Flow XML and extract comprehensive metadata.

        Args:
            xml_content: Raw Flow XML content

        Returns:
            Dictionary containing:
            - metadata: Flow-level metadata
            - field_references: List of FieldReference objects
            - element_counts: Counts of different element types
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return {
                'error': f'XML parsing error: {str(e)}',
                'metadata': {},
                'field_references': [],
                'element_counts': {}
            }

        metadata = self._extract_flow_metadata(root)
        field_references = self._extract_field_references(root)
        element_counts = self._count_elements(root)

        return {
            'metadata': metadata,
            'field_references': field_references,
            'element_counts': element_counts
        }

    def _extract_flow_metadata(self, root: ET.Element) -> Dict:
        """Extract high-level Flow metadata.

        Args:
            root: XML root element

        Returns:
            Dictionary of Flow metadata
        """
        metadata = {}

        # Process type
        process_type_elem = root.find(f'{self.FLOW_NS}processType')
        if process_type_elem is not None:
            metadata['process_type'] = process_type_elem.text

        # Start element reference (entry point)
        start_elem = root.find(f'{self.FLOW_NS}start')
        if start_elem is not None:
            # Check for trigger type
            trigger_type = start_elem.find(f'{self.FLOW_NS}triggerType')
            if trigger_type is not None:
                metadata['trigger_type'] = trigger_type.text

            # Check for trigger object
            object_elem = start_elem.find(f'{self.FLOW_NS}object')
            if object_elem is not None:
                metadata['trigger_object'] = object_elem.text

        # Status
        status_elem = root.find(f'{self.FLOW_NS}status')
        if status_elem is not None:
            metadata['status'] = status_elem.text
            metadata['is_active'] = (status_elem.text == 'Active')

        # Description
        desc_elem = root.find(f'{self.FLOW_NS}description')
        if desc_elem is not None:
            metadata['description'] = desc_elem.text

        return metadata

    def _extract_field_references(self, root: ET.Element) -> List[FieldReference]:
        """Extract all field references from Flow XML.

        Args:
            root: XML root element

        Returns:
            List of FieldReference objects
        """
        field_refs = []

        # Extract from record operations
        for element_tag, element_type in self.RECORD_ELEMENT_TYPES.items():
            for elem in root.findall(f'{self.FLOW_NS}{element_tag}'):
                refs = self._parse_record_element(elem, element_type)
                field_refs.extend(refs)

        # Extract from assignments
        for assignment in root.findall(f'{self.FLOW_NS}assignments'):
            refs = self._parse_assignment(assignment)
            field_refs.extend(refs)

        # Extract from decisions (filters)
        for decision in root.findall(f'{self.FLOW_NS}decisions'):
            refs = self._parse_decision(decision)
            field_refs.extend(refs)

        return field_refs

    def _parse_record_element(self, element: ET.Element, element_type: str) -> List[FieldReference]:
        """Parse a record operation element (lookup, create, update, delete).

        Args:
            element: XML element for record operation
            element_type: Type of operation (recordLookup, recordCreate, etc.)

        Returns:
            List of FieldReference objects
        """
        refs = []

        # Get element name
        name_elem = element.find(f'{self.FLOW_NS}name')
        element_name = name_elem.text if name_elem is not None else 'Unknown'

        # Get object
        object_elem = element.find(f'{self.FLOW_NS}object')
        if object_elem is None:
            return refs
        object_name = object_elem.text

        # Parse filters (for lookups and updates)
        for filter_elem in element.findall(f'{self.FLOW_NS}filters'):
            field_elem = filter_elem.find(f'{self.FLOW_NS}field')
            if field_elem is not None and field_elem.text:
                field_name = field_elem.text
                refs.append(FieldReference(
                    object_name=object_name,
                    field_name=field_name,
                    element_name=element_name,
                    element_type=element_type,
                    is_input=True,
                    is_output=False
                ))

        # Parse input assignments (for creates and updates)
        for input_assign in element.findall(f'{self.FLOW_NS}inputAssignments'):
            field_elem = input_assign.find(f'{self.FLOW_NS}field')
            if field_elem is not None and field_elem.text:
                field_name = field_elem.text
                refs.append(FieldReference(
                    object_name=object_name,
                    field_name=field_name,
                    element_name=element_name,
                    element_type=element_type,
                    is_input=False,
                    is_output=True
                ))

        # Parse output assignments (for lookups)
        for output_assign in element.findall(f'{self.FLOW_NS}outputAssignments'):
            assignee_ref = output_assign.find(f'{self.FLOW_NS}assignToReference')
            field_elem = output_assign.find(f'{self.FLOW_NS}field')

            if field_elem is not None and field_elem.text:
                field_name = field_elem.text
                var_name = assignee_ref.text if assignee_ref is not None else None

                refs.append(FieldReference(
                    object_name=object_name,
                    field_name=field_name,
                    element_name=element_name,
                    element_type=element_type,
                    is_input=True,
                    is_output=False,
                    variable_name=var_name
                ))

        return refs

    def _parse_assignment(self, element: ET.Element) -> List[FieldReference]:
        """Parse an assignment element for field references.

        Args:
            element: XML assignment element

        Returns:
            List of FieldReference objects
        """
        refs = []

        name_elem = element.find(f'{self.FLOW_NS}name')
        element_name = name_elem.text if name_elem is not None else 'Unknown'

        for assign_to in element.findall(f'{self.FLOW_NS}assignmentItems'):
            # Check if assignToReference contains object.field pattern
            assign_ref = assign_to.find(f'{self.FLOW_NS}assignToReference')
            if assign_ref is not None and assign_ref.text:
                match = self.field_pattern.match(assign_ref.text)
                if match:
                    object_name, field_name = match.groups()
                    refs.append(FieldReference(
                        object_name=object_name,
                        field_name=field_name,
                        element_name=element_name,
                        element_type='assignment',
                        is_input=False,
                        is_output=True
                    ))

            # Check value references
            value_elem = assign_to.find(f'{self.FLOW_NS}value')
            if value_elem is not None:
                for elem_ref in value_elem.findall(f'{self.FLOW_NS}elementReference'):
                    if elem_ref.text:
                        match = self.field_pattern.match(elem_ref.text)
                        if match:
                            object_name, field_name = match.groups()
                            refs.append(FieldReference(
                                object_name=object_name,
                                field_name=field_name,
                                element_name=element_name,
                                element_type='assignment',
                                is_input=True,
                                is_output=False
                            ))

        return refs

    def _parse_decision(self, element: ET.Element) -> List[FieldReference]:
        """Parse a decision element for field references in conditions.

        Args:
            element: XML decision element

        Returns:
            List of FieldReference objects
        """
        refs = []

        name_elem = element.find(f'{self.FLOW_NS}name')
        element_name = name_elem.text if name_elem is not None else 'Unknown'

        # Parse rules and conditions
        for rule in element.findall(f'{self.FLOW_NS}rules'):
            for condition in rule.findall(f'{self.FLOW_NS}conditions'):
                left_value = condition.find(f'{self.FLOW_NS}leftValueReference')
                if left_value is not None and left_value.text:
                    match = self.field_pattern.match(left_value.text)
                    if match:
                        object_name, field_name = match.groups()
                        refs.append(FieldReference(
                            object_name=object_name,
                            field_name=field_name,
                            element_name=element_name,
                            element_type='decision',
                            is_input=True,
                            is_output=False
                        ))

                right_value = condition.find(f'{self.FLOW_NS}rightValue')
                if right_value is not None:
                    for elem_ref in right_value.findall(f'{self.FLOW_NS}elementReference'):
                        if elem_ref.text:
                            match = self.field_pattern.match(elem_ref.text)
                            if match:
                                object_name, field_name = match.groups()
                                refs.append(FieldReference(
                                    object_name=object_name,
                                    field_name=field_name,
                                    element_name=element_name,
                                    element_type='decision',
                                    is_input=True,
                                    is_output=False
                                ))

        return refs

    def _count_elements(self, root: ET.Element) -> Dict[str, int]:
        """Count different types of elements in the Flow.

        Args:
            root: XML root element

        Returns:
            Dictionary of element type counts
        """
        counts = {
            'total_elements': 0,
            'record_lookups': 0,
            'record_creates': 0,
            'record_updates': 0,
            'record_deletes': 0,
            'decisions': 0,
            'assignments': 0,
            'loops': 0,
            'screens': 0,
            'subflows': 0
        }

        for element_tag in self.RECORD_ELEMENT_TYPES.keys():
            count = len(root.findall(f'{self.FLOW_NS}{element_tag}'))
            counts[element_tag.replace('s', '')] = count
            counts['total_elements'] += count

        for element_type in ['decisions', 'assignments', 'loops', 'screens', 'subflows']:
            count = len(root.findall(f'{self.FLOW_NS}{element_type}'))
            counts[element_type] = count
            counts['total_elements'] += count

        return counts
