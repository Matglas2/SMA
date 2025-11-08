"""CLI interface for SMA."""

import click
import random
import os
from datetime import datetime
from .database import Database


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


if __name__ == '__main__':
    main()
