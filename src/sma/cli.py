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
from .database import Database
from .salesforce.connection import SalesforceConnection

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


if __name__ == '__main__':
    main()
