import click

from .commands import extract
from .commands import search

@click.group()
def cli():
    pass

cli.add_command(extract.extract)
cli.add_command(search.search)

if __name__ == "__main__":
    cli()
