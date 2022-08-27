from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from struct import unpack

import lz4.frame as lz4f
import click
import progressbar

def int32(bytes): return unpack("<I", bytes)[0]
def int64(bytes): return unpack("<Q", bytes)[0]

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
@click.option("-sAn", "--skip-animation", is_flag=True, help="Skip extracting animation data")
@click.option("-sAr", "--skip-archive", is_flag=True, help="Skip extracting archive data")
@click.option("-sAu", "--skip-audio", is_flag=True, help="Skip extracting audio data")
@click.option("-sMe", "--skip-mesh", is_flag=True, help="Skip extracting mesh data")
@click.option("-sMo", "--skip-morph", is_flag=True, help="Skip extracting morph data")
@click.option("-sP", "--skip-prefab", is_flag=True, help="Skip extracting prefab data")
@click.option("-sT", "--skip-texture", is_flag=True, help="Skip extracting texture data")
@click.option("-sV", "--skip-video", is_flag=True, help="Skip extracting video data")
@click.argument("input", type=click.Path())
def extract(input, skip_animation, skip_archive, skip_audio, skip_mesh, skip_morph, skip_prefab, skip_texture, skip_video):
    """Extract a .vpp_pc or .str2_pc archive."""
    widgets = ["", progressbar.SimpleProgress(), "", progressbar.PercentageLabelBar(), " ", progressbar.AdaptiveETA()]
    with open(input, "rb") as archive:
        # Header
        header      = archive.read(120)
        magic       = int32(header[0:4])
        if magic != 1367935694: exit("Magic is incorrect, unsupported input!")
        # version   = int32(header[4:8])
        # unk01     =       header[8:16]
        fileCount   = int32(header[16:20])
        # unk02     =       header[20:24]
        namesOffset = int32(header[24:28])
        namesSize   = int32(header[28:32])
        # packSize  = int64(header[32:40])
        # unk03     =       header[40:48]
        # dataSize  = int64(header[48:56])
        # timestamp = int64(header[56:64])
        baseOffset  = int64(header[64:72])
        # unk03     =       header[72:120]

        # File Table
        fileTable = []
        widgets[0], widgets[2] = "Reading ", " File Entries "
        for i in progressbar.progressbar(range(fileCount), widgets=widgets):
            fileEntry      = archive.read(48)
            filenameOffset = int64(fileEntry[0:8])
            filepathOffset = int64(fileEntry[8:16])
            dataOffset     = int64(fileEntry[16:24])
            size           = int64(fileEntry[24:32])
            compressedSize = int64(fileEntry[32:40])
            flags          = int64(fileEntry[40:48])
            fileTable.append([dataOffset, size, compressedSize, flags, filenameOffset, filepathOffset])
        del filenameOffset, filepathOffset, dataOffset, size, compressedSize, flags

        # Name Table
        archive.seek(120 + namesOffset)
        nameTable = archive.read(namesSize)

    # Parse Name Table
    widgets[0], widgets[2] = "Parsing ", " Names "
    for i in progressbar.progressbar(range(fileCount), widgets=widgets):
        fStart       = fileTable[i][4]
        pStart       = fileTable[i][5]
        fEnd         = nameTable.find(b"\x00", fileTable[i][4])
        pEnd         = nameTable.find(b"\x00", fileTable[i][5])
        filename     = nameTable[fStart:fEnd].decode("utf-8")
        path         = nameTable[pStart:pEnd].decode("utf-8")

        # Skip Excluded Formats
        isFileAnimation = ".anim_pad" in filename
        isFileMorph     = ".cmorph_pc" in filename
        isFileVideo     = ".bk2" in filename
        isFileArchive   = any(format in filename for format in [".str2_pc", ".vpp_pc"])
        isFileAudio     = any(format in filename for format in [".bnk_pad", ".wem_pad"])
        isFileMesh      = any(format in filename for format in [".cmesh_pc", ".gmesh_pc"])
        isFilePrefab    = any(format in filename for format in [".cprefab_pc", ".gprefab_pc", ".hprefab_pc"])
        isFileTexture   = any(format in filename for format in [".cvbm_pc", ".gvbh_pc", ".gvbm_pc"])
        if (
            ( skip_animation and isFileAnimation ) or
            ( skip_archive   and isFileArchive   ) or
            ( skip_audio     and isFileAudio     ) or
            ( skip_morph     and isFileMorph     ) or
            ( skip_prefab    and isFilePrefab    ) or
            ( skip_texture   and isFileTexture   ) or
            ( skip_video     and isFileVideo     )
        ):
            fileTable[i] = None
            continue

        fileTable[i] = fileTable[i][:-2]
        fileTable[i].extend([path, filename])
    fileTable = list(filter(None, fileTable))
    del isFileAnimation, isFileMorph, isFileVideo, isFileArchive, isFileAudio, isFileMesh, isFilePrefab, isFileTexture
    del filename, path, nameTable

    # Extract Files
    with ThreadPoolExecutor() as pool:
        threads = []
        for i in range(len(fileTable)):
            dataOffset      = fileTable[i][0]
            size            = fileTable[i][1]
            compressedSize  = fileTable[i][2]
            flags           = fileTable[i][3]
            path            = fileTable[i][4]
            filename        = fileTable[i][5]

            thread = pool.submit(threadedExtractor, input, dataOffset + baseOffset, size, compressedSize, flags, path, filename)
            threads.append(thread)

        widgets[0], widgets[2] = "Extracting ", " Files "
        for thread in progressbar.progressbar(as_completed(threads), widgets=widgets, max_value=len(fileTable)):
            thread.result()

if __name__ == "__main__":
    cli()
