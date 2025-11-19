import numpy as np
from tqdm import tqdm
import math
import sys
import os
import io
from ofReader.ofFileFormat import ofFileFormat

def has_processors_dir(path):
    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        if os.path.isdir(full_path) and name.startswith("processors"):
            return True, name
    return False, "processor0"


def readFaceCompactList(binaryFp, fileFormat : ofFileFormat, binaryDataPos,nValues):
    """Function to read OpenFOAMs faceCompactIOList
    
    Reading the face compact list requires an own function, as it is stored in 
    a different format than typical vector or scalar fields. 

    First a list of start indicies is read in and then in a second step the 
    faces are constructed from the data block. 
    Note that each face can have a different number of labels, thus we cannot 
    read them in all at once. 
    See also the CompactIOList.C file of OpenFOAM. 
    """

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

    ascii_reader = io.TextIOWrapper(binaryFp, encoding='utf-8', errors='ignore')

    while True:
        line = ascii_reader.readline()
        if not line:
            break
        # Remove white space
        line = line.rstrip()

        # Check for beginning of the face label block
        if (line.isnumeric()):
            break

    ascii_reader.detach()

    print("Allocate space for ",nValues," faces...")
    faces = np.empty((nValues-1),dtype=object)
    print("done")

    binaryFp.read(1)

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

def readParticlePositionASCII(asciiFp, fileFormat : ofFileFormat, nValues : int):
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
        # Break line in parts
        subStr = line.split('(')
        subStr = subStr[1].split(')')
        subStr = subStr[0].split()
        data[i][0] = fileFormat.scalarDataType(subStr[0])
        data[i][1] = fileFormat.scalarDataType(subStr[1])
        data[i][2] = fileFormat.scalarDataType(subStr[2])

    return data



def readBinaryDataBlock(binaryFp,fileFormat : ofFileFormat):
    # Find how many values have to be read
    data = np.zeros(1)
    nValues = 0
    binaryDataPos = 0

    def read_ascii_line():
        """Read one ASCII line safely from the binary file.
        Returns:
            (line, raw)
            line = decoded string without newline
            raw  = original raw bytes (None if EOF)
        """
        raw = binaryFp.readline()       # raw bytes including newline, or b'' at EOF
        if raw == b"":                  # TRUE EOF
            return None, None
        line = raw.decode('utf-8', errors='ignore').rstrip('\r\n')
        return line, raw

    while True:
        line, raw = read_ascii_line()

        if raw is None:            # REAL EOF (not blank line!)
            raise EOFError("Reached end of file before finding nValues is found")

        stripped = line.strip()

        # Check for beginning of block
        if (line.isnumeric()):
            nValues = int(line)
            break


    if fileFormat.type == "faceCompactList":
        return readFaceCompactList(binaryFp,fileFormat,binaryDataPos,nValues)
    else:
        # Read the next byte and express as char
        binaryFp.read(1)
        # Discard this byte as it is the opening bracket of the data field

        if fileFormat.type == "scalar":
            data = np.zeros(nValues)    
        elif fileFormat.type == "label":
            data = np.zeros(nValues,dtype=int)
        elif fileFormat.type == "vectorField" or fileFormat.type ==  "particlePosition":
            data = np.zeros((nValues,3)) 

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
            sys.exit("Error reading: "+binaryFp.name())
    return data


def readASCIIDataBlock(asciiFp,fileFormat : ofFileFormat):
    data = np.zeros(1)

    # Number of values to read
    while True:
        line = asciiFp.readline()

        # Remove white space
        line = line.rstrip()

        if (line.isnumeric()):
            nValues = int(line)
            break

    if fileFormat.type == "scalar":
        data = readScalarFieldASCII(asciiFp,fileFormat,nValues)
    elif fileFormat.type == "label":
        data = readLabelFieldASCII(asciiFp,fileFormat,nValues)
    elif fileFormat.type == 'vectorField':       
        data = readVectorFieldASCII(asciiFp,fileFormat,nValues)
    elif fileFormat.type == 'faceList':           
        data = readFaceList(asciiFp,fileFormat,nValues)
    elif fileFormat.type == "particlePosition":
        data = readParticlePositionASCII(asciiFp,fileFormat,nValues)
    else:
        print("Unknown data type: ",fileFormat.type)
        sys.exit("Error reading: "+asciiFp.name())
    return data


def readASCIIInternalField(asciiFp, file_format : ofFileFormat):
    """Read the internal field of a volField"""
    data = np.zeros(1)
    for line in asciiFp:
        line = line.rstrip()
        if "internalField" in line:
            # First try to split the line
            line_parts = line.split()
            if line_parts[1] == "uniform":
                if file_format.type == "vector" or file_format.type == "vectorField":
                    data = np.zeros((1,3),dtype=file_format.scalarDataType)
                    vector_parts = line_parts[2:]
                    
                    data[0,0] = file_format.scalarDataType(vector_parts[0].strip('();'))
                    data[0,1] = file_format.scalarDataType(vector_parts[1].strip('();'))
                    data[0,2] = file_format.scalarDataType(vector_parts[2].strip('();'))
                    break
                if file_format.type == "scalar":
                    data = np.zeros(1,dtype=file_format.scalarDataType)
                    scalar = line_parts[2].split(';')[0]
                    data = file_format.scalarDataType(scalar)
                    break
            else:
                data = readASCIIDataBlock(asciiFp,file_format)
    return data


def readBinaryInternalField(binaryFp, file_format : ofFileFormat):
    """
    Read the ASCII header up to the internalField line from the binary file object `binaryFp`.
    This function uses binaryFp.readline() to avoid TextIOWrapper read-ahead buffering.
    After this function finds the internalField line it leaves binaryFp positioned
    at the start of the next line (so readBinaryDataBlock can read the ASCII count + binary block).

    Arguments
    - binaryFp: a binary file-like object opened in 'rb' mode, seekable.
    - file_format: object with attributes `type` and `scalarDataType` (callable/type).
    """

    # Default return if we never find the field
    data = np.zeros(1, dtype=file_format.scalarDataType)

    def read_ascii_line():
        """Read one ASCII line safely from the binary file.
        Returns:
            (line, raw)
            line = decoded string without newline
            raw  = original raw bytes (None if EOF)
        """
        raw = binaryFp.readline()       # raw bytes including newline, or b'' at EOF
        if raw == b"":                  # TRUE EOF
            return None, None
        line = raw.decode('utf-8', errors='ignore').rstrip('\r\n')
        return line, raw

    # MAIN LOOP: read ASCII lines until "internalField" appears
    while True:
        line, raw = read_ascii_line()

        if raw is None:            # REAL EOF (not blank line!)
            raise EOFError("Reached end of file before finding 'internalField'")

        stripped = line.strip()
        if 'internalField' not in stripped:
            continue

        # Found the internalField line; parse it
        parts = stripped.split()
        if len(parts) < 2:
            raise ValueError(f"Malformed internalField line: {line!r}")

        mode = parts[1]
        if mode == 'uniform':
            # VECTOR field (e.g. internalField uniform (1 2 3); )
            if file_format.type in ('vector', 'vectorField'):
                # Attempt to parse three parts after 'uniform'
                # The value might be like "(1 2 3);" or "([1] [2] [3]);" etc.
                # We'll try to collect tokens after 'uniform' until we have three numeric tokens.
                token_text = ' '.join(parts[2:])  # rest of the line
                # remove parentheses and trailing semicolon and split on whitespace
                token_text = token_text.strip().lstrip('(').rstrip(');').rstrip(')')
                vec_tokens = token_text.split()
                if len(vec_tokens) < 3:
                    raise ValueError(f"Malformed uniform vector in line: {line!r}")
                data = np.array([[file_format.scalarDataType(vec_tokens[0]),
                                  file_format.scalarDataType(vec_tokens[1]),
                                  file_format.scalarDataType(vec_tokens[2])]],
                                dtype=file_format.scalarDataType)
                # binaryFp is already positioned at the next line after this ASCII line
                return data

            # SCALAR field (e.g. internalField uniform 1;)
            elif file_format.type == 'scalar':
                if len(parts) < 3:
                    raise ValueError(f"Malformed uniform scalar line: {line!r}")
                # parts[2] may include trailing semicolon
                scalar_token = parts[2].rstrip(';')
                data = file_format.scalarDataType(scalar_token)
                return data

            else:
                raise ValueError(f"Unknown file_format.type: {file_format.type!r}")

        else:
            # Non-uniform — we stop here and let the binary reader handle the block
            return readBinaryDataBlock(binaryFp, file_format)

    # If we reach here, internalField not found; raise or return default
    raise EOFError("Could not find 'internalField' in file")
    