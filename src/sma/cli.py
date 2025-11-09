"""CLI interface for SMA."""

import click
import random
import os
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rapidfuzz import fuzz, process
from .database import Database
from .salesforce.connection import SalesforceConnection
from .interactive_session import start_interactive_session

console = Console()


# ASCII art collection (Windows-compatible)
ASCII_ART = [
    r"""
      .   .
       \ /
    .-'   '-.
   /  o   o  \
   |    >    |
   \  \___/  /
    '-.___..-'
    """,
    r"""
       *
      ***
     *****
    *******
      ***
      ***
    """,
    r"""
    +------------------+
    |  Have a great    |
    |  day ahead!      |
    +------------------+
           ||
          //\\
         //  \\
    """,
    r"""
       ___
      /   \
     | O O |
      \___/
       |||
      /| |\
    """,
    r"""
      /\___/\
     (  o.o  )
      > ^ <
     /|     |\
    (_|     |_)
    """,
]


@click.group()
@click.version_option(version="0.1.0")
def main():
    """SMA - A SQLite-powered CLI application.

    Welcome to SMA! Use the commands below to interact with the application.
    """
    pass


@main.command()
@click.option('--name', default=None, help='Your name for a personalized greeting')
def hello(name):
    """Greet the user with a nice message, quote, and ASCII art.

    This command will:
    - Display a personalized greeting
    - Share an inspiring quote
    - Show fun ASCII art
    - Log the greeting to the database
    """
    # Get username
    if name is None:
        name = os.environ.get('USERNAME') or os.environ.get('USER') or 'Friend'

    # Get current time for contextual greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting_time = "Good morning"
    elif hour < 18:
        greeting_time = "Good afternoon"
    else:
        greeting_time = "Good evening"

    # Select random art
    art = random.choice(ASCII_ART)

    # Get random quote and log to database
    try:
        with Database() as db:
            # Get random quote from database
            quote_data = db.get_random_quote()
            if quote_data:
                quote = f"{quote_data['text']} - {quote_data['author']}"
            else:
                quote = "No quotes available."

            # Log greeting
            cursor = db.conn.cursor()
            cursor.execute("INSERT INTO greetings (username) VALUES (?)", (name,))
            db.conn.commit()

            # Get total greeting count
            cursor.execute("SELECT COUNT(*) as count FROM greetings")
            total_greetings = cursor.fetchone()['count']
    except Exception as e:
        # If database fails, don't stop the greeting
        quote = "Stay positive and keep going!"
        total_greetings = None

    # Display the greeting
    click.echo("=" * 60)
    click.echo(art)
    click.echo("=" * 60)
    click.echo()
    click.echo(click.style(f"  {greeting_time}, {name}!", fg='bright_green', bold=True))
    click.echo()
    click.echo(click.style("  Have a wonderful day!", fg='bright_yellow'))
    click.echo()
    click.echo("  " + "-" * 56)
    click.echo(click.style(f"  Quote: {quote}", fg='cyan', italic=True))
    click.echo("  " + "-" * 56)
    click.echo()

    if total_greetings:
        click.echo(click.style(f"  This is greeting #{total_greetings}! ", fg='magenta'))

    click.echo("=" * 60)


@main.command()
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
def ss(alias):
    """Start interactive Simple Salesforce session.

    Opens an interactive Python session with an authenticated Salesforce client.
    You can use the 'sf' object to interact with Salesforce using simple_salesforce.

    The session provides helper functions:
    - query(soql) - Execute SOQL queries
    - describe(object) - Describe Salesforce objects
    - get_record(object, id) - Get records by ID
    - search(sosl) - Execute SOSL searches

    You can also access the Salesforce client directly via the 'sf' variable.

    Example:
        sma ss                          # Use active org
        sma ss --alias production       # Use specific org
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Check if connected
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first.\n")
                    return
                alias = status['org_name']
            else:
                # Verify org exists
                cursor = db.conn.cursor()
                cursor.execute("SELECT org_name FROM salesforce_orgs WHERE org_name = ?", (alias,))
                result = cursor.fetchone()
                if not result:
                    console.print(f"\n[bold red]✗ Org not found:[/bold red] {alias}\n")
                    console.print("Run [cyan]sma sf list[/cyan] to see connected orgs.\n")
                    return

            # Get Salesforce client
            try:
                sf_client = conn_manager.get_client(alias)
            except Exception as e:
                console.print(f"\n[bold red]✗ Failed to connect:[/bold red] {str(e)}\n")
                console.print("Your session may have expired. Try reconnecting:\n")
                console.print(f"  [cyan]sma sf connect --alias {alias} --client-id YOUR_ID --client-secret YOUR_SECRET[/cyan]\n")
                return

            # Start interactive session
            start_interactive_session(sf_client, alias)

    except KeyboardInterrupt:
        console.print("\n\n[green]Session ended.[/green]\n")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


# Salesforce commands group
@main.group(name='sf')
def salesforce():
    """Salesforce integration commands."""
    pass


@salesforce.command(name='connect')
@click.option('--alias', required=True, help='Alias for this org (e.g., "production", "sandbox")')
@click.option('--client-id', required=True, help='Connected App Client ID')
@click.option('--client-secret', required=True, help='Connected App Client Secret')
@click.option('--sandbox', is_flag=True, help='Connect to sandbox (test.salesforce.com)')
@click.option('--instance-url', default=None, help='Custom instance URL')
def sf_connect(alias, client_id, client_secret, sandbox, instance_url):
    """Connect to Salesforce using OAuth.

    You need to create a Connected App in Salesforce first:
    1. Setup → App Manager → New Connected App
    2. Enable OAuth Settings
    3. Callback URL: http://localhost:8765/oauth/callback
    4. OAuth Scopes: Full access (full), Perform requests at any time (refresh_token)
    5. Copy Client ID and Client Secret

    Example:
        sma sf connect --alias production --client-id YOUR_ID --client-secret YOUR_SECRET
        sma sf connect --alias sandbox --client-id YOUR_ID --client-secret YOUR_SECRET --sandbox
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            console.print("\n[bold cyan]Connecting to Salesforce...[/bold cyan]\n")

            # Determine instance URL
            login_url = instance_url
            if login_url is None:
                login_url = "https://test.salesforce.com" if sandbox else "https://login.salesforce.com"

            # Connect
            result = conn_manager.connect(
                org_alias=alias,
                client_id=client_id,
                client_secret=client_secret,
                instance_url=login_url,
                sandbox=sandbox
            )

            console.print(f"\n[bold green]✓ Successfully connected to Salesforce![/bold green]\n")
            console.print(f"Org Name: [cyan]{result['org_name']}[/cyan]")
            console.print(f"Org Type: [cyan]{result['org_type']}[/cyan]")
            console.print(f"Org ID: [cyan]{result['org_id']}[/cyan]")
            console.print(f"Instance: [cyan]{result['instance_url']}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Connection failed:[/bold red] {str(e)}\n")
        raise click.Abort()


@salesforce.command(name='status')
def sf_status():
    """Show current Salesforce connection status."""
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)
            status = conn_manager.get_status()

            if status is None:
                console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                console.print("Run [cyan]sma sf connect[/cyan] to connect.\n")
                return

            console.print("\n[bold cyan]Salesforce Connection Status[/bold cyan]\n")
            console.print(f"Org Name: [green]{status['org_name']}[/green]")
            console.print(f"Org Type: [green]{status['org_type']}[/green]")
            console.print(f"Org ID: [green]{status['org_id']}[/green]")
            console.print(f"Instance: [green]{status['instance_url']}[/green]")

            if status['last_sync']:
                console.print(f"Last Sync: [green]{status['last_sync']}[/green]")
            else:
                console.print(f"Last Sync: [yellow]Never[/yellow]")

            console.print()

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@salesforce.command(name='list')
def sf_list():
    """List all connected Salesforce orgs."""
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)
            orgs = conn_manager.list_orgs()

            if not orgs:
                console.print("\n[yellow]No connected orgs.[/yellow]")
                console.print("Run [cyan]sma sf connect[/cyan] to connect.\n")
                return

            # Create table
            table = Table(title="Connected Salesforce Orgs", show_header=True, header_style="bold cyan")
            table.add_column("Active", style="green")
            table.add_column("Alias", style="cyan")
            table.add_column("Type")
            table.add_column("Org ID")
            table.add_column("Last Sync")

            for org in orgs:
                active = "●" if org['is_active'] else ""
                last_sync = org['last_sync'] if org['last_sync'] else "Never"

                table.add_row(
                    active,
                    org['org_name'],
                    org['org_type'],
                    org['org_id'],
                    last_sync
                )

            console.print()
            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@salesforce.command(name='switch')
@click.argument('alias')
def sf_switch(alias):
    """Switch active Salesforce org.

    Example:
        sma sf switch production
        sma sf switch sandbox
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)
            conn_manager.switch_org(alias)

            console.print(f"\n[bold green]✓ Switched to org:[/bold green] [cyan]{alias}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@salesforce.command(name='disconnect')
@click.option('--alias', default=None, help='Org alias to disconnect (disconnects active org if not specified)')
@click.confirmation_option(prompt='Are you sure you want to disconnect?')
def sf_disconnect(alias):
    """Disconnect from Salesforce org.

    Example:
        sma sf disconnect              # Disconnect active org
        sma sf disconnect --alias sandbox
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            if alias is None:
                status = conn_manager.get_status()
                if status:
                    alias = status['org_name']

            conn_manager.disconnect(alias)

            console.print(f"\n[bold green]✓ Disconnected from:[/bold green] [cyan]{alias}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@salesforce.command(name='sync')
@click.option('--objects-only', is_flag=True, help='Sync only objects (skip fields)')
@click.option('--flows-only', is_flag=True, help='Sync only flows and dependencies (skip objects/fields)')
@click.option('--triggers-only', is_flag=True, help='Sync only triggers (skip objects/fields)')
def sf_sync(objects_only, flows_only, triggers_only):
    """Sync Salesforce metadata to local database.

    Downloads object and field metadata from Salesforce and stores
    it locally for fast querying. Run this after connecting to populate
    the database with metadata.

    Example:
        sma sf sync                    # Sync all metadata
        sma sf sync --objects-only     # Sync only objects
        sma sf sync --flows-only       # Sync only flows
        sma sf sync --triggers-only    # Sync only triggers
    """
    try:
        with Database() as db:
            from .salesforce.metadata import MetadataSync

            conn_manager = SalesforceConnection(db)

            # Check if connected
            status = conn_manager.get_status()
            if status is None:
                console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                console.print("Run [cyan]sma sf connect[/cyan] first.\n")
                return

            # Get Salesforce client
            sf_client = conn_manager.get_client()
            if sf_client is None:
                console.print("\n[bold red]✗ Could not connect to Salesforce.[/bold red]")
                console.print("Your session may have expired. Try reconnecting:\n")
                console.print(f"  [cyan]sma sf connect --alias {status['org_name']} --client-id YOUR_ID --client-secret YOUR_SECRET[/cyan]\n")
                return

            # Create metadata sync instance
            metadata_sync = MetadataSync(sf_client, db.conn, status['org_id'], status['org_name'])

            # Check for mutually exclusive flags
            selected_flags = sum([objects_only, flows_only, triggers_only])
            if selected_flags > 1:
                console.print("\n[bold red]✗ Error:[/bold red] Only one sync option can be used at a time.\n")
                console.print("Choose one of: --objects-only, --flows-only, --triggers-only\n")
                return

            if objects_only:
                console.print("\n[bold cyan]Syncing objects only...[/bold cyan]\n")
                count = metadata_sync.sync_sobjects()
                console.print(f"\n[bold green]✓ Synced {count} objects![/bold green]\n")

            elif flows_only:
                console.print("\n[bold cyan]Syncing flows and dependencies...[/bold cyan]\n")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task1 = progress.add_task("[cyan]Retrieving flow metadata and dependencies...", total=None)
                    flow_count = metadata_sync.sync_flows_with_dependencies()
                    progress.update(task1, completed=True)

                console.print(f"\n[bold green]✓ Synced {flow_count} flows with field references![/bold green]\n")
                console.print("You can now analyse flow dependencies:\n")
                console.print(f"  [cyan]sma sf analyse field-flows Account Email[/cyan]")
                console.print(f"  [cyan]sma sf analyse flow-fields \"Flow Name\"[/cyan]\n")

            elif triggers_only:
                console.print("\n[bold cyan]Syncing triggers...[/bold cyan]\n")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task1 = progress.add_task("[cyan]Retrieving trigger metadata...", total=None)
                    trigger_count = metadata_sync.sync_trigger_metadata()
                    progress.update(task1, completed=True)

                console.print(f"\n[bold green]✓ Synced {trigger_count} triggers![/bold green]\n")
                console.print("You can now analyse trigger coverage:\n")
                console.print(f"  [cyan]sma sf analyse field-triggers Account Email[/cyan]\n")

            else:
                # Sync all metadata
                console.print("\n[bold cyan]Starting metadata sync...[/bold cyan]\n")
                result = metadata_sync.sync_all()

                # Show summary
                console.print("\n[bold cyan]Sync Summary[/bold cyan]\n")

                # Phase 2 results
                console.print("[bold]Phase 2: Basic Metadata[/bold]")
                console.print(f"  Objects synced: [green]{result.get('objects', 0)}[/green]")
                console.print(f"  Fields synced:  [green]{result.get('fields', 0)}[/green]")

                # Phase 3 results
                console.print("\n[bold]Phase 3: Dependencies & Relationships[/bold]")
                console.print(f"  Flows synced:         [green]{result.get('flows', 0)}[/green]")
                console.print(f"  Triggers synced:      [green]{result.get('triggers', 0)}[/green]")
                console.print(f"  Relationships synced: [green]{result.get('relationships', 0)}[/green]")

                console.print(f"\nYou can now analyse metadata using the analyse commands:\n")
                console.print(f"  [cyan]sma sf analyse field-flows Account Email[/cyan]")
                console.print(f"  [cyan]sma sf analyse field-deps Contact Phone[/cyan]")
                console.print(f"  [cyan]sma sf analyse object-relationships Account[/cyan]")
                console.print(f"\nOr browse the database:\n")
                console.print(f"  [cyan]sma db browse[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Sync failed:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@salesforce.command(name='search')
@click.argument('query')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--limit', default=20, help='Maximum number of results to display (default: 20)')
@click.option('--threshold', default=60, help='Minimum match score threshold (0-100, default: 60)')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
@click.option('--search-in', type=click.Choice(['all', 'name', 'label'], case_sensitive=False), default='all', help='Where to search (field name, label, or both)')
def sf_search(query, alias, limit, threshold, format, search_in):
    """Fuzzy search for fields by name or label.

    Searches across all fields in the connected Salesforce org and returns
    matches ranked by similarity score. Useful for quickly finding fields
    when you're not sure of the exact name.

    Examples:
        sma sf search email                    # Find all email-related fields
        sma sf search "created date"           # Find date fields
        sma sf search phone --limit 10         # Show top 10 matches only
        sma sf search addr --threshold 70      # Only show matches above 70% similarity
        sma sf search name --search-in label   # Search only in field labels
        sma sf search acc --format json        # Output as JSON
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']
                org_id = status['org_id']
            else:
                # Get org_id from alias
                cursor = db.conn.cursor()
                cursor.execute("SELECT org_id FROM salesforce_orgs WHERE org_name = ?", (alias,))
                result = cursor.fetchone()
                if not result:
                    console.print(f"\n[bold red]✗ Org not found:[/bold red] {alias}\n")
                    return
                org_id = result['org_id']

            # Fetch all fields from database
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT
                    f.api_name,
                    f.label,
                    f.type,
                    s.api_name as object_name,
                    s.label as object_label,
                    f.is_custom,
                    f.help_text
                FROM fields f
                JOIN sobjects s ON f.sobject_salesforce_id = s.salesforce_id
                WHERE f.org_id = ?
                ORDER BY s.api_name, f.api_name
            """, (org_id,))

            all_fields = cursor.fetchall()

            if not all_fields:
                console.print(f"\n[yellow]No fields found in database.[/yellow]")
                console.print("Run [cyan]sma sf sync[/cyan] first to populate the database.\n")
                return

            # Prepare fields for fuzzy matching
            field_choices = []
            for field in all_fields:
                search_text = []

                if search_in in ['all', 'name']:
                    search_text.append(field['api_name'])

                if search_in in ['all', 'label'] and field['label']:
                    search_text.append(field['label'])

                # Combine search texts
                combined_text = ' '.join(search_text)

                field_choices.append({
                    'search_text': combined_text,
                    'field': field
                })

            # Perform fuzzy search
            matches = []
            for choice in field_choices:
                # Calculate match score
                score = fuzz.partial_ratio(query.lower(), choice['search_text'].lower())

                if score >= threshold:
                    matches.append({
                        'field': choice['field'],
                        'score': score
                    })

            # Sort by score (descending) and limit results
            matches.sort(key=lambda x: x['score'], reverse=True)
            matches = matches[:limit]

            if not matches:
                console.print(f"\n[yellow]No fields found matching '{query}' with threshold {threshold}%[/yellow]")
                console.print(f"Try lowering the threshold with [cyan]--threshold 50[/cyan]\n")
                return

            if format == 'json':
                import json
                output = []
                for match in matches:
                    field = match['field']
                    output.append({
                        'object_name': field['object_name'],
                        'object_label': field['object_label'],
                        'field_name': field['api_name'],
                        'field_label': field['label'],
                        'type': field['type'],
                        'is_custom': bool(field['is_custom']),
                        'help_text': field['help_text'],
                        'match_score': match['score']
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Fields Matching '{query}' (Top {len(matches)} Results)",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Score", justify="right", style="green", width=6)
                table.add_column("Object", style="cyan")
                table.add_column("Field Name", style="yellow")
                table.add_column("Label", style="white")
                table.add_column("Type", style="magenta")
                table.add_column("Custom", justify="center", width=6)

                for match in matches:
                    field = match['field']
                    score = match['score']

                    # Color code score
                    if score >= 90:
                        score_str = f"[bold green]{score}%[/bold green]"
                    elif score >= 75:
                        score_str = f"[green]{score}%[/green]"
                    elif score >= 60:
                        score_str = f"[yellow]{score}%[/yellow]"
                    else:
                        score_str = f"[dim]{score}%[/dim]"

                    custom_icon = "✓" if field['is_custom'] else ""

                    table.add_row(
                        score_str,
                        field['object_name'],
                        field['api_name'],
                        field['label'] or "-",
                        field['type'] or "-",
                        custom_icon
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Total matches:[/bold] [cyan]{len(matches)}[/cyan] of [dim]{len(all_fields)}[/dim] total fields")
                console.print(f"[bold]Search query:[/bold] [cyan]{query}[/cyan]")
                console.print(f"[bold]Threshold:[/bold] [cyan]{threshold}%[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Search failed:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@salesforce.group(name='analyse')
def sf_analyse():
    """Analyse Salesforce metadata dependencies and relationships.

    Query the local database to understand field usage, automation coverage,
    and relationship mappings. Run 'sma sf sync' first to populate the database.
    """
    pass


@sf_analyse.command(name='field-flows')
@click.argument('object_name')
@click.argument('field_name')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
def analyse_field_flows(object_name, field_name, alias, format):
    """Show which flows use a specific field.

    Example:
        sma sf analyse field-flows Account Email
        sma sf analyse field-flows Opportunity StageName --alias production
        sma sf analyse field-flows Contact Phone --format json
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']

            # Query field-flow dependencies
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT
                    d.dependent_name as flow_name,
                    d.reference_type,
                    f.element_name,
                    f.element_type,
                    f.is_input,
                    f.is_output,
                    f.variable_name,
                    fm.process_type,
                    fm.trigger_type,
                    fm.is_active
                FROM sf_field_dependencies d
                LEFT JOIN sf_flow_field_references f
                    ON d.dependent_id = f.flow_id
                    AND f.object_name = d.object_name
                    AND f.field_name = d.field_name
                LEFT JOIN sf_flow_metadata fm
                    ON d.dependent_id = fm.flow_id
                WHERE d.connection_alias = ?
                  AND d.object_name = ?
                  AND d.field_name = ?
                  AND d.dependent_type = 'flow'
                ORDER BY d.dependent_name, f.element_name
            """, (alias, object_name, field_name))

            results = cursor.fetchall()

            if not results:
                console.print(f"\n[yellow]No flows found using {object_name}.{field_name}[/yellow]\n")
                return

            if format == 'json':
                import json
                output = []
                for row in results:
                    output.append({
                        'flow_name': row['flow_name'],
                        'reference_type': row['reference_type'],
                        'element_name': row['element_name'],
                        'element_type': row['element_type'],
                        'is_input': bool(row['is_input']),
                        'is_output': bool(row['is_output']),
                        'variable_name': row['variable_name'],
                        'process_type': row['process_type'],
                        'trigger_type': row['trigger_type'],
                        'is_active': bool(row['is_active'])
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Flows Using {object_name}.{field_name}",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Flow Name", style="cyan")
                table.add_column("Element", style="yellow")
                table.add_column("Element Type")
                table.add_column("Usage")
                table.add_column("Status", style="green")

                for row in results:
                    usage_parts = []
                    if row['is_input']:
                        usage_parts.append("Read")
                    if row['is_output']:
                        usage_parts.append("Write")
                    usage = ", ".join(usage_parts) if usage_parts else row['reference_type'] or "Unknown"

                    status = "Active" if row['is_active'] else "Inactive"

                    table.add_row(
                        row['flow_name'] or "Unknown",
                        row['element_name'] or "-",
                        row['element_type'] or "-",
                        usage,
                        status
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Total:[/bold] [cyan]{len(results)}[/cyan] flow element(s)\n")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@sf_analyse.command(name='field-triggers')
@click.argument('object_name')
@click.argument('field_name')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
def analyse_field_triggers(object_name, field_name, alias, format):
    """Show which triggers reference a specific field.

    Note: This shows triggers on the object. Full Apex code parsing
    for field-level usage will be added in a future phase.

    Example:
        sma sf analyse field-triggers Account Email
        sma sf analyse field-triggers Opportunity Amount --format json
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']

            # Query trigger metadata for the object
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT
                    trigger_name,
                    is_before_insert,
                    is_before_update,
                    is_before_delete,
                    is_after_insert,
                    is_after_update,
                    is_after_delete,
                    is_after_undelete,
                    is_active,
                    last_modified_date
                FROM sf_trigger_metadata
                WHERE object_name = ?
                  AND is_active = 1
                ORDER BY trigger_name
            """, (object_name,))

            results = cursor.fetchall()

            if not results:
                console.print(f"\n[yellow]No active triggers found on {object_name}[/yellow]\n")
                console.print("Note: Field-level trigger analysis requires Apex code parsing (future phase).\n")
                return

            if format == 'json':
                import json
                output = []
                for row in results:
                    events = []
                    if row['is_before_insert']: events.append('before insert')
                    if row['is_before_update']: events.append('before update')
                    if row['is_before_delete']: events.append('before delete')
                    if row['is_after_insert']: events.append('after insert')
                    if row['is_after_update']: events.append('after update')
                    if row['is_after_delete']: events.append('after delete')
                    if row['is_after_undelete']: events.append('after undelete')

                    output.append({
                        'trigger_name': row['trigger_name'],
                        'events': events,
                        'is_active': bool(row['is_active']),
                        'last_modified': row['last_modified_date']
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Triggers on {object_name}",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Trigger Name", style="cyan")
                table.add_column("Events", style="yellow")
                table.add_column("Last Modified")

                for row in results:
                    events = []
                    if row['is_before_insert']: events.append('BI')
                    if row['is_before_update']: events.append('BU')
                    if row['is_before_delete']: events.append('BD')
                    if row['is_after_insert']: events.append('AI')
                    if row['is_after_update']: events.append('AU')
                    if row['is_after_delete']: events.append('AD')
                    if row['is_after_undelete']: events.append('AUD')

                    events_str = ", ".join(events) if events else "None"

                    table.add_row(
                        row['trigger_name'],
                        events_str,
                        row['last_modified_date'] or "Unknown"
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Total:[/bold] [cyan]{len(results)}[/cyan] active trigger(s)\n")
                console.print("[dim]Note: Field-level usage requires Apex parsing (future phase)[/dim]\n")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@sf_analyse.command(name='field-deps')
@click.argument('object_name')
@click.argument('field_name')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
def analyse_field_deps(object_name, field_name, alias, format):
    """Show all dependencies for a specific field.

    Displays flows, triggers, and other automation that reference this field.

    Example:
        sma sf analyse field-deps Account Email
        sma sf analyse field-deps Contact Phone --format json
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']

            # Query all dependencies
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT
                    dependent_type,
                    dependent_name,
                    reference_type,
                    line_number,
                    last_verified
                FROM sf_field_dependencies
                WHERE connection_alias = ?
                  AND object_name = ?
                  AND field_name = ?
                ORDER BY dependent_type, dependent_name
            """, (alias, object_name, field_name))

            results = cursor.fetchall()

            if not results:
                console.print(f"\n[yellow]No dependencies found for {object_name}.{field_name}[/yellow]\n")
                console.print("This field may not be used in any tracked automation.\n")
                return

            if format == 'json':
                import json
                output = []
                for row in results:
                    output.append({
                        'type': row['dependent_type'],
                        'name': row['dependent_name'],
                        'reference_type': row['reference_type'],
                        'line_number': row['line_number'],
                        'last_verified': row['last_verified']
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Dependencies for {object_name}.{field_name}",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Type", style="cyan")
                table.add_column("Name", style="yellow")
                table.add_column("Reference Type")
                table.add_column("Last Verified")

                # Group by type
                type_counts = {}
                for row in results:
                    dep_type = row['dependent_type']
                    type_counts[dep_type] = type_counts.get(dep_type, 0) + 1

                    table.add_row(
                        dep_type,
                        row['dependent_name'] or "Unknown",
                        row['reference_type'] or "-",
                        row['last_verified'] or "Unknown"
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Summary:[/bold]")
                for dep_type, count in sorted(type_counts.items()):
                    console.print(f"  {dep_type}: [cyan]{count}[/cyan]")
                console.print()

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@sf_analyse.command(name='flow-fields')
@click.argument('flow_name')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
def analyse_flow_fields(flow_name, alias, format):
    """Show all fields used by a specific flow.

    Example:
        sma sf analyse flow-fields "Account Update Flow"
        sma sf analyse flow-fields MyFlow --format json
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']

            # Query flow field references
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT
                    f.object_name,
                    f.field_name,
                    f.element_name,
                    f.element_type,
                    f.is_input,
                    f.is_output,
                    f.variable_name
                FROM sf_flow_field_references f
                JOIN sf_flow_metadata fm ON f.flow_id = fm.flow_id
                WHERE fm.flow_api_name LIKE ? OR fm.flow_label LIKE ?
                ORDER BY f.object_name, f.field_name, f.element_name
            """, (f"%{flow_name}%", f"%{flow_name}%"))

            results = cursor.fetchall()

            if not results:
                console.print(f"\n[yellow]No field references found for flow matching '{flow_name}'[/yellow]\n")
                console.print("The flow may not exist, or hasn't been synced yet.\n")
                return

            if format == 'json':
                import json
                output = []
                for row in results:
                    output.append({
                        'object': row['object_name'],
                        'field': row['field_name'],
                        'element_name': row['element_name'],
                        'element_type': row['element_type'],
                        'is_input': bool(row['is_input']),
                        'is_output': bool(row['is_output']),
                        'variable_name': row['variable_name']
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Fields Used in Flow: {flow_name}",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Object.Field", style="cyan")
                table.add_column("Element", style="yellow")
                table.add_column("Element Type")
                table.add_column("Usage")
                table.add_column("Variable")

                for row in results:
                    usage_parts = []
                    if row['is_input']:
                        usage_parts.append("Read")
                    if row['is_output']:
                        usage_parts.append("Write")
                    usage = ", ".join(usage_parts) if usage_parts else "-"

                    table.add_row(
                        f"{row['object_name']}.{row['field_name']}",
                        row['element_name'] or "-",
                        row['element_type'] or "-",
                        usage,
                        row['variable_name'] or "-"
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Total:[/bold] [cyan]{len(results)}[/cyan] field reference(s)\n")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@sf_analyse.command(name='object-relationships')
@click.argument('object_name')
@click.option('--alias', default=None, help='Salesforce org alias (uses active org if not specified)')
@click.option('--direction', type=click.Choice(['all', 'parent', 'child'], case_sensitive=False), default='all', help='Relationship direction to show')
@click.option('--format', type=click.Choice(['table', 'json'], case_sensitive=False), default='table', help='Output format')
def analyse_object_relationships(object_name, alias, direction, format):
    """Show relationship graph for a Salesforce object.

    Displays lookup, master-detail, and other relationships.

    Example:
        sma sf analyse object-relationships Account
        sma sf analyse object-relationships Contact --direction parent
        sma sf analyse object-relationships Opportunity --format json
    """
    try:
        with Database() as db:
            conn_manager = SalesforceConnection(db)

            # Determine which org to query
            if alias is None:
                status = conn_manager.get_status()
                if status is None:
                    console.print("\n[yellow]No active Salesforce connection.[/yellow]")
                    console.print("Run [cyan]sma sf connect[/cyan] first or specify --alias.\n")
                    return
                alias = status['org_name']

            # Build query based on direction
            if direction == 'parent':
                # This object is the child, show parent relationships
                query = """
                    SELECT
                        source_field,
                        relationship_type,
                        target_object,
                        target_field,
                        relationship_name,
                        is_cascade_delete,
                        is_reparentable
                    FROM sf_field_relationships
                    WHERE connection_alias = ?
                      AND source_object = ?
                      AND target_object IS NOT NULL
                    ORDER BY relationship_type, source_field
                """
                params = (alias, object_name)
            elif direction == 'child':
                # This object is the parent, show child relationships
                query = """
                    SELECT
                        child_object,
                        relationship_field,
                        relationship_type,
                        relationship_name,
                        child_count_estimate
                    FROM sf_object_relationships
                    WHERE connection_alias = ?
                      AND parent_object = ?
                    ORDER BY relationship_type, child_object
                """
                params = (alias, object_name)
            else:
                # Show both directions
                # We'll run two queries and combine results
                pass

            cursor = db.conn.cursor()

            if direction in ['parent', 'all']:
                # Query parent relationships
                cursor.execute("""
                    SELECT
                        'parent' as direction,
                        source_field as field,
                        relationship_type,
                        target_object as related_object,
                        relationship_name,
                        is_cascade_delete,
                        is_reparentable
                    FROM sf_field_relationships
                    WHERE connection_alias = ?
                      AND source_object = ?
                      AND target_object IS NOT NULL
                    ORDER BY relationship_type, source_field
                """, (alias, object_name))

                parent_results = cursor.fetchall()
            else:
                parent_results = []

            if direction in ['child', 'all']:
                # Query child relationships
                cursor.execute("""
                    SELECT
                        'child' as direction,
                        relationship_field as field,
                        relationship_type,
                        child_object as related_object,
                        relationship_name,
                        0 as is_cascade_delete,
                        1 as is_reparentable
                    FROM sf_object_relationships
                    WHERE connection_alias = ?
                      AND parent_object = ?
                    ORDER BY relationship_type, child_object
                """, (alias, object_name))

                child_results = cursor.fetchall()
            else:
                child_results = []

            results = list(parent_results) + list(child_results)

            if not results:
                console.print(f"\n[yellow]No relationships found for {object_name}[/yellow]\n")
                return

            if format == 'json':
                import json
                output = []
                for row in results:
                    output.append({
                        'direction': row['direction'],
                        'field': row['field'],
                        'type': row['relationship_type'],
                        'related_object': row['related_object'],
                        'relationship_name': row['relationship_name'],
                        'cascade_delete': bool(row['is_cascade_delete']),
                        'reparentable': bool(row['is_reparentable'])
                    })
                console.print(json.dumps(output, indent=2))
            else:
                # Table format
                table = Table(
                    title=f"Relationships for {object_name}",
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Direction", style="magenta")
                table.add_column("Field", style="cyan")
                table.add_column("Type", style="yellow")
                table.add_column("Related Object", style="green")
                table.add_column("Relationship Name")
                table.add_column("Cascade Delete")

                for row in results:
                    direction_icon = "⬆" if row['direction'] == 'parent' else "⬇"
                    cascade = "Yes" if row['is_cascade_delete'] else "No"

                    table.add_row(
                        f"{direction_icon} {row['direction'].title()}",
                        row['field'],
                        row['relationship_type'] or "Unknown",
                        row['related_object'],
                        row['relationship_name'] or "-",
                        cascade
                    )

                console.print()
                console.print(table)
                console.print(f"\n[bold]Total:[/bold] [cyan]{len(results)}[/cyan] relationship(s)\n")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


# Database commands group
@main.group(name='db')
def database():
    """Database management commands."""
    pass


@database.command(name='browse')
@click.option('--port', default=8001, help='Port for datasette server (default: 8001)')
@click.option('--no-browser', is_flag=True, help='Do not open browser automatically')
def db_browse(port, no_browser):
    """Open interactive database browser in web browser.

    Uses datasette to provide a beautiful web interface for exploring
    the SMA database. You can browse tables, run SQL queries, and
    export data.

    Example:
        sma db browse
        sma db browse --port 8080
        sma db browse --no-browser
    """
    try:
        db_path = Path.home() / ".sma" / "sma.db"

        if not db_path.exists():
            console.print("\n[yellow]Database not found.[/yellow]")
            console.print("The database will be created when you run your first command.\n")
            return

        console.print(f"\n[bold cyan]Starting database browser...[/bold cyan]\n")
        console.print(f"Database: [cyan]{db_path}[/cyan]")
        console.print(f"Port: [cyan]{port}[/cyan]")
        console.print(f"\nPress [bold]Ctrl+C[/bold] to stop the server.\n")

        # Build datasette command
        cmd = ['datasette', str(db_path), '--port', str(port)]

        if not no_browser:
            cmd.append('--open')

        # Run datasette
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            console.print("\n\n[green]Database browser stopped.[/green]\n")
        except FileNotFoundError:
            console.print("\n[bold red]Error:[/bold red] datasette is not installed.\n")
            console.print("Install it with: [cyan]pip install datasette[/cyan]\n")
            raise click.Abort()

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@database.command(name='stats')
def db_stats():
    """Show database statistics.

    Displays information about the SMA database including:
    - Database location and size
    - Number of tables
    - Record counts per table
    """
    try:
        db_path = Path.home() / ".sma" / "sma.db"

        if not db_path.exists():
            console.print("\n[yellow]Database not found.[/yellow]")
            console.print("The database will be created when you run your first command.\n")
            return

        # Get file size
        size_bytes = db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        console.print(f"\n[bold cyan]Database Statistics[/bold cyan]\n")
        console.print(f"Location: [cyan]{db_path}[/cyan]")
        console.print(f"Size: [cyan]{size_mb:.2f} MB[/cyan] ({size_bytes:,} bytes)\n")

        # Get table statistics
        with Database() as db:
            cursor = db.conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row['name'] for row in cursor.fetchall()]

            if not tables:
                console.print("[yellow]No tables found.[/yellow]\n")
                return

            # Create table for stats
            stats_table = Table(title="Table Statistics", show_header=True, header_style="bold cyan")
            stats_table.add_column("Table Name", style="cyan")
            stats_table.add_column("Row Count", justify="right", style="green")

            total_rows = 0
            for table_name in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                total_rows += count
                stats_table.add_row(table_name, f"{count:,}")

            console.print(stats_table)
            console.print(f"\n[bold]Total Tables:[/bold] [cyan]{len(tables)}[/cyan]")
            console.print(f"[bold]Total Records:[/bold] [cyan]{total_rows:,}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@database.command(name='path')
def db_path():
    """Show database file path.

    Displays the full path to the SMA database file.
    Useful for opening the database in external tools.
    """
    db_path = Path.home() / ".sma" / "sma.db"

    console.print(f"\n[bold cyan]Database Path:[/bold cyan]\n")
    console.print(f"[cyan]{db_path}[/cyan]\n")

    if db_path.exists():
        size_bytes = db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        console.print(f"Size: [green]{size_mb:.2f} MB[/green]\n")
    else:
        console.print("[yellow]Database does not exist yet.[/yellow]\n")


@database.command(name='reset')
@click.confirmation_option(prompt='Are you sure you want to reset the database? This will clear all Salesforce metadata but keep greetings, quotes, and org connections.')
def db_reset():
    """Reset database metadata while preserving greetings, quotes, and org connections.

    This will:
    - Clear all Salesforce metadata tables (objects, fields, flows, triggers, etc.)
    - Keep greetings table data
    - Keep quotes table data
    - Keep salesforce_orgs table data

    Use this to start fresh with metadata sync without losing your org connections.

    Example:
        sma db reset
    """
    try:
        with Database() as db:
            cursor = db.conn.cursor()

            # List of tables to clear (all Salesforce metadata except salesforce_orgs)
            tables_to_clear = [
                'sobjects',
                'fields',
                'sf_field_dependencies',
                'sf_flow_field_references',
                'sf_field_relationships',
                'sf_object_relationships',
                'sf_trigger_metadata',
                'sf_flow_metadata',
                'sf_automation_coverage'
            ]

            console.print("\n[bold cyan]Resetting database...[/bold cyan]\n")

            cleared_counts = {}
            for table in tables_to_clear:
                # Check if table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=?
                """, (table,))

                if cursor.fetchone():
                    # Count before clearing
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    cleared_counts[table] = count

                    # Clear the table
                    cursor.execute(f"DELETE FROM {table}")

            db.conn.commit()

            # Show what was cleared
            if cleared_counts:
                console.print("[bold green]✓ Database reset complete![/bold green]\n")
                console.print("[bold]Cleared tables:[/bold]")
                for table, count in cleared_counts.items():
                    console.print(f"  {table}: [yellow]{count:,}[/yellow] records removed")
                console.print()
            else:
                console.print("[yellow]No metadata found to clear.[/yellow]\n")

            # Show what was preserved
            console.print("[bold]Preserved tables:[/bold]")
            preserved_tables = ['greetings', 'quotes', 'salesforce_orgs']
            for table in preserved_tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                console.print(f"  {table}: [green]{count:,}[/green] records kept")
            console.print()

    except Exception as e:
        console.print(f"\n[bold red]✗ Reset failed:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise click.Abort()


if __name__ == '__main__':
    main()
