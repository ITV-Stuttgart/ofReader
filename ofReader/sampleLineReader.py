import numpy as np
import matplotlib.pyplot as plt
from numpy import genfromtxt
import os

def sampleLineReader(path):
    # Get the variables stored in this file
    fileName = os.path.basename(path)
    varNames = fileName.split('_')
    nVars  = len(varNames)-1
    # Split off ending of last entry
    fileEnding = varNames[-1].split('.')[1]
    varNames[-1] = varNames[-1].split('.')[0]
    varNames[0] = 'x'
    
    if fileEnding == 'csv':
        readData = np.genfromtxt(path,delimiter=',')
    else:
        readData = np.genfromtxt(path)
    
    data = {}
    i = 0
    for name in varNames:
        data[name] = readData[:,i]
        i = i+1
    
    return data
