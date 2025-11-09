"""OAuth authentication for Salesforce."""

import webbrowser
import keyring
import json
import base64
import hashlib
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional, Dict, Any
import requests
from threading import Thread
import time


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    authorization_code: Optional[str] = None

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        # Parse the authorization code from callback URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'code' in params:
            OAuthCallbackHandler.authorization_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Success page
            html = """
            <html>
            <head><title>SMA - Authentication Successful</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Error page
            html = """
            <html>
            <head><title>SMA - Authentication Failed</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">✗ Authentication Failed</h1>
                <p>No authorization code received. Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class SalesforceAuth:
    """Manage Salesforce OAuth authentication."""

    KEYRING_SERVICE = "SMA_Salesforce"
    CALLBACK_PORT = 8765
    CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/oauth/callback"

    def __init__(self, client_id: str, client_secret: str, instance_url: str = "https://login.salesforce.com"):
        """Initialize Salesforce authentication.

        Args:
            client_id: Salesforce Connected App Client ID
            client_secret: Salesforce Connected App Client Secret
            instance_url: Salesforce login URL (login.salesforce.com or test.salesforce.com)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.instance_url = instance_url
        self.code_verifier: Optional[str] = None

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and code challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters, base64url encoded)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')  # Remove padding

        # Generate code challenge (SHA256 hash of verifier, base64url encoded)
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')  # Remove padding

        return code_verifier, code_challenge

    def get_authorization_url(self) -> str:
        """Generate OAuth authorization URL with PKCE.

        Returns:
            Authorization URL to open in browser
        """
        # Generate PKCE parameters
        self.code_verifier, code_challenge = self._generate_pkce_pair()

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.CALLBACK_URL,
            'scope': 'api full refresh_token',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        param_string = urlencode(params)
        return f"{self.instance_url}/services/oauth2/authorize?{param_string}"

    def start_callback_server(self, timeout: int = 300) -> Optional[str]:
        """Start local HTTP server to receive OAuth callback.

        Args:
            timeout: Seconds to wait for callback (default 300 = 5 minutes)

        Returns:
            Authorization code if received, None otherwise
        """
        OAuthCallbackHandler.authorization_code = None
        server = HTTPServer(('localhost', self.CALLBACK_PORT), OAuthCallbackHandler)

        # Run server in separate thread
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Wait for authorization code or timeout
        start_time = time.time()
        while OAuthCallbackHandler.authorization_code is None:
            if time.time() - start_time > timeout:
                server.shutdown()
                return None
            time.sleep(0.5)

        server.shutdown()
        return OAuthCallbackHandler.authorization_code

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token using PKCE.

        Args:
            authorization_code: Code received from OAuth callback

        Returns:
            Token response containing access_token, refresh_token, instance_url, etc.

        Raises:
            requests.HTTPError: If token exchange fails
        """
        token_url = f"{self.instance_url}/services/oauth2/token"

        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.CALLBACK_URL,
            'code_verifier': self.code_verifier  # PKCE code verifier
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from initial authentication

        Returns:
            New token response with fresh access_token

        Raises:
            requests.HTTPError: If token refresh fails
        """
        token_url = f"{self.instance_url}/services/oauth2/token"

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        return response.json()

    def authenticate(self) -> Dict[str, Any]:
        """Perform full OAuth authentication flow.

        Returns:
            Token response with credentials

        Raises:
            Exception: If authentication fails
        """
        # Generate and open authorization URL
        auth_url = self.get_authorization_url()

        print(f"\nOpening browser for Salesforce authentication...")
        print(f"If browser doesn't open automatically, visit:\n{auth_url}\n")

        webbrowser.open(auth_url)

        # Start callback server and wait for code
        print("Waiting for authorization callback...")
        authorization_code = self.start_callback_server()

        if not authorization_code:
            raise Exception("Authentication timeout. No authorization code received.")

        # Exchange code for tokens
        print("Exchanging authorization code for access token...")
        token_response = self.exchange_code_for_token(authorization_code)

        return token_response

    def save_credentials(self, org_alias: str, token_response: Dict[str, Any]) -> None:
        """Save credentials securely to system keyring.

        Args:
            org_alias: User-friendly name for this org (e.g., "production", "sandbox")
            token_response: Token response from authentication
        """
        credentials = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response.get('refresh_token'),
            'instance_url': token_response['instance_url'],
            'id': token_response['id'],
            'issued_at': token_response['issued_at']
        }

        keyring.set_password(
            self.KEYRING_SERVICE,
            org_alias,
            json.dumps(credentials)
        )

    def load_credentials(self, org_alias: str) -> Optional[Dict[str, Any]]:
        """Load credentials from system keyring.

        Args:
            org_alias: Org alias to load

        Returns:
            Credentials dict if found, None otherwise
        """
        creds_json = keyring.get_password(self.KEYRING_SERVICE, org_alias)

        if creds_json:
            return json.loads(creds_json)
        return None

    def delete_credentials(self, org_alias: str) -> None:
        """Delete credentials from system keyring.

        Args:
            org_alias: Org alias to delete
        """
        try:
            keyring.delete_password(self.KEYRING_SERVICE, org_alias)
        except keyring.errors.PasswordDeleteError:
            pass  # Already deleted or doesn't exist

    @staticmethod
    def list_saved_orgs() -> list:
        """List all saved org aliases.

        Note: This is a simplified implementation. Keyring doesn't provide
        a native way to list all stored keys, so we'll track orgs in the database.

        Returns:
            List of org aliases
        """
        # This will be implemented in the connection manager
        # which has access to the database
        return []
