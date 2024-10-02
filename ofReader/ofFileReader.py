"""
Read an OpenFOAM field, e.g., a volScalarField or lagrangian fields with the 
function
   
    readOpenFOAMFile(filePath)

For e.g. a volScalarField it is often necessary to know the mesh. To read in 
the mesh the class fvMesh is provided.

"""

import numpy as np
from tqdm import tqdm
import math

# ==============================================================================
# Helper Classes 
# ==============================================================================

class ofFileFormat:
    """OpenFOAM File Format
    
    Reads the file header and stores all relevant information such as the type
    of the object to be read, e.g., scalar field, vector field, etc. or the 
    used byte size for scalar and label values.
    """
    _format : str
    _labelSize : int
    _scalarSize : int
    _type : str
    _labelByteSize : int
    _scalarByteSize : int
    _labelDataType : np.int32
    _scalarDataType : np.float64

    def __init__(self,filePath):
        self._type = "undefined"
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
                    if subStr[1] == "Cloud<passivePositionParticle>":
                        self.type = "particlePosition"
                    elif subStr[1] == "scalarField" or subStr[1] == "volScalarField":
                        self.type = "scalar"
                    elif subStr[1] == "vectorField" or subStr[1] == "volVectorField":
                        self.type = "vectorField"
                    elif subStr[1] == "labelList":
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


# ==============================================================================
# Helper Functions 
# ==============================================================================
def readOpenFOAMFile(filePath):
    fileFormat = ofFileFormat(filePath)

    data = np.zeros(1)
    if fileFormat.format == "ASCII":
        data = readASCIIDataBlock(filePath,fileFormat)
    elif fileFormat.format == "binary":
        data = readBinaryDataBlock(filePath,fileFormat)
    else:
        print("File format is undefined")
        exit(1)
    return data


def readFaceCompactList(filePath,fileFormat : ofFileFormat, binaryDataPos,nValues):
    """Function to read OpenFOAMs faceCompactIOList
    
    Reading the face compact list requires an own function, as it is stored in 
    a different format than typical vector or scalar fields. 

    First a list of start indicies is read in and then in a second step the 
    faces are constructed from the data block. 
    Note that each face can have a different number of labels, thus we cannot 
    read them in all at once. 
    See also the CompactIOList.C file of OpenFOAM. 
    """
    with open(filePath, mode='rb') as binaryFp:
        # Jump to pos
        binaryFp.seek(binaryDataPos)
        # Read the next byte and express as char
        binaryFp.read(1)
        # Discard this byte as it is the opening bracket of the data field

        # Read now all labels
        if fileFormat.labelSize == 32:
            startIndices = np.zeros(nValues,dtype=np.int32)
            startIndices = np.frombuffer(binaryFp.read(nValues*fileFormat.labelByteSize),dtype=np.int32,count=nValues)
        else:
            startIndices = np.zeros(nValues,dtype=np.int64)
            startIndices = np.frombuffer(binaryFp.read(nValues*fileFormat.labelByteSize),dtype=np.int64,count=nValues)        
        # Read closing bracket
        binaryFp.read(1)
        binaryDataPos = binaryFp.tell()

    with open(filePath, encoding='utf-8', errors='ignore') as asciiFp:
        # Jump to pos
        asciiFp.seek(binaryDataPos)
        while True:
            line = asciiFp.readline()
            if not line:
                break
            # Remove white space
            line = line.rstrip()

            # Check for beginning of the face label block
            if (line.isnumeric()):
                # Get current file position
                binaryDataPos = asciiFp.tell()
                break

    print("Allocate space for ",nValues," faces...")
    faces = [ np.zeros(1,dtype=int) for _ in range(nValues-1) ]
    print("done")
    with open(filePath, mode='rb') as binaryFp:
        # Jump to pos
        binaryFp.seek(binaryDataPos)
        binaryFp.read(1)

        # Read now all faces
        filePathParts = filePath.split('/')
        print("Reading ",filePathParts[-1])
        nFaces = nValues -1
        facesToRead = min(nFaces,500)
        readFaces = 0
        for i in tqdm(range(int(math.ceil(nFaces/facesToRead)))):
            facesToRead = min(facesToRead,nFaces-readFaces)
            nLabels = int(startIndices[readFaces+facesToRead]-startIndices[readFaces])
            buffer = np.frombuffer(binaryFp.read(nLabels*fileFormat.labelByteSize),dtype=fileFormat.labelDataType,count=nLabels)
            for j in range(readFaces,readFaces+facesToRead):
                startIndexOfBuffer = startIndices[j] - startIndices[readFaces]
                stopIndexOfBuffer = startIndices[j+1] - startIndices[readFaces]
                faces[j] = np.array(buffer[startIndexOfBuffer:stopIndexOfBuffer])
            readFaces = readFaces+facesToRead
    return faces

def readLabelField(binaryFp, fileFormat : ofFileFormat, nValues : int):
    # Set buffer length to read
    
    bufferElements = min(nValues,1000)
    readValues = 0
    data = np.zeros(nValues,dtype=fileFormat.labelDataType)
    for i in tqdm(range(int(math.ceil(nValues/bufferElements)))):
        bufferElements = min(bufferElements,nValues-readValues)
        bufferSize = bufferElements*fileFormat.labelByteSize
        data[readValues:readValues+bufferElements] = np.frombuffer(
            binaryFp.read(bufferSize),
            dtype=fileFormat.labelDataType,
            count=bufferElements)
        readValues = readValues + bufferElements
    return data


def readScalarField(binaryFp, fileFormat : ofFileFormat, nValues : int):
    # Set buffer length to read
    
    bufferElements = min(nValues,1000)
    readValues = 0
    data = np.zeros(nValues,dtype=fileFormat.scalarDataType)
    for i in tqdm(range(int(math.ceil(nValues/bufferElements)))):
        bufferElements = min(bufferElements,nValues-readValues)
        bufferSize = bufferElements*fileFormat.scalarByteSize
        data[readValues:readValues+bufferElements] = np.frombuffer(
            binaryFp.read(bufferSize),
            dtype=fileFormat.scalarDataType,
            count=bufferElements)
        readValues = readValues + bufferElements
    return data

def readVectorField(binaryFp, fileFormat : ofFileFormat, nValues : int):
    # Set buffer length to read
    
    bufferElements = min(nValues,500)
    readValues = 0
    data = np.zeros((nValues,3),dtype=fileFormat.scalarDataType)
    for i in tqdm(range(int(math.ceil(nValues/bufferElements)))):
        bufferElements = min(bufferElements,nValues-readValues)
        bufferSize = bufferElements*fileFormat.scalarByteSize
        # Each vector has three elements, thus have to read three scalars
        buffer = np.frombuffer(
            binaryFp.read(3*bufferSize),
            dtype=fileFormat.scalarDataType,
            count=3*bufferElements)
        

        data[readValues:readValues+bufferElements,:] = buffer.reshape(bufferElements,3)
        readValues = readValues + bufferElements
    return data

def readParticlePosition(binaryFp, fileFormat : ofFileFormat, nValues : int):
    # Set buffer length to read
    data = np.zeros((nValues,3),dtype=fileFormat.scalarDataType)
    for i in tqdm(range(nValues)):
        # Read first two bytes as opening bracket and new line character and discard
        binaryFp.read(2)
        data[i] = np.frombuffer(binaryFp.read(3*fileFormat.scalarByteSize),dtype=fileFormat.scalarDataType,count=3)
        
        # read integer for orig particle ID
        binaryFp.read(fileFormat.labelByteSize)
        # Read closing bracket
        binaryFp.read(1)
    return data


def readLabelFieldASCII(asciiFp, fileFormat : ofFileFormat, nValues : int):
    data = np.zeros(nValues,dtype=fileFormat.labelDataType)
    # Find opening bracket
    while True:
        line = asciiFp.readline()
        line.rstrip()
        if not line or '(' in line:
            break

    for i in range(nValues):
        line = asciiFp.readline()
        line.rstrip()
        if not line:
            break
        data[i] = fileFormat.labelDataType(line)

    return data

def readScalarFieldASCII(asciiFp, fileFormat : ofFileFormat, nValues : int):
    data = np.zeros(nValues,dtype=fileFormat.scalarDataType)
    # Find opening bracket
    while True:
        line = asciiFp.readline()
        line.rstrip()
        if not line or '(' in line:
            break

    for i in range(nValues):
        line = asciiFp.readline()
        line.rstrip()
        if not line:
            break
        data[i] = fileFormat.scalarDataType(line)

    return data

def readVectorFieldASCII(asciiFp, fileFormat : ofFileFormat, nValues : int):
    data = np.zeros((nValues,3),dtype=fileFormat.scalarDataType)
    # Find opening bracket
    while True:
        line = asciiFp.readline()
        line.rstrip()
        if not line or '(' in line:
            break

    for i in range(nValues):
        line = asciiFp.readline()
        line.rstrip()
        if not line:
            break
        
        subStr = line.split('(')
        subStr = subStr[1].split(')')
        subStr = subStr[0]
        subStr = subStr.split()
        data[i][0] = fileFormat.scalarDataType(subStr[0])
        data[i][1] = fileFormat.scalarDataType(subStr[1])
        data[i][2] = fileFormat.scalarDataType(subStr[2])

    return data

def readFaceList(asciiFp, fileFormat : ofFileFormat, nValues : int):
    faces = [ np.zeros(1,dtype=fileFormat.labelDataType) for _ in range(nValues) ]
    # Find opening bracket
    while True:
        line = asciiFp.readline()
        line.rstrip()
        if not line or '(' in line:
            break

    for i in range(nValues):
        line = asciiFp.readline()
        line.rstrip()
        if not line:
            break
        
        subStr = line.split('(')
        subStr = subStr[1].split(')')
        subStr = subStr[0]
        subStr = subStr.split()
        face = np.zeros(len(subStr),dtype=fileFormat.labelDataType)
        for j in range(len(subStr)):
            face[j] = fileFormat.labelDataType(subStr[j])
        faces[i] = face
    return faces

def readParticlePositionASCII(binaryFp, fileFormat : ofFileFormat, nValues : int):
    print("Not defined")
    exit()



def readBinaryDataBlock(filePath,fileFormat : ofFileFormat):
    # Find how many values have to be read
    data = np.zeros(1)
    nValues = 0
    binaryDataPos = 0
    with open(filePath, encoding='utf-8', errors='ignore') as fp:    
        while True:
            line = fp.readline()
            if not line:
                break
            # Remove white space
            line = line.rstrip()

            # Check for beginning of block
            if (line.isnumeric()):
                nValues = int(line)
                # Get current file position
                binaryDataPos = fp.tell()
                break
    
    if fileFormat.type == "faceCompactList":
        return readFaceCompactList(filePath,fileFormat,binaryDataPos,nValues)
    else:
        with open(filePath, mode='rb') as binaryFp:
            # Jump to pos
            binaryFp.seek(binaryDataPos)
            # Read the next byte and express as char
            binaryFp.read(1)
            # Discard this byte as it is the opening bracket of the data field

            if fileFormat.type == "scalar":
                data = np.zeros(nValues)    
            elif fileFormat.type == "label":
                data = np.zeros(nValues,dtype=int)
            elif fileFormat.type == "vectorField" or fileFormat.type ==  "particlePosition":
                data = np.zeros((nValues,3)) 
            
            filePathParts = filePath.split('/')
            print("Reading ",filePathParts[-1])

            if fileFormat.type == "scalar":
                data = readScalarField(binaryFp,fileFormat,nValues)
            elif fileFormat.type == "label":
                data = readLabelField(binaryFp,fileFormat,nValues)
            elif fileFormat.type == 'vectorField':           
                data = readVectorField(binaryFp,fileFormat,nValues)
            elif fileFormat.type == "particlePosition":
                data = readParticlePosition(binaryFp,fileFormat,nValues)
            else:
                print("Unknown data type: ",fileFormat.type)
                exit()
    return data


def readASCIIDataBlock(filePath,fileFormat : ofFileFormat):
    # Read the file until closing bracket
    with open(filePath, encoding='utf-8', errors='ignore') as fp:

        # Number of values to read
        while True:
            line = fp.readline()
            if not line:
                break
            # Remove white space
            line = line.rstrip()

            # Check for beginning of block
            if (line.isnumeric()):
                nValues = int(line)
                break
        
        # Discard this byte as it is the opening bracket of the data field

        if fileFormat.type == "scalar":
            data = np.zeros(nValues)    
        elif fileFormat.type == "label":
            data = np.zeros(nValues,dtype=int)
        elif fileFormat.type == "vectorField" or fileFormat.type ==  "particlePosition":
            data = np.zeros((nValues,3)) 
        
        filePathParts = filePath.split('/')
        print("Reading ",filePathParts[-1])

        if fileFormat.type == "scalar":
            data = readScalarFieldASCII(fp,fileFormat,nValues)
        elif fileFormat.type == "label":
            data = readLabelFieldASCII(fp,fileFormat,nValues)
        elif fileFormat.type == 'vectorField':           
            data = readVectorFieldASCII(fp,fileFormat,nValues)
        elif fileFormat.type == 'faceList':           
            data = readFaceList(fp,fileFormat,nValues)
        elif fileFormat.type == "particlePosition":
            data = readParticlePositionASCII(fp,fileFormat,nValues)
        else:
            print("Unknown data type: ",fileFormat.type)
            exit()
    return data
                


