import numpy as np
from scipy.interpolate import LinearNDInterpolator
import math



class circAverageReader:
    """
    Load and processes files written by the circAverage tool:
    https://github.tik.uni-stuttgart.de/ITV/circAverage-v2012.git

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
    
            
    # =======================================================================

    def __init__(self,fname):
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
        self._points = np.array(readData[3])
        
    
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
    

    def pcolor(self,ax,**kwargs):
        """Plots the result in a matplotlib.pyplot.pcolor plot
        
        Input:
        ======
            ax : Matplotlib axis to plot the data in

            scaleCoordinates : Optional argument to scale the coordinates of the 
                x and y axis.

            **kwargs : Additional arguments that can be used with pcolor
        """
        scaleCoordinates = [1,1]
        for key, value in kwargs.items():
            if key == "scaleCoordinates":
                scaleCoordinates = value

        # List of triangles, each tri is a list of indices in the X,Y array
        tri = []
        # List to store the value in each tri
        triValue = []
        # Loop over all faces
        i=0
        for face in self._faces:
            if len(face) == 3:
                tri.append(np.array(face))
                triValue.append(self._values[i])
            if len(face) == 4:
                face1 = [face[0],face[1],face[2]]
                face2 = [face[2],face[3],face[0]]
                tri.append(np.array(face1,dtype=np.int32))
                triValue.append(self._values[i])
                tri.append(np.array(face2,dtype=np.int32))
                triValue.append(self._values[i])
            i = i +1

        return ax.tripcolor(self._points[:,0]*scaleCoordinates,self._points[:,1]*scaleCoordinates,triValue,triangles=tri) 


    @property
    def values(self):
        return self._values
    
    @property
    def pos(self):
        return self._pos
    
    @property
    def points(self):
        return self._points
    
    @property
    def faces(self):
        return self._faces
