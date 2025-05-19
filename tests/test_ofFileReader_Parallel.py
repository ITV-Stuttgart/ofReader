from ofReader import readOpenFOAMFile
import numpy as np
import matplotlib.pyplot as plt


def test_ofFileReader_parallel():
    data = readOpenFOAMFile('./tests/testCase/',time=0, fileName='C',decomposed=True)
    # Number of read points must match the mesh size
    assert(len(data) == 10648)
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(data[:,0],data[:,1],data[:,2])
    plt.savefig('test-readParallel.png',format='png')
    
