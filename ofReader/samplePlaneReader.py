import numpy as np
from scipy.interpolate import LinearNDInterpolator
import math
import copy


class samplePlaneReader:
    """
    Load and processes files written by the circAverage tool:
    https://github.tik.uni-stuttgart.de/ITV/circAverage-v2012.git
    Or any other tool that uses the samplePlane object. Note that
    here we refer to the own samplePlane not OpenFOAM's native 
    sampledPlane!
    
    Access coordinates with pos function and values with values
    To plot data along a line defined by two points 
    p1 = [ax,rad] and p2 = [ax2,rad2] with each an axial and radial
    component use the plotAlongLine(p1,p2) function
    """

    # =======================================================================
    # Protected Functions
    def _readInlineList(self,line,dtype=float):
        # First split of the 
        splitLine = line.split("(")
        splitLine = splitLine[1].split(")")
        splitLine = splitLine[0].split()
        val = []
        for e in splitLine:
            val.append(dtype(e))
        return val

    def _readList(self,f,dtype=float):
        val = []
        while (True):
            line = f.readline()            
            line = line.strip()

            # If it starts with a bracket it is a list
            if line.startswith("(") and line.endswith(")"):
                val.append(self._readInlineList(line))
            elif len(line) > 2 and line[0].isdigit() and line[1] == "(":
                val.append(self._readInlineList(line))
            elif line.startswith("("):
                continue
            elif line.endswith(")"):
                break
            else:
                val.append(dtype(line))
        return val
    
    
    # Calculate the magnitude of a vector
    def _magnitude(self,vector):
        return math.sqrt(sum(pow(element, 2) for element in vector))
    

    def _triangulate(self):
        
        if not self._tri:
            # Loop over all faces
            i=0
            for face in self._faces:
                if len(face) == 3:
                    self._tri.append(np.array(face))
                    self._triValue.append(self._values[i])
                if len(face) == 4:
                    face1 = [face[0],face[1],face[2]]
                    face2 = [face[2],face[3],face[0]]
                    self._tri.append(np.array(face1,dtype=np.int32))
                    self._triValue.append(self._values[i])
                    self._tri.append(np.array(face2,dtype=np.int32))
                    self._triValue.append(self._values[i])
                i = i +1
        
        return self._tri, self._triValue


    # =======================================================================

    def __init__(self):
        self._fname = "None"
        self._pos = np.zeros(1)
        self._values = np.zeros(1)
        self._faces = []
        self._triPoints = np.zeros(1)
        
        self._tri = []      # List of triangles, each tri is a list of indices in the X,Y array
        self._triValue = [] # List to store the value in each tri
    
    def readFromFile(self,fname):
        self._fname = fname

        # readData contains list of values, cell coordinates, faces, and points
        # readData[0] : values
        # readData[1] : coordinates
        # readData[2] : faces
        # readData[3] : points
        readData = []
        with open(fname) as f:
            while (True):
                # store position of file ptr before readline
                file_pos = f.tell()
                line = f.readline()
                
                # Check for end of file
                if not line:
                    break
                
                line = line.strip()
                # search for the first bracket
                if line.startswith("("):
                    f.seek(file_pos)
                    val = self._readList(f)
                    readData.append(val)

        # Set the cell values  
        self._values = np.array(readData[0])
        
        # readData[1] currently is a list of list and needs to be converted to an array
        self._pos = np.empty((len(readData[1]),len(readData[1][0])))
        
        rowI = 0
        for row in readData[1]:
            colI = 0
            for e in row:
                self._pos[rowI,colI] = e
                colI = colI + 1
            rowI = rowI + 1
        
        # Generate the interpolator
        self._interp = LinearNDInterpolator(self._pos,self._values)

        # Load the points and faces
        self._faces = readData[2]

        # points
        self._triPoints = np.array(readData[3])

        self._tri, self._triValue = self._triangulate()

    def __str__(self):
        return f"Eulerian data from file: ", self._fname
    
    
    # return an x, y data set to plot the data along a line
    # Line is defined with two points
    def plotAlongLine(self,point1,point2,nPoints=100):
        # Make point into a numpy array
        point1 = np.array(point1)
        point2 = np.array(point2)
        
        
        # create points to interpolate to
        t = np.linspace(0.0,1.0,nPoints)
        q = np.empty((len(t),2))
        x = np.linspace(0.0,1.0,nPoints)
        for i in range(len(t)):
            q[i,:] = point1 + t[i]*(point2-point1)
            x[i] = self._magnitude(t[i]*(point2-point1))
        
        # Find the closest point
        v = np.zeros(nPoints)
        for i in range(len(v)):
            v[i] = self._interp(q[i])

        return x,v
    

    def plot(self,ax,**kwargs):
        """Plots the result in a matplotlib.pyplot.pcolor plot
        
        Input:
        ------
            ax : axis
                Matplotlib axis to plot the data in

            scaleCoordinates : float to scale the x and y coordinates
                Optional argument to scale the coordinates of the 
                x and y axis.

            **kwargs : 
                Additional arguments that can be used with pcolor
        """
        scaleCoordinates = (1,1)
        if 'scaleCoordinates' in kwargs:
            scaleCoordinates = kwargs['scaleCoordinates']
            kwargs.pop('scaleCoordinates')
        
        return ax.tripcolor(
            self._triPoints[:,0]*scaleCoordinates,
            self._triPoints[:,1]*scaleCoordinates,
            self._triValue,
            triangles=self._tri,
            **kwargs) 


    def __mul__(self,other):
        """Multiply with another circAverageReader of the same type or a 
           scalar
        """
        # Create a copy of the current reader
        copyReader = samplePlaneReader()
        copyReader._faces = copy.deepcopy(self._faces)
        copyReader._triPoints = copy.deepcopy(self._triPoints)
        copyReader._pos = copy.deepcopy(self._pos)

        if isinstance(other,(int,float)):
            copyReader._values = other*self._values
        else:
            copyReader._values = self._values*other._values
        
        return copyReader

    def __rmul__(self,other):
        # Create a copy of the current reader
        copyReader = samplePlaneReader()
        copyReader._faces = copy.deepcopy(self._faces)
        copyReader._triPoints = copy.deepcopy(self._triPoints)
        copyReader._pos = copy.deepcopy(self._pos)

        if isinstance(other,(int,float)):
            copyReader._values = other*self._values
        else:
            copyReader._values = self._values*other._values
        
        return copyReader

    def __truediv__(self,other):
        # Create a copy of the current reader
        copyReader = samplePlaneReader()
        copyReader._faces = copy.deepcopy(self._faces)
        copyReader._triPoints = copy.deepcopy(self._triPoints)
        copyReader._pos = copy.deepcopy(self._pos)

        if isinstance(other,(int,float)):
            copyReader._values = self._values/other
        else:
            copyReader._values = self._values/other._values
        
        return copyReader


    @property
    def values(self):
        return self._values
    
    @property
    def pos(self):
        return self._pos
    
    @property
    def points(self):
        return self._triPoints
    
    @property
    def faces(self):
        return self._faces
