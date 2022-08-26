import os, sys
from struct import unpack

import lz4.frame as lz4f
import click
import progressbar

def unpackLong(file): return unpack("<I", file.read(4))[0]
def unpackLongLong(file): return unpack("<Q", file.read(8))[0]

@click.group()
def cli():
    pass

@cli.command()
@click.argument("input", type=click.File("rb"))
def tableParse(input):
    """Prints a list of files contained within a .vpp_pc or .str2_pc archive."""

    # Header
    magic = unpackLong(input)
    if magic != 1367935694: sys.exit("Magic is incorrect, unsupported input!")
    input.seek(12, 1) # 8 Unknown Bytes
    fileCount = unpackLong(input)
    input.seek(4, 1) # 4 Unknown Bytes
    namesOffset = unpackLong(input)
    namesSize = unpackLong(input)
    input.seek(32, 1) # 8 Unknown Bytes
    baseOffset = unpackLongLong(input)
    input.seek(48, 1) # 48 Unknown Bytes, Always Zeros?

    # Name Table
    curPos = input.tell()
    input.seek(namesOffset + curPos)
    nameTable = input.read(namesSize)
    input.seek(curPos)

    # Files
    for i in range(fileCount):
        print(f"\nTable Entry {i}")
        filename = nameTable[unpackLongLong(input):].split(b"\x00")[0].decode("utf-8")
        print(f"({input.tell() - 8}) Filename: {filename}")
        path = nameTable[unpackLongLong(input):].split(b"\x00")[0].decode("utf-8")
        print(f"({input.tell() - 8}) Path: {path}")
        dataOffset = unpackLongLong(input)
        print(f"({input.tell() - 8}) Data Offset: {dataOffset}")
        size = unpackLongLong(input)
        print(f"({input.tell() - 8}) Size: {size}")
        compressedSize = unpackLongLong(input)
        print(f"({input.tell() - 8}) Compressed Size: {compressedSize}")
        flags = unpackLongLong(input)
        isFileCompressed = "Compressed" if flags & 1 else "Uncompressed"
        print(f"({input.tell() - 8}) Flags: {flags} ({isFileCompressed})")

@cli.command()
@click.option("-sA", "--skip-audio", is_flag=True, help="Skip extracting audio data")
@click.option("-sC", "--skip-compressed", is_flag=True, help="Skip extracting compressed data")
@click.argument("input", type=click.File("rb"))
def extract(input, skip_audio, skip_compressed):
    """Extract a .vpp_pc or .str2_pc archive."""

    # Header
    magic = unpackLong(input)
    if magic != 1367935694: sys.exit("Magic is incorrect, unsupported input!")
    version = unpackLong(input)
    input.seek(8, 1) # 8 Unknown Bytes
    fileCount = unpackLong(input)
    input.seek(4, 1) # 4 Unknown Bytes
    namesOffset = unpackLong(input)
    namesSize = unpackLong(input)
    packSize = unpackLongLong(input)
    input.seek(8, 1) # 8 Unknown Bytes
    dataSize = unpackLongLong(input)
    timestamp = unpackLongLong(input)
    baseOffset = unpackLongLong(input)
    input.seek(48, 1) # 48 Unknown Bytes, Always Zeros?

    # Name Table
    curPos = input.tell()
    input.seek(namesOffset + curPos)
    nameTable = input.read(namesSize)
    input.seek(curPos)

    # Files
    for i in progressbar.progressbar(range(fileCount)):
        filename = nameTable[unpackLongLong(input):].split(b"\x00")[0].decode("utf-8")
        path = nameTable[unpackLongLong(input):].split(b"\x00")[0].decode("utf-8")
        filepath = f"{path}\\{filename}"

        dataOffset = unpackLongLong(input)
        size = unpackLongLong(input)
        compressedSize = unpackLongLong(input)
        flags = unpackLongLong(input)

        isFileAudio = any(format in filename for format in [".bnk_pad", ".wem_pad"])
        isFileCompressed = flags & 1
        if (skip_audio and isFileAudio) or (skip_compressed and isFileCompressed): continue

        curPos = input.tell()
        input.seek(dataOffset + baseOffset)
        os.makedirs(path, exist_ok=True)
        with open(filepath, "wb") as output:
            if isFileCompressed: # .gvbh_pc, .gvbm_pc(?), .fxo_dx11_pc, .fxo_dx12_pc, .fxo_vk_pc, .strh_pc
                output.write(lz4f.decompress(input.read(compressedSize), size))
            else:
                output.write(input.read(size))
        input.seek(curPos)

if __name__ == "__main__":
    cli()
