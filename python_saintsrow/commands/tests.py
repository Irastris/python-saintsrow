import json
from pathlib import Path

import click
import lz4.frame as lz4f

from ..classes.SR5Archive import SR5Archive
from ..functions.lz4f import lz4fCompress
from ..functions.threadedExtractor import threadedExtractor

@click.command()
@click.option("-lz4", is_flag=True, help="Perform LZ4 test")
@click.argument("input", type=click.Path())
def tests(input, lz4):
    """Perform miscellaneous, evolving tests."""

    print("")

    if lz4:
        inputPath = Path(input)

        # Open Input Archive
        with open(input, "rb") as inputFile:
            archive = SR5Archive(inputFile)

            # Build Tables
            for i in range(archive.header.fileCount):
                dataOffset     = archive.fileTable[i][3]
                size           = archive.fileTable[i][4]
                sizeCompressed = archive.fileTable[i][5]
                flags          = archive.fileTable[i][6]
                path           = archive.fileTable[i][9]
                filename       = archive.fileTable[i][10]

                inputFile.seek(dataOffset + archive.header.dataOffsetBase)
                if flags & 1:
                    dataLz4 = inputFile.read(sizeCompressed)
                    data = lz4f.decompress(dataLz4, size)
                    dataLz4_2 = lz4fCompress(data)
                    if dataLz4 != dataLz4_2:
                        print(f"Compression mismatch! {filename}")
                        # threadedExtractor(inputPath, dataOffset + archive.header.dataOffsetBase, size, sizeCompressed, flags, path, filename)
