from python_saintsrow.functions.binaryUtils import int16unpack, int32unpack, int64unpack

class SR5Archive:
    class Header:
        def __init__(self, header):
            self.magic                 = int32unpack(header[0:4])
            self.version               = int32unpack(header[4:8])
            self.crc                   = int32unpack(header[8:12])
            self.flags                 = int32unpack(header[12:16])
            self.fileCount             = int32unpack(header[16:20])
            self.dirCount              = int32unpack(header[20:24])
            self.namesOffset           = int32unpack(header[24:28])
            self.namesSize             = int32unpack(header[28:32])
            self.packSize              = int64unpack(header[32:40])
            self.uncompressedSize      = int64unpack(header[40:48])
            self.size                  = int64unpack(header[48:56])
            self.timestamp             = int64unpack(header[56:64])
            self.dataOffsetBase        = int64unpack(header[64:72])
            self.unk03                 =             header[72:120]
            self.maxAlign              = 0

    def fileTable(self, archive):
        fileTable = []
        for i in range(self.header.fileCount):
            entryOffset    = archive.tell()
            fileEntry      = archive.read(48)
            filenameOffset = int64unpack(fileEntry[0:8])
            filepathOffset = int64unpack(fileEntry[8:16])
            dataOffset     = int64unpack(fileEntry[16:24])
            size           = int64unpack(fileEntry[24:32])
            compressedSize = int64unpack(fileEntry[32:40])
            flags          = int16unpack(fileEntry[40:42])
            align          = int16unpack(fileEntry[42:44])
            unk00          = int32unpack(fileEntry[44:48])
            fileTable.append([entryOffset, filenameOffset, filepathOffset, dataOffset, size, compressedSize, flags, align, unk00])
            if align > self.header.maxAlign: self.header.maxAlign = align
        return fileTable

    def dirTable(self, archive):
        return archive.read(self.header.dirCount * 8)

    def nameTable(self, archive):
        return archive.read(self.header.namesSize)

    def parseFileTable(self):
        for i in range(self.header.fileCount):
            fStart       = self.fileTable[i][1]
            pStart       = self.fileTable[i][2]
            fEnd         = self.nameTable.find(b"\x00", fStart)
            pEnd         = self.nameTable.find(b"\x00", pStart)
            filename     = self.nameTable[fStart:fEnd].decode("utf-8")
            path         = self.nameTable[pStart:pEnd].decode("utf-8")
            if path.startswith("..\\ctg\\"): path = path[7:]
            self.fileTable[i].extend([path, filename])

    def __init__(self, archive):
        self.header = self.Header(archive.read(120))
        self.fileTable = self.fileTable(archive)
        self.dirTable = self.dirTable(archive)
        self.nameTable = self.nameTable(archive)
        self.parseFileTable()
