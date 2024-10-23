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
        
        self._nCells = 0

        self._centers = []
        self._volumes = []

        # Get the number of cells
        nCells = 0
        for cellIndex in self._owner:
            if cellIndex > nCells:
                nCells = cellIndex
        for cellIndex in self._neighbor:
            if cellIndex > nCells:
                nCells = cellIndex
        # As it is zero based add one more entry
        nCells = nCells +1
        self._nCells = nCells

        print("Create cells in mesh...")
        self._cells = np.empty(nCells,dtype=fvmCell)
        for i in range(len(self._cells)):
            self._cells[i] = fvmCell()

        print("Add owner faces...")
        for i in tqdm(range(len(self._owner))):
            self._cells[self._owner[i]].addFaceIndex(i)

        print("Add neighbor faces...")
        for i in tqdm(range(len(self._neighbor))):
            self._cells[self._neighbor[i]].addFaceIndex(i)
    
    def centers(self):
        if len(self._centers) == 0:
            # Calculate the centers
            self._centers = np.zeros((len(self._cells),3))
            for i in range(len(self._cells)):
                self._centers[i] = self._cells[i].midPoint(self._points,self._faces)
        return self._centers
    
    def volumes(self):
        if len(self._volumes) == 0:
            # Calculate the centers
            self._volumes = np.zeros(len(self._cells))
            for i in range(len(self._cells)):
                self._volumes[i] = self._cells[i].volume(self._points,self._faces)
        return self._volumes
    
    @property
    def nCells(self):
        return self._nCells
    
    @property
    def cells(self):
        return self._cells



class fvmCell:
    """Container to store the information of a cell and function to 
    calculate the centre point of the cell.
    """
    def __init__(self):
        self._faceList = []
        self._midPoint = np.zeros(3)
        self._midPointSet = False
        self._volume = 0

    def addFaceIndex(self,faceIndex):
        self._faceList.append(faceIndex)

    def midPoint(self,points,faces):
        """ 
        Calculate the mid point of the cell 
        for now very simple as the average of the cell vertices
        This is incorrect but gives an idea
        """
        if not self._midPointSet:
            nPoints = 0
            for faceIndex in self._faceList:
                for pointIndex in faces[faceIndex]:
                    self._midPoint = self._midPoint + points[pointIndex]
                    nPoints = nPoints + 1
            self._midPoint = self._midPoint/nPoints
            self._midPointSet = True
            return self._midPoint
        else:
            return self._midPoint
        
    def volume(self,points,faces):
        # Calculate the mid point
        self.midPoint(points,faces)
        self._volume = 0
        # Decompose cell into tetrahedars for each face 
        for faceIndex in self._faceList:
            face = faces[faceIndex]
            # Always split face in tets
            if len(face) == 4:
                # Calculate the volume based on tet1
                vec1 = points[face[0]]-self._midPoint
                vec2 = points[face[1]]-self._midPoint
                vec3 = points[face[2]]-self._midPoint
 
                M1 = np.reshape(np.concatenate((vec1,vec2,vec3)),(3,3))
                self._volume = self._volume + np.abs(1.0/6.0*np.linalg.det(M1))

                # Calculate the volume based on tet2
                vec1 = points[face[2]]-self._midPoint
                vec2 = points[face[3]]-self._midPoint
                vec3 = points[face[0]]-self._midPoint
                M2 = np.reshape(np.concatenate((vec1,vec2,vec3)),(3,3))
                
                self._volume = self._volume + np.abs(1.0/6.0*np.linalg.det(M2))
            if len(face) == 3:
                # Calculate the volume based on tet1
                vec1 = points[face[0]]-self._midPoint
                vec2 = points[face[1]]-self._midPoint
                vec3 = points[face[2]]-self._midPoint
                
                M1 = np.reshape(np.concatenate((vec1,vec2,vec3)),(3,3))
                self._volume = self._volume + np.abs(1.0/6.0*np.linalg.det(M1))
        
        return self._volume



