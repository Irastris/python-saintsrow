import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
import progressbar

from ..classes.SR5Archive import SR5Archive
from ..functions.threadedExtractor import threadedExtractor

widgets = ["Extracting Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]

@click.command()
@click.argument("input", type=click.Path())
def extract(input):
    """Extract a .vpp_pc or .str2_pc archive."""

    print("")
    with open(input, "rb") as inputFile:
        archive = SR5Archive(inputFile)

    # Build Tables
    fileTable = {}
    for i in range(archive.header.fileCount):
        filename = archive.fileTable[i][9]
        if filename not in fileTable:
            fileTable[filename] = {}
        fileTable[filename]["entryOffset"]    = archive.fileTable[i][0]
        fileTable[filename]["nameOffset"]     = archive.fileTable[i][6]
        fileTable[filename]["pathOffset"]     = archive.fileTable[i][7]
        fileTable[filename]["dataOffset"]     = archive.fileTable[i][1]
        fileTable[filename]["size"]           = archive.fileTable[i][2]
        fileTable[filename]["sizeCompressed"] = archive.fileTable[i][3]
        fileTable[filename]["flags"]          = archive.fileTable[i][4]
        fileTable[filename]["unk00"]          = archive.fileTable[i][5]

    # Dump Tables To JSON
    stem = Path(input).name
    with open(f"{stem}.json", "w") as jsonFile:
        jsonFile.write(json.dumps(fileTable, indent=4))

    # Extract Files
    filesExtracted = 0
    with ThreadPoolExecutor() as pool, progressbar.ProgressBar(widgets=widgets, max_value=len(archive.fileTable)) as bar:
        threads = []

        for i in range(len(archive.fileTable)):
            dataOffset      = archive.fileTable[i][1]
            size            = archive.fileTable[i][2]
            compressedSize  = archive.fileTable[i][3]
            flags           = archive.fileTable[i][4]
            path            = archive.fileTable[i][8]
            filename        = archive.fileTable[i][9]

            thread = pool.submit(threadedExtractor, input, dataOffset + archive.header.dataOffsetBase, size, compressedSize, flags, path, filename)
            threads.append(thread)

        for thread in as_completed(threads):
            thread.result()
            filesExtracted += 1
            bar.update(filesExtracted)
