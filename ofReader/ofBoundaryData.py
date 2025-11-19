import numpy as np
from ofReader.ofFileFormat import ofFileFormat
from ofReader.ofReadSupportFunctions import *
import os.path as path
from io import StringIO


class ofBoundaryData:

    def _read_ascii_line(self,fp):
        """
        Read one ASCII line from a binary file pointer fp.
        Returns: line and if EoF

        line, EoF = _read_ascii_line(fp)
        """
        if self._file_format.format == "binary":
            raw = fp.readline()  # raw bytes including newline, b'' at EOF
            if raw == b"":
                return None, True  # True EOF
            line = raw.decode("utf-8", errors="ignore").rstrip("\r\n")
            return line, False
        else:
            line = fp.readline()
            if not line:
                return line, True
            return line, False


    def _readPatch(self,fp):
        """Reads the patch information containing the patch name, type and value

        Returns a tuple of first if a patch could be read and second the 
        patch itself.
        """

        patch_data = np.zeros(1)
        patch_name = "default"
        patch_type = "empty"

        # Read the patch name
        while (True):
            line,eof = self._read_ascii_line(fp)
            if eof:
                raise EOFError("EOF read -- invalid boundaryField")
            
            stripped = line.strip()
            if stripped == "}":
                return False,Patch(patch_name)
            
            if stripped != "":
                patch_name = stripped.rstrip(';')
                break

        # Read the patch type
        while (True):
            line,eof = self._read_ascii_line(fp)
            if eof:
                raise EOFError("EOF read -- invalid boundaryField")

            stripped = line.strip()

            if stripped == "}":
                return False,Patch(patch_name)

            if stripped.startswith("type"):
                parts = stripped.split()
                patch_type = parts[1].rstrip(";")
                break

        # Read the patch value
        uniform_value = True
        while (True):
            line,eof = self._read_ascii_line(fp)
            if eof:
                raise EOFError("EOF read -- invalid boundaryField")

            stripped = line.strip()

            if stripped == "}":
                p = Patch(patch_name)
                p.type = patch_type
                return False,p

            if stripped.startswith("value"):
                if "nonuniform" in stripped:
                    uniform_value = False
                break
        
        if not uniform_value:
            if self._file_format.format == "binary":
                patch_data = readBinaryDataBlock(fp,self._file_format)
            else:
                patch_data = readASCIIDataBlock(fp,self._file_format)


        # Create the Patch
        patch = Patch(patch_name)
        patch.type = patch_type
        patch.data = patch_data

        return True,patch


    def __init__(self):
        self._patches = {}


    # Access
    @property
    def patches(self):
        return self._patches

    
    def read(self,fp,file_format : ofFileFormat):
        """Read the boundary data block from a given file with the 
        ofFileFormat to get the binary or ascii settings
        """
        self._contains_boundary = False
        self._file_format = file_format
        

        # Read till boundary field keyword is found
        while (True):
            line,eof = self._read_ascii_line(fp)
            if eof:
                raise EOFError("EOF before boundaryField entry")

            if line.rstrip() == "boundaryField":
                break
        
        while (True):
            line,eof = self._read_ascii_line(fp)
            if eof:
                raise EOFError("EOF before opening bracket of boundaryField entry")
            
            if line.rstrip() == "{":
                break

        while(True):
            valid_patch, patch = self._readPatch(fp)
            if not valid_patch:
                break
            self._patches[patch.name] = patch




# ==============================================================================
#                           Patch Types
# ==============================================================================

class Patch:
    def __init__(self,name):
        self.name = name
        self.type = "empty"
        self.data = np.zeros(1)

    def write(self,buffer : StringIO):
        buffer.write(f"\t{self.name}\n")
        buffer.write("\t{\n")
        buffer.write(f"\t\ttype\t{self.type};\n")
        self._writePatchProperties(buffer)
        buffer.write("\t}\n")
    
    def _writePatchProperties(self,buffer : StringIO):
        buffer.write("")


class Cyclic_Patch(Patch):
    def __init__(self,name):
        super().__init__(name)
        self.type = "cyclic"

    def _writePatchProperties(self,buffer : StringIO):
        buffer.write("")

class Empty_Patch(Patch):
    def __init__(self,name):
        super().__init__(name)
        self.type = "empty"

class Calculated_Patch(Patch):
    def __init__(self,name):
        super().__init__(name)
        self.type = "calculated"


class WaveTransmissive_Patch(Patch):
    def __init__(self,name):
        super().__init__(name)
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