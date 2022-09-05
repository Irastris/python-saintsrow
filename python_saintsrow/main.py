import click

from python_saintsrow.commands.archive import extract
from python_saintsrow.commands.archive import repack
from python_saintsrow.commands.archive import search
from python_saintsrow.commands.archive import tests

@click.group()
def cli():
    pass

@click.group()
def archive():
    """Operations on .vpp_pc/.str2_pc archives."""
    pass

archive.add_command(extract.extract)
archive.add_command(repack.repack)
archive.add_command(search.search)
archive.add_command(tests.tests)

cli.add_command(archive)

if __name__ == "__main__":
    cli()
