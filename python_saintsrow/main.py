import click

from .commands import extract
from .commands import repack
from .commands import search
from .commands import tests

@click.group()
def cli():
    pass

cli.add_command(extract.extract)
cli.add_command(repack.repack)
cli.add_command(search.search)
cli.add_command(tests.tests)

if __name__ == "__main__":
    cli()
