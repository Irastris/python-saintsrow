from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from struct import unpack

import lz4.frame as lz4f
import click
import progressbar

class SR5Archive:
    class Header:
        def __init__(self, header):
            self.magic                 = int32(header[0:4])
            self.version               = int32(header[4:8])
            self.crc                   = int32(header[8:12])
            self.flags                 = int32(header[12:16])
            self.fileCount             = int32(header[16:20])
            self.dirCount              = int32(header[20:24])
            self.namesOffset           = int32(header[24:28])
            self.namesSize             = int32(header[28:32])
            self.packSize              = int64(header[32:40])
            self.uncompressedSize      = int64(header[40:48])
            self.size                  = int64(header[48:56])
            self.timestamp             = int64(header[56:64])
            self.dataOffsetBase        = int64(header[64:72])
            self.unk03                 =       header[72:120]

    def fileTable(self, archive):
        fileTable = []
        for i in range(self.header.fileCount):
            entryOffset    = archive.tell()
            fileEntry      = archive.read(48)
            filenameOffset = int64(fileEntry[0:8])
            filepathOffset = int64(fileEntry[8:16])
            dataOffset     = int64(fileEntry[16:24])
            size           = int64(fileEntry[24:32])
            compressedSize = int64(fileEntry[32:40])
            flags          = int64(fileEntry[40:48])
            fileTable.append([entryOffset, dataOffset, size, compressedSize, flags, filenameOffset, filepathOffset])
        return fileTable

    def nameTable(self, archive):
        archive.seek(120 + self.header.namesOffset)
        return archive.read(self.header.namesSize)

    def parseFileTable(self):
        for i in range(self.header.fileCount):
            fStart       = self.fileTable[i][5]
            pStart       = self.fileTable[i][6]
            fEnd         = self.nameTable.find(b"\x00", self.fileTable[i][5])
            pEnd         = self.nameTable.find(b"\x00", self.fileTable[i][6])
            filename     = self.nameTable[fStart:fEnd].decode("utf-8")
            path         = self.nameTable[pStart:pEnd].decode("utf-8")
            self.fileTable[i] = self.fileTable[i][:-2]
            self.fileTable[i].extend([path, filename])

    def __init__(self, archive):
        self.header = self.Header(archive.read(120))
        self.fileTable = self.fileTable(archive)
        self.nameTable = self.nameTable(archive)
        self.parseFileTable()

def int32(bytes): return unpack("<I", bytes)[0]
def int64(bytes): return unpack("<Q", bytes)[0]

def printEntryInfo(entry, dataOffsetBase):
    print("")
    print(f"Entry Offset:    {entry[0]}")
    print(f"Filename:        {entry[6]}")
    print(f"Path:            {entry[5]}")
    print(f"Data Offset:     {entry[1]} ({entry[1] + dataOffsetBase})")
    print(f"Size:            {entry[2]}")
    print(f"Compressed Size: {entry[3]}")
    print(f"Flags:           {entry[4]}")

def threadedExtractor(archive:Path, dataOffset:int, size:int, compressedSize:int, flags:int, path:Path, filename:Path):
    filepath = Path(f"{path}\\{filename}")
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(archive, "rb") as input, open(filepath, "wb") as output:
        input.seek(dataOffset)
        if flags & 1:
            output.write(lz4f.decompress(input.read(compressedSize), size))
        else:
            output.write(input.read(size))
    return

@click.group()
def cli():
    pass

@cli.command()
@click.option("-e", "--extract", is_flag=True, help="Extract matching file(s)")
@click.option("-q", "--query", type=str, required=True, help="String to search for")
@click.argument("input", type=click.Path())
def search(input, query, extract):
    """Search (and optionally extract) a .vpp_pc or .str2_pc archive."""
    with open(input, "rb") as inputFile:
        archive = SR5Archive(inputFile)

    # Search Files
    matches = []
    for i in range(len(archive.fileTable)):
        if query in archive.fileTable[i][6]:
            matches.append(archive.fileTable[i])

    # Print Matches
    for match in matches:
        printEntryInfo(match, archive.header.dataOffsetBase)
        if extract:
            threadedExtractor(input, match[1] + archive.header.dataOffsetBase, match[2], match[3], match[4], match[5], match[6]) # No need to actually thread
            print("Extracted")

@cli.command()
@click.option("-sAn", "--skip-animation", is_flag=True, help="Skip extracting animation data")
@click.option("-sAr", "--skip-archive", is_flag=True, help="Skip extracting archive data")
@click.option("-sAu", "--skip-audio", is_flag=True, help="Skip extracting audio data")
@click.option("-sMe", "--skip-mesh", is_flag=True, help="Skip extracting mesh data")
@click.option("-sMo", "--skip-morph", is_flag=True, help="Skip extracting morph data")
@click.option("-sP", "--skip-prefab", is_flag=True, help="Skip extracting prefab data")
@click.option("-sT", "--skip-texture", is_flag=True, help="Skip extracting texture data")
@click.option("-sV", "--skip-video", is_flag=True, help="Skip extracting video data")
@click.option("-sX", "--skip-xml", is_flag=True, help="Skip extracting XML data")
@click.argument("input", type=click.Path())
def extract(input, skip_animation, skip_archive, skip_audio, skip_mesh, skip_morph, skip_prefab, skip_texture, skip_video, skip_xml):
    """Extract a .vpp_pc or .str2_pc archive."""
    print("")
    with open(input, "rb") as inputFile:
        archive = SR5Archive(inputFile)

    # Skip Excluded Formats
    for i in range(archive.header.fileCount):
        isFileAnimation = ".anim_pad" in archive.fileTable[i][6]
        isFileMorph     = ".cmorph_pc" in archive.fileTable[i][6]
        isFileVideo     = ".bk2" in archive.fileTable[i][6]
        isFileArchive   = any(format in archive.fileTable[i][6] for format in [".str2_pc", ".vpp_pc"])
        isFileAudio     = any(format in archive.fileTable[i][6] for format in [".bnk_pad", ".wem_pad"])
        isFileMesh      = any(format in archive.fileTable[i][6] for format in [".cmesh_pc", ".gmesh_pc"])
        isFilePrefab    = any(format in archive.fileTable[i][6] for format in [".cprefab_pc", ".gprefab_pc", ".hprefab_pc"])
        isFileTexture   = any(format in archive.fileTable[i][6] for format in [".cvbm_pc", ".gvbh_pc", ".gvbm_pc"])
        isFileXML       = any(format in archive.fileTable[i][6] for format in [".vint_proj", ".vpkg", ".xml"])
        if (
            ( skip_animation and isFileAnimation ) or
            ( skip_archive   and isFileArchive   ) or
            ( skip_audio     and isFileAudio     ) or
            ( skip_morph     and isFileMorph     ) or
            ( skip_prefab    and isFilePrefab    ) or
            ( skip_texture   and isFileTexture   ) or
            ( skip_video     and isFileVideo     ) or
            ( skip_xml       and isFileXML       )
        ):
            archive.fileTable[i] = None
    archive.fileTable = list(filter(None, archive.fileTable))

    # Extract Files
    filesExtracted = 0
    widgets = ["Extracting Files (", progressbar.SimpleProgress(), ") ", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]
    with ThreadPoolExecutor() as pool, progressbar.ProgressBar(widgets=widgets, max_value=len(archive.fileTable)) as bar:
        threads = []

        for i in range(len(archive.fileTable)):
            dataOffset      = archive.fileTable[i][1]
            size            = archive.fileTable[i][2]
            compressedSize  = archive.fileTable[i][3]
            flags           = archive.fileTable[i][4]
            path            = archive.fileTable[i][5]
            filename        = archive.fileTable[i][6]

            thread = pool.submit(threadedExtractor, input, dataOffset + archive.header.dataOffsetBase, size, compressedSize, flags, path, filename)
            threads.append(thread)

        for thread in as_completed(threads):
            thread.result()
            filesExtracted += 1
            bar.update(filesExtracted)

if __name__ == "__main__":
    cli()
