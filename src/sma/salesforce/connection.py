"""Salesforce connection management."""

from typing import Optional, Dict, Any
from simple_salesforce import Salesforce
from .auth import SalesforceAuth
from ..database import Database
import requests


class SalesforceConnection:
    """Manage Salesforce connections and credentials."""

    def __init__(self, database: Database):
        """Initialize connection manager.

        Args:
            database: Database instance for storing org metadata
        """
        self.db = database

    def connect(
        self,
        org_alias: str,
        client_id: str,
        client_secret: str,
        instance_url: str = "https://login.salesforce.com",
        sandbox: bool = False
    ) -> Dict[str, Any]:
        """Connect to Salesforce using OAuth.

        Args:
            org_alias: User-friendly name for this org
            client_id: Connected App Client ID
            client_secret: Connected App Client Secret
            instance_url: Login URL (override for custom domains)
            sandbox: If True, use test.salesforce.com

        Returns:
            Connection result with org info

        Raises:
            Exception: If authentication fails
        """
        # Use sandbox URL if specified
        if sandbox and instance_url == "https://login.salesforce.com":
            instance_url = "https://test.salesforce.com"

        # Initialize auth
        auth = SalesforceAuth(client_id, client_secret, instance_url)

        # Perform OAuth flow
        token_response = auth.authenticate()

        # Save credentials
        auth.save_credentials(org_alias, token_response)

        # Extract org info from token response
        org_id = self._extract_org_id(token_response['id'])
        org_instance_url = token_response['instance_url']

        # Get org details from Salesforce
        org_info = self._get_org_info(token_response['access_token'], org_instance_url)

        # Determine org type
        org_type = "Sandbox" if org_info.get('IsSandbox') else "Production"

        # Store in database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO salesforce_orgs
            (org_id, instance_url, org_name, org_type, is_active, last_sync)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (org_id, org_instance_url, org_alias, org_type, 1))

        # Deactivate other orgs
        cursor.execute("""
            UPDATE salesforce_orgs
            SET is_active = 0
            WHERE org_id != ?
        """, (org_id,))

        self.db.conn.commit()

        return {
            'org_id': org_id,
            'org_alias': org_alias,
            'instance_url': org_instance_url,
            'org_type': org_type,
            'org_name': org_info.get('Name', org_alias)
        }

    def get_client(self, org_alias: Optional[str] = None) -> Salesforce:
        """Get authenticated Salesforce client.

        Args:
            org_alias: Org to connect to. If None, uses active org.

        Returns:
            Authenticated Salesforce client

        Raises:
            Exception: If no credentials found or authentication fails
        """
        # Get org from database
        if org_alias is None:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT org_id, instance_url, org_name
                FROM salesforce_orgs
                WHERE is_active = 1
                LIMIT 1
            """)
            row = cursor.fetchone()

            if not row:
                raise Exception("No active Salesforce org. Run 'sma sf connect' first.")

            org_alias = row['org_name']
            instance_url = row['instance_url']
        else:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT instance_url
                FROM salesforce_orgs
                WHERE org_name = ?
            """, (org_alias,))
            row = cursor.fetchone()

            if not row:
                raise Exception(f"Org '{org_alias}' not found. Run 'sma sf connect' first.")

            instance_url = row['instance_url']

        # Load credentials from keyring
        auth = SalesforceAuth("dummy", "dummy")  # Client ID/Secret not needed for refresh
        credentials = auth.load_credentials(org_alias)

        if not credentials:
            raise Exception(f"No credentials found for '{org_alias}'. Run 'sma sf connect' first.")

        # Create Salesforce client
        try:
            sf = Salesforce(
                instance_url=instance_url,
                session_id=credentials['access_token']
            )
            return sf
        except Exception as e:
            # Try to refresh token if access token expired
            if credentials.get('refresh_token'):
                # Need to get client_id and client_secret from user config
                # For now, raise error and ask user to reconnect
                raise Exception(
                    f"Access token expired for '{org_alias}'. "
                    f"Please reconnect using 'sma sf connect'."
                ) from e
            raise

    def disconnect(self, org_alias: Optional[str] = None) -> None:
        """Disconnect from Salesforce org.

        Args:
            org_alias: Org to disconnect. If None, disconnects active org.
        """
        if org_alias is None:
            # Get active org
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT org_name
                FROM salesforce_orgs
                WHERE is_active = 1
                LIMIT 1
            """)
            row = cursor.fetchone()

            if not row:
                raise Exception("No active Salesforce org.")

            org_alias = row['org_name']

        # Delete credentials from keyring
        auth = SalesforceAuth("dummy", "dummy")
        auth.delete_credentials(org_alias)

        # Remove from database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            DELETE FROM salesforce_orgs
            WHERE org_name = ?
        """, (org_alias,))
        self.db.conn.commit()

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current connection status.

        Returns:
            Status dict with org info, or None if not connected
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT org_id, instance_url, org_name, org_type, last_sync
            FROM salesforce_orgs
            WHERE is_active = 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            return None

        return {
            'org_id': row['org_id'],
            'org_name': row['org_name'],
            'org_type': row['org_type'],
            'instance_url': row['instance_url'],
            'last_sync': row['last_sync']
        }

    def list_orgs(self) -> list:
        """List all connected orgs.

        Returns:
            List of org info dicts
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT org_id, org_name, org_type, instance_url, is_active, last_sync
            FROM salesforce_orgs
            ORDER BY is_active DESC, org_name ASC
        """)

        orgs = []
        for row in cursor.fetchall():
            orgs.append({
                'org_id': row['org_id'],
                'org_name': row['org_name'],
                'org_type': row['org_type'],
                'instance_url': row['instance_url'],
                'is_active': bool(row['is_active']),
                'last_sync': row['last_sync']
            })

        return orgs

    def switch_org(self, org_alias: str) -> None:
        """Switch active org.

        Args:
            org_alias: Org to make active
        """
        cursor = self.db.conn.cursor()

        # Check if org exists
        cursor.execute("""
            SELECT org_id
            FROM salesforce_orgs
            WHERE org_name = ?
        """, (org_alias,))

        if not cursor.fetchone():
            raise Exception(f"Org '{org_alias}' not found.")

        # Deactivate all orgs
        cursor.execute("UPDATE salesforce_orgs SET is_active = 0")

        # Activate specified org
        cursor.execute("""
            UPDATE salesforce_orgs
            SET is_active = 1
            WHERE org_name = ?
        """, (org_alias,))

        self.db.conn.commit()

    def _extract_org_id(self, identity_url: str) -> str:
        """Extract org ID from identity URL.

        Args:
            identity_url: Identity URL from token response

        Returns:
            18-character org ID
        """
        # Identity URL format: https://login.salesforce.com/id/{orgId}/{userId}
        parts = identity_url.split('/')
        return parts[-2] if len(parts) >= 2 else "unknown"

    def _get_org_info(self, access_token: str, instance_url: str) -> Dict[str, Any]:
        """Get organization information from Salesforce.

        Args:
            access_token: Access token
            instance_url: Instance URL

        Returns:
            Organization information
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Query Organization object
        query = "SELECT Id, Name, IsSandbox, InstanceName FROM Organization LIMIT 1"
        url = f"{instance_url}/services/data/v59.0/query"

        try:
            response = requests.get(url, headers=headers, params={'q': query})
            response.raise_for_status()
            data = response.json()

            if data.get('records'):
                return data['records'][0]
        except Exception:
            pass

        return {}
