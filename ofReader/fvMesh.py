from tqdm import tqdm
import numpy as np
from .ofFileReader import readOpenFOAMFile


class fvMesh:
    def __init__(self,casePath):
        """
        Read in the mesh in the OpenFOAM format and generate the cells
        """
        self._points = readOpenFOAMFile(casePath + '/constant/polyMesh/points')
        self._faces  = readOpenFOAMFile(casePath + '/constant/polyMesh/faces')
        self._owner  = readOpenFOAMFile(casePath + '/constant/polyMesh/owner')
        self._neighbor = readOpenFOAMFile(casePath + '/constant/polyMesh/neighbour')
        
        self._centers = []

        # Get the number of cells
        nCells = 0
        for cellIndex in self._owner:
            if cellIndex > nCells:
                nCells = cellIndex
        # As it is zero based add one more entry
        nCells = nCells +1

        print("Create cells in mesh...")
        self._cells = [ fvmCell() for _ in range(nCells) ]

        print("Add owner faces...")
        for i in tqdm(range(len(self._owner))):
            self._cells[self._owner[i]].addFaceIndex(i)

        print("Add neighbor faces...")
        for i in tqdm(range(len(self._neighbor))):
            if self._neighbor[i] >= len(self._cells):
                print("Error: try to access out of bounds: ",self._neighbor[i], " with max length: ", len(self._cells))
            self._cells[self._neighbor[i]].addFaceIndex(i)
    
    def cells(self):
        return self._cells
    
    def centers(self):
        if len(self._centers) == 0:
            # Calculate the centers
            self._centers = np.zeros((len(self._cells),3))
            for i in range(len(self._cells)):
                self._centers[i] = self._cells[i].midPoint(self._points,self._faces)
        return self._centers

class fvmCell:
    """Container to store the information of a cell and function to 
    calculate the centre point of the cell.
    """
    def __init__(self):
        self._faceList = []
        self._midPoint = np.zeros(3)
        self._midPointSet = False

    def addFaceIndex(self,faceIndex):
        self._faceList.append(faceIndex)

    def midPoint(self,points,faces):
        """ 
        Calculate the mid point of the cell 
        for now very simple as the average of the cell vertices
        This is incorrect but gives an idea
        """
        if not self._midPointSet:
            for faceIndex in self._faceList:
                for pointIndex in faces[faceIndex]:
                    self._midPoint = self._midPoint + points[pointIndex]
            self._midPoint = self._midPoint/len(self._faceList)
            self._midPointSet = True
            return self._midPoint
        else:
            return self._midPoint



