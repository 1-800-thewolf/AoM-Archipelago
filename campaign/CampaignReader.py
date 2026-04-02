
import os
from pathlib import Path
import struct

DE_DEPENDENCY_NUM = 7
RGE_DE2_MAX_CHAR = 256

RGE_STRING_ID = 0x0A60

class CpnHeader:
    version: int
    name: str
    scenarioNum: int
    
    def __init__(self, fp):
        self.version = struct.unpack("i", fp.read(4))[0]
        junk = struct.unpack("iiiiiii", fp.read(DE_DEPENDENCY_NUM*4))
        self.name = struct.unpack(f"{str(RGE_DE2_MAX_CHAR)}s", fp.read(RGE_DE2_MAX_CHAR))[0]
        self.scenarioNum = struct.unpack("i", fp.read(4))[0]
    
class Scenario:
    size: int
    offset: int
    name: str
    nameLen: int
    fileName: str
    outfilename: str
    xsdatname: str
    fileNameLen: int
    
    def __init__(self, fp):
        self.size = struct.unpack("i", fp.read(4))[0]
        self.offset = struct.unpack("i", fp.read(4))[0]
        de_str = struct.unpack("H", fp.read(2))[0]
        self.nameLen = struct.unpack("H", fp.read(2))[0]
        self.name = struct.unpack(f"{str(self.nameLen)}s", fp.read(self.nameLen))[0]
        de_str = struct.unpack("H", fp.read(2))[0]
        self.fileNameLen = struct.unpack("H", fp.read(2))[0]
        self.fileName = (struct.unpack(f"{str(self.fileNameLen)}s", fp.read(self.fileNameLen))[0]).decode("utf-8")
        self.outfilename = "out" + self.fileName
        self.xsdatname = Path(self.outfilename).stem + ".xsdat"
        
        
        

class Campaign:
    header: CpnHeader
    scenarios: list[Scenario] = []
    
    def __init__(self, filename: str, outFolder: str):
        with open(filename, "rb") as fp:
            self.header = CpnHeader(fp)
            
            for x in range(self.header.scenarioNum):
                scn = Scenario(fp)
                self.scenarios.append(scn)
            
            os.makedirs(outFolder, exist_ok=True)
            
            for scn in self.scenarios:
                with open(f"{outFolder}\\{scn.fileName}", "wb") as out:
                    fp.seek(scn.offset)
                    scnFile = fp.read(scn.size)
                    out.write(scnFile)