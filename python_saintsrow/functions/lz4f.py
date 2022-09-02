import lz4.frame as lz4f

def lz4fCompress(bytes):
    compressor = lz4f.LZ4FrameCompressor(block_size=lz4f.BLOCKSIZE_MAX256KB, compression_level=9, auto_flush=True)
    header = compressor.begin()
    data = compressor.compress(bytes)
    trail = b"\x00" * 4
    return b"".join([header, data, trail])
