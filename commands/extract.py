from concurrent.futures import ThreadPoolExecutor, as_completed

import click
import progressbar

from classes.SR5Archive import SR5Archive
from functions.threadedExtractor import threadedExtractor

@click.command()
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
