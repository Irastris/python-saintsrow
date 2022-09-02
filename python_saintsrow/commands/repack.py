import json
import math
import tempfile
from pathlib import Path

import click
import progressbar

from ..classes.SR5Archive import SR5Archive
from ..functions.binaryUtils import int16pack, int32pack, int64pack
from ..functions.lz4f import lz4fCompress

widgets = ["Packing Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]

@click.command()
@click.argument("a", type=click.Path()) # Original Archive
@click.argument("b", type=click.Path()) # JSON Dump
@click.argument("c", type=click.Path()) # Data Directory
@click.argument("d", type=click.Path()) # Output Archive
def repack(a, b, c, d):
    """Repack a folder into a .vpp_pc or .str2_pc"""

    print("")
    if Path(c).is_file(): exit("Invalid C input, must be data directory!")

    # Parse Original Archive
    with open(a, "rb") as inputArchive:
        archive = SR5Archive(inputArchive)
    # Reset these values because we add to them later to get the correct size
    archive.header.uncompressedSize = 0
    archive.header.size = 0

    # Get Unpacked Files
    files = {}
    for file in Path(c).glob("**/*"):
        if Path(file).is_file():
            if file.name in files:
                print(f"Duplicate! {file.name}")
            else:
                files[file.name] = file

    # Load JSON Dump
    with open(b, "r") as jsonFile:
        fileTable = json.load(jsonFile)

    # Data Preprocessing
    dataBlock = tempfile.TemporaryFile()
    for file in progressbar.progressbar(fileTable, widgets=widgets):
        filepath = Path(files[file])

        # TODO: Figure out the oddity surrounding alignment. Only BK2 consistently works when respecting its alignment
        align = fileTable[file]["align"]
        isFileAligned = ".bk2" in file
        if isFileAligned: dataBlock.seek(int(math.ceil(dataBlock.tell() / align)) * align)

        fileTable[file]["dataOffset"] = dataBlock.tell() # Update data offset

        with open(files[file], "rb") as data:
            if fileTable[file]["flags"] & 1:
                lz4 = lz4fCompress(data.read())
                dataBlock.write(lz4)
                fileTable[file]["sizeCompressed"] = len(lz4)
                archive.header.size += len(lz4)
            else:
                dataBlock.write(data.read())
                fileTable[file]["size"] == filepath.stat().st_size
                archive.header.size += filepath.stat().st_size

        archive.header.uncompressedSize += filepath.stat().st_size

    # Output
    with open(d, "wb") as outputArchive:
        # Header
        outputArchive.write(int32pack(archive.header.magic))            # Magic
        outputArchive.write(int32pack(archive.header.version))          # Version
        outputArchive.write(int32pack(archive.header.crc))              # CRC | TODO: Research this more
        outputArchive.write(int32pack(archive.header.flags))            # Flags | TODO: Research this more
        outputArchive.write(int32pack(archive.header.fileCount))        # File Count
        outputArchive.write(int32pack(archive.header.dirCount))         # Directory Count
        outputArchive.write(int32pack(archive.header.namesOffset))      # Names Offset
        outputArchive.write(int32pack(archive.header.namesSize))        # Names Size
        packSizeOffset = outputArchive.tell()
        outputArchive.write(int64pack(archive.header.packSize))         # Pack Size
        outputArchive.write(int64pack(archive.header.uncompressedSize)) # Size
        outputArchive.write(int64pack(archive.header.size))             # Compressed Size
        outputArchive.write(int64pack(archive.header.timestamp))        # Timestamp
        outputArchive.write(int64pack(archive.header.dataOffsetBase))   # Data Offset Base
        outputArchive.write(archive.header.unk03)                       # 48 Zeroes

        # File Table
        for file in fileTable:
            outputArchive.write(int64pack(fileTable[file]["nameOffset"])) # Name Offset
            outputArchive.write(int64pack(fileTable[file]["pathOffset"])) # Path Offset
            outputArchive.write(int64pack(fileTable[file]["dataOffset"])) # Data Offset
            outputArchive.write(int64pack(fileTable[file]["size"])) # Size
            outputArchive.write(int64pack(fileTable[file]["sizeCompressed"])) # Compressed Size
            outputArchive.write(int16pack(fileTable[file]["flags"])) # Flags
            outputArchive.write(int16pack(fileTable[file]["align"])) # Alignment
            outputArchive.write(int32pack(fileTable[file]["unk00"])) # Unk00

        # Directory Offsets
        outputArchive.write(archive.dirTable)

        # Name Table
        outputArchive.write(archive.nameTable)

        # Data
        outputArchive.seek(archive.header.dataOffsetBase)
        dataBlock.seek(0)
        outputArchive.write(dataBlock.read())

        # Pack Size
        packSize = outputArchive.tell()
        outputArchive.seek(packSizeOffset)
        outputArchive.write(int64pack(packSize))

    dataBlock.close()
