from struct import pack, unpack

def int16unpack(bytes): return unpack("<H", bytes)[0]
def int32unpack(bytes): return unpack("<L", bytes)[0]
def int64unpack(bytes): return unpack("<Q", bytes)[0]

def int32pack(int): return pack("<L", int)
def int64pack(int): return pack("<Q", int)
