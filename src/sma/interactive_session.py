"""Interactive Simple Salesforce session."""

import sys
from typing import Optional
from simple_salesforce import Salesforce
from rich.console import Console

console = Console()


def start_interactive_session(sf_client: Salesforce, org_name: str) -> None:
    """Start an interactive Simple Salesforce session.

    Args:
        sf_client: Authenticated Salesforce client
        org_name: Name of the connected org
    """
    # Print welcome message
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold green]Simple Salesforce Interactive Session[/bold green]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")

    console.print(f"Connected to: [yellow]{org_name}[/yellow]")
    console.print(f"Instance URL: [yellow]{sf_client.sf_instance}[/yellow]\n")

    console.print("[bold]Available objects:[/bold]")
    console.print("  [cyan]sf[/cyan]          - Authenticated Salesforce client")
    console.print("  [cyan]query[/cyan]       - Execute SOQL query: query('SELECT Id FROM Account LIMIT 10')")
    console.print("  [cyan]describe[/cyan]    - Describe an object: describe('Account')")
    console.print("  [cyan]get_record[/cyan] - Get a record: get_record('Account', record_id)")
    console.print("  [cyan]search[/cyan]      - Execute SOSL search: search('FIND {John} IN ALL FIELDS')")
    console.print("\n[bold]Examples:[/bold]")
    console.print("  [dim]# Query records[/dim]")
    console.print("  [green]>>> query('SELECT Id, Name FROM Account LIMIT 5')[/green]")
    console.print("\n  [dim]# Describe object[/dim]")
    console.print("  [green]>>> describe('Contact')[/green]")
    console.print("\n  [dim]# Access SObject directly[/dim]")
    console.print("  [green]>>> sf.Account.create({'Name': 'Test Account'})[/green]")
    console.print("\n  [dim]# Get metadata[/dim]")
    console.print("  [green]>>> sf.Account.describe()[/green]")
    console.print("\n[dim]Type 'exit()' or Ctrl+D to quit[/dim]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")

    # Helper functions to make session easier
    def query(soql: str):
        """Execute SOQL query and return results.

        Args:
            soql: SOQL query string

        Returns:
            Query results
        """
        try:
            result = sf_client.query(soql)
            console.print(f"\n[green]✓ Query successful[/green] - {result['totalSize']} record(s) found\n")
            return result
        except Exception as e:
            console.print(f"\n[bold red]✗ Query failed:[/bold red] {str(e)}\n")
            return None

    def describe(sobject_name: str):
        """Describe a Salesforce object.

        Args:
            sobject_name: API name of the object (e.g., 'Account', 'Contact')

        Returns:
            Object metadata
        """
        try:
            sobject = getattr(sf_client, sobject_name)
            result = sobject.describe()
            console.print(f"\n[green]✓ Object: {result['label']}[/green]")
            console.print(f"  API Name: [cyan]{result['name']}[/cyan]")
            console.print(f"  Fields: [cyan]{len(result['fields'])}[/cyan]")
            console.print(f"  Createable: [cyan]{result['createable']}[/cyan]")
            console.print(f"  Updateable: [cyan]{result['updateable']}[/cyan]")
            console.print(f"  Deletable: [cyan]{result['deletable']}[/cyan]\n")
            return result
        except Exception as e:
            console.print(f"\n[bold red]✗ Describe failed:[/bold red] {str(e)}\n")
            return None

    def get_record(sobject_name: str, record_id: str):
        """Get a specific record by ID.

        Args:
            sobject_name: API name of the object
            record_id: Salesforce record ID

        Returns:
            Record data
        """
        try:
            sobject = getattr(sf_client, sobject_name)
            result = sobject.get(record_id)
            console.print(f"\n[green]✓ Record retrieved successfully[/green]\n")
            return result
        except Exception as e:
            console.print(f"\n[bold red]✗ Get record failed:[/bold red] {str(e)}\n")
            return None

    def search(sosl: str):
        """Execute SOSL search.

        Args:
            sosl: SOSL search string

        Returns:
            Search results
        """
        try:
            result = sf_client.search(sosl)
            console.print(f"\n[green]✓ Search successful[/green] - {len(result)} result(s) found\n")
            return result
        except Exception as e:
            console.print(f"\n[bold red]✗ Search failed:[/bold red] {str(e)}\n")
            return None

    # Prepare namespace for interactive session
    namespace = {
        'sf': sf_client,
        'query': query,
        'describe': describe,
        'get_record': get_record,
        'search': search,
        'console': console,
    }

    # Try to use IPython if available (better interactive experience)
    try:
        from IPython import embed
        embed(user_ns=namespace, colors='neutral')
    except ImportError:
        # Fallback to standard Python interactive console
        import code
        code.interact(local=namespace, banner='')
