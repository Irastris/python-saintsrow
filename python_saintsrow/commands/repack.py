import math
import json
from pathlib import Path

import click
import lz4.frame as lz4f
import progressbar

from ..classes.SR5Archive import SR5Archive
from ..functions.binaryUtils import int32pack, int64pack

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

    # Load JSON Dump
    with open(b, "r") as jsonFile:
        fileTable = json.load(jsonFile)

    # Get Unpacked Files
    files = {}
    for file in Path(c).glob("**/*"):
        if Path(file).is_file():
            if file.name in files:
                print(f"Duplicate! {file.name}")
            else:
                files[file.name] = file

    # Build Name Table
    with open(a, "rb") as inputArchive:
        archive = SR5Archive(inputArchive)

    # Output
    with open(d, "wb") as outputArchive:
        # Header
        outputArchive.write(int32pack(archive.header.magic))            # Magic
        outputArchive.write(int32pack(archive.header.version))          # Version
        outputArchive.write(int32pack(archive.header.crc))              # CRC | TODO: Research this more
        outputArchive.write(int32pack(archive.header.flags))            # Flags | TODO: Research this more
        outputArchive.write(int32pack(archive.header.fileCount))        # File Count
        outputArchive.write(int32pack(archive.header.dirCount))         # Directory Count
        outputArchive.write(int32pack(archive.header.namesOffset))      # Names Offset, set later
        outputArchive.write(int32pack(archive.header.namesSize))        # Names Size, set later
        outputArchive.write(int64pack(archive.header.packSize))         # Pack Size, set later
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
            outputArchive.write(int32pack(fileTable[file]["flags"])) # Flags
            outputArchive.write(int32pack(fileTable[file]["unk00"])) # Unk00

        # Directory Offsets
        outputArchive.write(archive.dirTable)

        # Name Table
        outputArchive.write(archive.nameTable)

        # Data
        outputArchive.seek(archive.header.dataOffsetBase)
        for file in fileTable: # progressbar.progressbar(range(len(files)), widgets=widgets)
            isFileAligned = any(format in file for format in [".bk2"])
            with open(files[file], "rb") as data:
                bytes = data.read()
                if isFileAligned: outputArchive.seek(int(math.ceil(outputArchive.tell() / 2048)) * 2048)
                outputArchive.write(bytes)
