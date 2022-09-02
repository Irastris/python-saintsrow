import click

from ..classes.SR5Archive import SR5Archive
from ..functions.threadedExtractor import threadedExtractor

def printEntryInfo(entry, dataOffsetBase):
    print("")
    print(f"Entry Offset:    {entry[0]}")
    print(f"Filename:        {entry[10]}")
    print(f"Path:            {entry[9]}")
    print(f"Data Offset:     {entry[3]} ({entry[3] + dataOffsetBase})")
    print(f"Size:            {entry[4]}")
    print(f"Compressed Size: {entry[5]}")
    print(f"Flags:           {entry[6]}")
    print(f"Alignment:       {entry[7]}")
    print(f"Unk00:           {entry[8]}")

@click.command()
@click.option("-e", "--extract", is_flag=True, help="Extract matching file(s)")
@click.option("-q", "--query", type=str, default="", help="String to search for")
@click.argument("input", type=click.Path())
def search(input, query, extract):
    """Search (and optionally extract) a .vpp_pc or .str2_pc archive."""

    with open(input, "rb") as inputFile:
        archive = SR5Archive(inputFile)

    # Search Files
    matches = []
    for entry in archive.fileTable:
        if query in entry[10]:
            matches.append(entry)

    # Print Matches
    for match in matches:
        printEntryInfo(match, archive.header.dataOffsetBase)
        if extract:
            threadedExtractor(input, match[1] + archive.header.dataOffsetBase, match[2], match[3], match[4], match[9], match[10]) # No need to actually thread
            print("Extracted")
