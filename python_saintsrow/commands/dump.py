import json
from pathlib import Path

import click
import lz4.frame as lz4f
import progressbar

from ..classes.SR5Archive import SR5Archive

widgets = ["Packing Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]

@click.command()
@click.argument("input", type=click.Path())
def dump(input):
    """Dump entry table from a .vpp_pc or .str2_pc to JSON for repacking"""

    print("")
    with open(input, "rb") as inputFile:
        archive = SR5Archive(inputFile)

    # Build Tables
    fileTable = {}
    for i in range(archive.header.fileCount):
        filename = archive.fileTable[i][9]
        if filename not in fileTable:
            fileTable[filename] = {}
        fileTable[filename]["entryOffset"] = archive.fileTable[i][0]
        fileTable[filename]["nameOffset"] = archive.fileTable[i][6]
        fileTable[filename]["pathOffset"] = archive.fileTable[i][7]
        fileTable[filename]["dataOffset"] = archive.fileTable[i][1]
        fileTable[filename]["size"] = archive.fileTable[i][2]
        fileTable[filename]["sizeCompressed"] = archive.fileTable[i][3]
        fileTable[filename]["flags"] = archive.fileTable[i][4]
        fileTable[filename]["unk00"] = archive.fileTable[i][5]

    stem = Path(input).name
    with open(f"{stem}.json", "w") as jsonFile:
        jsonFile.write(json.dumps(fileTable, indent=4))
