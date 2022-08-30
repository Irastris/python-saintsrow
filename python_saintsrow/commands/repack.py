from pathlib import Path
from time import time

import click
import progressbar

from ..functions.binaryUtils import int32pack, int64pack

widgets = ["Packing Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]

@click.command()
@click.argument("input", type=click.Path())
@click.argument("output", type=click.Path())
def repack(input, output):
    """Repack a folder into a .vpp_pc or .str2_pc"""

    print("")
    dataDir = Path(input)
    if dataDir.is_file(): exit("Invalid input, must be data directory!")

    # Get Files
    files = []
    for file in dataDir.glob("**/*"):
        if Path(file).is_file():
            files.append(file)

    # Get Directories
    directories = []
    for file in files:
        directory = str(file.parents[0])
        if directory.startswith("data\\engine"):
            directory = f"..\\ctg\\{directory}"
        if directory not in directories:
            directories.append(directory)

    # Build Name Table
    # TODO: Fix and optimize this, only correct if no compressed data exists in pack
    fileTable = [] # Name Offset, Directory Offset, Data Offset, Size, Compressed Size, Flags
    directoryDict = {}
    nameTable = b""
    dataLength = 0
    for file in files:
        fileEntry = files.index(file)
        fileTable.append([len(nameTable)])
        nameTable = nameTable + str.encode(file.name) + b"\x00"
        directory = str(file.parents[0])
        if directory.startswith("data\\engine"):
            directory = f"..\\ctg\\{directory}"
        if directory in directoryDict:
            fileTable[fileEntry].append(directoryDict[directory])
        else:
            directoryDict[directory] = (len(nameTable))
            fileTable[fileEntry].append(directoryDict[directory])
            nameTable = nameTable + str.encode(directory) + b"\x00"
        filesize = file.stat().st_size
        fileTable[fileEntry].extend((dataLength, filesize, 18446744073709551615, 65536)) # 65536 if uncompressed
        dataLength += filesize

    with open(output, "wb") as archive:
        # Header
        archive.write(int32pack(1367935694))       # Magic
        archive.write(int32pack(17))               # Version
        archive.write(int32pack(0))                # CRC (Unused? Doesn't seem to care if it's calculated or not)
        archive.write(int32pack(0))                # Flags | TODO: Research this more
        archive.write(int32pack(len(files)))       # File Count
        archive.write(int32pack(len(directories))) # Directory Count
        namesOffset = archive.tell()
        archive.write(int32pack(0))                # Names Offset, set later
        archive.write(int32pack(0))                # Names Size, set later
        packSize = archive.tell()
        archive.write(int64pack(0))                # Pack Size, set later
        # TODO: Fix next two writes, only correct if not compressing anything
        archive.write(int64pack(dataLength))       # Uncompressed Size
        archive.write(int64pack(0))                # Size (0 if no compressed files)
        archive.write(int64pack(int(time())))      # Timestamp
        dataOffsetBase = archive.tell()
        archive.write(int64pack(0))                # Data Offset Base, set later
        archive.write(b"\x00" * 48)                # 48 Zeroes

        # File Table
        for entry in fileTable:
            archive.write(int64pack(entry[0])) # Name Offset
            archive.write(int64pack(entry[1])) # Directory Offset
            archive.write(int64pack(entry[2])) # Data Offset
            archive.write(int64pack(entry[3])) # Size
            archive.write(int64pack(entry[4])) # Compressed Size
            archive.write(int64pack(entry[5])) # Flags

        # Directory Offsets
        for directoryOffset in directoryDict.values():
            archive.write(int64pack(directoryOffset))

        # Name Table
        curPos = archive.tell()
        archive.seek(namesOffset)
        archive.write(int32pack(curPos - 120))
        archive.write(int32pack(len(nameTable)))
        archive.seek(curPos)
        archive.write(nameTable)

        # Data
        curPos = archive.tell()
        archive.seek(dataOffsetBase)
        archive.write(int32pack(curPos))
        archive.seek(curPos)
        for i in progressbar.progressbar(range(len(files)), widgets=widgets):
            with open(files[i], "rb") as data:
                archive.write(data.read())

        # Pack Size
        curPos = archive.tell()
        archive.seek(packSize)
        archive.write(int32pack(curPos))
        archive.seek(curPos)
