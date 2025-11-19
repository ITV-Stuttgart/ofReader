import numpy as np

# ==============================================================================
# Helper Classes 
# ==============================================================================

class ofFileFormat:
    """OpenFOAM File Format
    
    Reads the file header and stores all relevant information such as the type
    of the object to be read, e.g., scalar field, vector field, etc. or the 
    used byte size for scalar and label values.
    """

    def __init__(self):
        # Member variables
        self._format : str = "ASCII"
        self._labelSize : int = 32
        self._scalarSize : int = 64
        self._fieldType : str = "undefined"
        self._type : str = "undefined"
        self._labelByteSize : int = 0
        self._scalarByteSize : int = 0
        self._labelDataType : type = np.int32
        self._scalarDataType : type = np.float64

    def readFile(self,filePath):
        self._type = "undefined"
        # Default label size
        self.labelSize = 32
        self.scalarSize = 64
        with open(filePath, encoding='utf-8', errors='ignore') as fp:
            for line in fp:
                # Find the keyword format
                if "format" in line:
                    # Read the keyword
                    subStr = line.split()
                    subStr[1]=subStr[1].rstrip(';')
                    if subStr[1] == "binary":
                        self.format = "binary"
                    else:
                        self.format = "ASCII"
                if "class" in line:
                    # Read the keyword
                    subStr = line.split()
                    subStr[1]=subStr[1].rstrip(';')
                    if subStr[1] == "Cloud<passivePositionParticle>" or subStr[1] == "Cloud<passiveParticle>":
                        self.type = "particlePosition"
                    elif subStr[1] == "scalarField":
                        self.type = "scalar"
                    elif subStr[1] == "volScalarField":
                        self.type = "scalar"
                        self._fieldType = "volField"
                    elif subStr[1] == "vectorField":
                        self.type = "vectorField"
                    elif subStr[1] == "volVectorField":
                        self.type = "vectorField"
                        self._fieldType = "volField"
                    elif subStr[1] == "labelList" or subStr[1] == "labelField":
                        self.type = "label"
                    elif subStr[1] == "faceCompactList":
                        self.type = "faceCompactList"
                    elif subStr[1] == "faceList":
                        self.type = "faceList"
                if "arch" in line:
                    subStr    = line.split()
                    valueString = subStr[1].rstrip(';')
                    labelPos = valueString.find("label")
                    scalarPos = valueString.find("scalar")
                    if labelPos != -1:
                        temp = valueString[labelPos:-1]
                        temp = temp.split('=')
                        self.labelSize = temp[1][0:2]
                    if scalarPos != -1:
                        temp = valueString[scalarPos:-1]
                        temp = temp.split('=')
                        self.scalarSize = temp[1][0:2]
                if "}" in line:
                    break

    # Access
    @property
    def format(self):
        return self._format
    
    @property
    def labelSize(self):
        return self._labelSize
    
    @property
    def scalarSize(self):
        return self._scalarSize
    
    @property
    def type(self):
        return self._type
    
    @property
    def labelByteSize(self):
        return self._labelByteSize
    @property
    def scalarByteSize(self):
        return self._scalarByteSize
    
    @property
    def labelDataType(self):
        return self._labelDataType
    
    @property
    def scalarDataType(self):
        return self._scalarDataType

    @property
    def fieldType(self):
        return self._fieldType

    
    # Modify
    @format.setter
    def format(self,newFormat : str):
        self._format = newFormat

    @labelSize.setter
    def labelSize(self,newLabelSize):
        self._labelSize = int(newLabelSize)
        self._labelByteSize = int(self._labelSize/8)
        if self._labelSize == 32:
            self._labelDataType = np.int32
        elif self._labelSize == 64:
            self._labelDataType = np.int64

    @scalarSize.setter
    def scalarSize(self,newScalarSize):
        self._scalarSize = int(newScalarSize)
        self._scalarByteSize = int(self._scalarSize/8)
        if self._scalarSize == 32:
            self._scalarDataType = np.float32
        elif self._scalarSize == 64:
            self._scalarDataType = np.float64

    @type.setter
    def type(self,newType : str):
        self._type = newType


    def __repr__(self):
        outputStr = ["format:     " + str(self._format),
                     "type:       " + str(self._type),
                     "scalarSize: " + str(self._scalarSize),
                     "labelSize:  " + str(self._labelSize)]
        return '\n'.join(outputStr)
