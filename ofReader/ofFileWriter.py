import numpy as np
from ofReader.ofFileReader import ofFileFormat
from ofReader.ofBoundaryData import ofBoundaryData
import os.path as path
from io import StringIO

def writeOpenFOAMFile(filePath,fileFormat : ofFileFormat, data, boundaryData, dimensions):

    # Name of the file is the last part of the file name
    name = path.basename(filePath)
    _writeOpenFOAMHeader(filePath,fileFormat, name)
    _writeDimensions(filePath,dimensions)
    _writeASCIIDataBlock(filePath,fileFormat, data)
    boundaryData.write(filePath)
    


def _writeOpenFOAMHeader(filePath,fileFormat : ofFileFormat,name):
    f = open(filePath, "w")
    f.write("/*--------------------------------*- C++ -*----------------------------------*\\\n")
    f.write("| =========                 |                                                 |\n")
    f.write("| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n")
    f.write("|  \\    /   O peration     | Version:  2312                                  |\n")
    f.write("|   \\  /    A nd           | Website:  www.openfoam.com                      |\n")
    f.write("|    \\/     M anipulation  |                                                 |\n")
    f.write("\*---------------------------------------------------------------------------*/\n")
    f.write("FoamFile\n")
    f.write("{\n")
    f.write("    version     2.0;\n")
    f.write(f"    format      {fileFormat.format.lower()};\n")
    f.write(f"    arch        \"LSB;label={fileFormat.labelSize:d};scalar={fileFormat.scalarSize:d}\";\n")
    f.write(f"    class       {fileFormat.type};\n")
    f.write("    location    \"0.00000000e+00\";\n")
    f.write(f"    object      {name};\n")
    f.write("}\n")
    f.write("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n")
    f.write("\n")
    f.close()

def _writeDimensions(filePath,dimensions):
    f = open(filePath, "a")
    f.write("dimensions\t[")
    for e in dimensions:
        f.write(f"{e:d} ")
    f.write("];\n\n")

def _writeASCIIDataBlock(filePath,fileFormat : ofFileFormat,data):
    f = open(filePath, "a")
    if fileFormat.type == "vectorField" or fileFormat.type == "volVectorField":
        f.write("internalField   nonuniform List<vector>\n")
        f.write(f"{len(data):d}\n")
        f.write("(\n")
        for i in range(len(data)):
            f.write(f"({data[i][0]:g} {data[i][1]:g} {data[i][2]:g})\n")
        f.write(");\n")
    if fileFormat.type == "scalarField" or fileFormat.type == "volScalarField":
        f.write("internalField   nonuniform List<scalar>\n")
        f.write(f"{len(data):d}\n")
        f.write("(\n")
        for i in range(len(data)):
            f.write(f"{data[i]:g}\n")
        f.write(");\n")
