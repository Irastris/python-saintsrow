import lz4.frame as lz4f

def lz4fCompress(bytes):
    compressor = lz4f.LZ4FrameCompressor(block_size=lz4f.BLOCKSIZE_MAX256KB, compression_level=9, auto_flush=True)
    header = compressor.begin()
    lz4 = compressor.compress(bytes)
    length = len(header) + len(lz4)
    return header, lz4, length
