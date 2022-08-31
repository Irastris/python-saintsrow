from pathlib import Path

import lz4.frame as lz4f

def threadedExtractor(archive:Path, dataOffset:int, size:int, compressedSize:int, flags:int, path:Path, filename:Path):
    filepath = Path(f"{path}\\{filename}")
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(archive, "rb") as input, open(filepath, "wb") as output:
        input.seek(dataOffset)
        if flags & 1:
            output.write(input.read(compressedSize)) # output.write(lz4f.decompress(input.read(compressedSize), size))
        else:
            output.write(input.read(size))
    return
