import numpy as np
import os

def sampleLineReader(path):
    # Get the variables stored in this file
    fileName = os.path.basename(path)

    # Variable names that store vectors in OpenFOAM
    vectorVariables = ["U","UMean","wallShearStress"]


    # Try to detect the number of variables stored in the file
    # OpenFOAM plits by default each variable with an underscore
    varNames = fileName.split('_')
    nVars  = len(varNames)-1
    # Split off ending of last entry
    fileEnding = varNames[-1].split('.')[1]
    varNames[-1] = varNames[-1].split('.')[0]
    varNames[0] = 'x'
    
    if fileEnding == 'csv':
        readData = np.genfromtxt(path,delimiter=',',skip_header=1)
    else:
        readData = np.genfromtxt(path)
    
    data = {}
    i = 0
    for name in varNames:
        if name in vectorVariables:
            data[name] = readData[:,i:i+3]
            i = i+2
        else:
            data[name] = readData[:,i]
        i = i+1
    
    return data
