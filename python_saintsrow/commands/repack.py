from pathlib import Path

import click
import lz4.frame as lz4f
import progressbar

from ..functions.binaryUtils import int32pack, int64pack

widgets = ["Packing Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]

@click.command()
@click.option("-c", "--compress", is_flag=True, help="Compress files, required for packing str2_pc")
@click.argument("input", type=click.Path())
@click.argument("output", type=click.Path())
def repack(input, output, compress):
    """Repack a folder into a .vpp_pc or .str2_pc"""

    print("")
    if Path(input).is_file(): exit("Invalid input, must be data directory!")

    # Get Files
    files = []
    for file in Path(input).glob("**/*"):
        if Path(file).is_file():
            files.append(file)

    # Build Tables
    fileTable = {}
    nameTable = b""
    dataLength = 0
    dataLengthCompressed = 0
    for i in range(len(files)): # Loop through all files
        fileEntry = files[i] # Get entry from index
        directory = str(fileEntry.parents[0]) # Get directory from filepath
        filename = str(fileEntry.name) # Get filename from filepath
        filesize = fileEntry.stat().st_size
        if directory.startswith("data\\engine"):
            directory = f"..\\ctg\\{directory}" # Fix engine data paths | TODO: Can this be better?
        if directory not in fileTable: # Initialize a key for this directory
            fileTable[directory] = {}
            fileTable[directory]["files"] = {}
            fileTable[directory]["pathOffset"] = (len(nameTable)) # Set path offset
            nameTable = nameTable + str.encode(directory) + b"\x00" # Append directory to the nameTable
        if filename not in fileTable[directory]["files"]:
            fileTable[directory]["files"][filename] = {} # Initialize
        fileTable[directory]["files"][filename]["nameOffset"] = len(nameTable) # Set name offset
        nameTable = nameTable + str.encode(filename) + b"\x00" # Append filename to the nameTable
        fileTable[directory]["files"][filename]["size"] = filesize # Set filesize
        compressedSize = 18446744073709551615 # Maximum int64 if file is not compressed
        if compress:
            with open(fileEntry, "rb") as file:
                compressedSize = len(lz4f.compress(file.read())) # LZ4 compress and get length | TODO: Can this be better?
        fileTable[directory]["files"][filename]["sizeCompressed"] = compressedSize # Set compressed filesize
        fileTable[directory]["files"][filename]["flags"] = 65537 if compress else 65536 # Set flags | TODO: Research flags more
        fileTable[directory]["files"][filename]["dataOffset"] = dataLengthCompressed if compress else dataLength # Set data offset
        dataLength += filesize
        dataLengthCompressed += compressedSize if compress else filesize

    with open(output, "wb") as archive:
        # Header
        archive.write(int32pack(1367935694))               # Magic
        archive.write(int32pack(17))                       # Version
        archive.write(int32pack(0))                        # CRC | TODO: Research this more
        archive.write(int32pack(20481 if compress else 0)) # Flags | TODO: Research this more
        archive.write(int32pack(len(files)))               # File Count
        archive.write(int32pack(len(fileTable)))           # Directory Count
        namesOffset = archive.tell()
        archive.write(int32pack(0))                        # Names Offset, set later
        archive.write(int32pack(0))                        # Names Size, set later
        packSize = archive.tell()
        archive.write(int64pack(0))                        # Pack Size, set later
        archive.write(int64pack(dataLength))               # Size
        archive.write(int64pack(dataLengthCompressed))     # Compressed Size
        archive.write(int64pack(0))                        # Timestamp
        dataOffsetBase = archive.tell()
        archive.write(int64pack(0))                        # Data Offset Base
        archive.write(b"\x00" * 48)                        # 48 Zeroes

        # File Table
        for directory in fileTable:
            for file in fileTable[directory]["files"]:
                archive.write(int64pack(fileTable[directory]["files"][file]["nameOffset"])) # Name Offset
                archive.write(int64pack(fileTable[directory]["pathOffset"])) # Path Offset
                archive.write(int64pack(fileTable[directory]["files"][file]["dataOffset"])) # Data Offset
                archive.write(int64pack(fileTable[directory]["files"][file]["size"])) # Size
                archive.write(int64pack(fileTable[directory]["files"][file]["sizeCompressed"])) # Compressed Size
                archive.write(int32pack(fileTable[directory]["files"][file]["flags"])) # Flags
                archive.write(int32pack(0))

        # Directory Offsets
        for directory in fileTable:
            archive.write(int64pack(fileTable[directory]["pathOffset"])) # Path Offset

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
                if compress:
                    archive.write(lz4f.compress(data.read()))
                else:
                    archive.write(data.read())

        # Pack Size
        curPos = archive.tell()
        archive.seek(packSize)
        archive.write(int32pack(curPos))
        archive.seek(curPos)
