"""
Read an OpenFOAM field, e.g., a volScalarField or lagrangian fields with the 
function
   
    readOpenFOAMFile(filePath)

For e.g. a volScalarField it is often necessary to know the mesh. To read in 
the mesh the class fvMesh is provided.

"""

import numpy as np
from tqdm import tqdm
import sys
import os
import re
from ofReader.ofFileFormat import ofFileFormat
from ofReader.ofBoundaryData import ofBoundaryData
from ofReader.ofvolField import ofVolField
from ofReader.ofReadSupportFunctions import *

# ==============================================================================
# Helper Functions 
# ==============================================================================
def readOpenFOAMFile(filePath,**kwargs):
    """Read an OpenFOAM file
    This can be an Euler field in a time directory or Lagrangian data.
    
    Usage:
    ------
        from ofReader.ofFileReader import readOpenFOAMFile
        # E.g. read the velocity file
        U = readOpenFOAMFile('0/U')

        To read the file in decomposed format pass the option decomposed
        U = readOpenFOAMFile('/path/to/case/', fileName='U', time=0, decomposed=True)
        
         
    """
    decomposed = False
    collated   = False
    time       = 0
    fileName   = ''
    casePath   = filePath

    boundary_data = ofBoundaryData()

    if 'decomposed' in kwargs:
            decomposed = bool(kwargs['decomposed'])
            if 'time' not in kwargs:
                raise ValueError('If decomposed is selected a time directory has to be specified.')
            if 'fileName' not in kwargs:
                raise ValueError('If decomposed is selected a fileName has to be specified.')
            
            time = kwargs['time']
            fileName = kwargs['fileName']
            decomposed=True
            kwargs.pop('decomposed')

    if not decomposed:
        fileFormat = ofFileFormat()
        fileFormat.readFile(filePath)

        data = np.zeros(1)

        if fileFormat.format == "binary":
            with open(filePath, mode='rb') as binaryFp:
                if fileFormat.fieldType == "volField":
                    data = readBinaryInternalField(binaryFp,fileFormat)
                    boundary_data.read(binaryFp,fileFormat)
                    field = ofVolField()
                    field.internal_data = data
                    field.boundary = boundary_data
                    return field
                else:
                    data = readBinaryDataBlock(binaryFp,fileFormat)
                    return data
        elif fileFormat.format == "ASCII":
            with open(filePath, encoding='utf-8', errors='ignore') as asciiFp:
                if fileFormat.fieldType == "volField":
                    data = readASCIIInternalField(asciiFp,fileFormat)
                    boundary_data.read(asciiFp,fileFormat)
                    field = ofVolField()
                    field.internal_data = data
                    field.boundary = boundary_data
                    return field
                else:
                    data = readASCIIDataBlock(asciiFp,fileFormat)
                    return data
        else:
            print("File format is undefined")
            sys.exit("Error reading: "+filePath)

    else:
        # If decomposed built the filePath
        collated, processorDirName = has_processors_dir(filePath)

        if collated:
            raise NotImplementedError("This feature is not yet implemented.")
        else:
            # Get the number of processors:
            nProcs = 0
            for name in os.listdir(casePath):
                full_path = os.path.join(casePath, name)
                if os.path.isdir(full_path) and name.startswith("processor"):
                    nProcs += 1

            # Read the first processor file
            data = np.zeros(1)
            filePath = f'{casePath}/processor0/{time:g}/{fileName}'

            fileFormat = ofFileFormat()
            fileFormat.readFile(filePath)

            if fileFormat.format == "ASCII":
                data = readASCIIDataBlock(filePath,fileFormat)
            elif fileFormat.format == "binary":
                data = readBinaryDataBlock(filePath,fileFormat)
            else:
                print("File format is undefined")
                sys.exit("Error reading: "+filePath)

            # Read all files:
            for n in range(1,nProcs):
                filePath = f'{casePath}/processor{n:g}/{time:g}/{fileName}'

                fileFormat = ofFileFormat()
                fileFormat.readFile(filePath)

                if fileFormat.format == "ASCII":
                    data1 = readASCIIDataBlock(filePath,fileFormat)
                elif fileFormat.format == "binary":
                    data1 = readBinaryDataBlock(filePath,fileFormat)
                else:
                    print("File format is undefined")
                    sys.exit("Error reading: "+filePath)

                data = np.concatenate((data,data1))
            
            return data


def readOpenFOAMDictionary(filename,**kwargs):
    """Reads an OpenFOAM dictionary, e.g., cloudProperties file
    
    This function reads a file and creates a python dictionary for each entry
    enclosed by curly braces.
    """
    with open(filename, "r") as f:
        text = f.read()

    # --- 1. Remove comments (// ...) ---
    text = re.sub(r"//.*", "", text)

    # --- 2. Tokenize braces, semicolons, and parentheses ---
    # Keep them as separate tokens
    tokens = re.split(r"(\{|\}|;)", text)
    tokens = [t.strip() for t in tokens if t.strip()]

    root = {}
    stack = [(root, None)]
    current_dict, current_name = root, None
    key_buffer = []

    for token in tokens:
        if token == "{":
            # Start new dictionary
            new_dict = {}
            if current_name is None and key_buffer:
                current_name = key_buffer.pop()
            if current_name is not None:
                current_dict[current_name] = new_dict
            stack.append((current_dict, current_name))
            current_dict, current_name = new_dict, None
            key_buffer = []

        elif token == "}":
            # End current dictionary
            current_dict, current_name = stack.pop()
            key_buffer = []

        elif token == ";":
            # Commit key-value pair
            if len(key_buffer) == 2:
                key, value = key_buffer
                current_dict[key] = value
            elif len(key_buffer) > 2:
                key = key_buffer[0]
                value = " ".join(key_buffer[1:])
                current_dict[key] = value
            elif len(key_buffer) == 1:
                current_dict[key_buffer[0]] = None
            key_buffer = []

        else:
            # Handle grouped values like (0 0 47.0)
            if token.startswith("(") and token.endswith(")"):
                key_buffer.append(token)
            else:
                # Split regular tokens on whitespace
                parts = token.split()
                key_buffer.extend(parts)
                if len(key_buffer) == 1:
                    current_name = key_buffer[0]
                # do not reset until we hit ; or { or }

    return root


