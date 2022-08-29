from struct import unpack

def int32(bytes): return unpack("<I", bytes)[0]
def int64(bytes): return unpack("<Q", bytes)[0]

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
