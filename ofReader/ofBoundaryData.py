import numpy as np
from ofReader.ofFileReader import ofFileFormat
import os.path as path
from io import StringIO


class ofBoundaryData:

    def __init__(self):
        self._patches = []

    def addPatch(self,patchName,patchType):
        if patchType == "cyclic":
            self._patches.append(_cyclic(patchName))
            return self._patches[-1]
        if patchType == "waveTransmissive":
            self._patches.append(_waveTransmissive(patchName))
            return self._patches[-1]
        else:
            self._patches.append(_empty(patchName))
            return self._patches[-1]
        
    def write(self,filePath):
        f = open(filePath, "a")
        buffer = StringIO()
        buffer.write("boundaryField\n")
        buffer.write("{\n")
        for p in self._patches:
            p.write(buffer)
        buffer.write("}\n")
        f.write(buffer.getvalue())
        f.close()

# ==============================================================================
#                           Patch Types
# ==============================================================================

class _patch:
    def __init__(self):
        self.name = "default"
        self.type = "empty"

    def write(self,buffer : StringIO):
        buffer.write(f"\t{self.name}\n")
        buffer.write("\t{\n")
        buffer.write(f"\t\ttype\t{self.type};\n")
        self._writePatchProperties(buffer)
        buffer.write("\t}\n")
    
    def _writePatchProperties(self,buffer : StringIO):
        buffer.write("")


class _cyclic(_patch):
    def __init__(self,name):
        self.name = name
        self.type = "cyclic"

    def _writePatchProperties(self,buffer : StringIO):
        buffer.write("")

class _empty(_patch):
    def __init__(self,name):
        self.name = name
        self.type = "empty"

class _waveTransmissive(_patch):
    def __init__(self,name):
        self.name = name
        self.type = "waveTransmissive"
        self.gamma = 1.0
        self.fieldInf = np.zeros(1)
        self.lInf = 0
        self.value = np.zeros(1)

    def _writePatchProperties(self,buffer : StringIO):
        buffer.write(f"\t\tgamma\t{self.gamma:f};\n")
        buffer.write(f"\t\tfieldInf\t")
        if len(self.fieldInf) > 1:
            buffer.write("(")
            for i in range(len(self.fieldInf)-1):
                buffer.write(f"{self.fieldInf[i]:f} ")
            buffer.write(f"{self.fieldInf[-1]:f});\n")
        else:
            buffer.write(f"{self.fieldInf};\n")
        buffer.write(f"\t\tlInf\t{self.lInf:f};\n")
        buffer.write(f"\t\tvalue\tuniform ")
        if len(self.value) > 1:
            buffer.write("(")
            for i in range(len(self.value)-1):
                buffer.write(f"{self.value[i]:f} ")
            buffer.write(f"{self.value[-1]:f});\n")
        else:
            buffer.write(f"{self.value};\n")