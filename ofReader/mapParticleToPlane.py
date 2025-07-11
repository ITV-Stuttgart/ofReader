import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy.interpolate import LinearNDInterpolator
from ofReader.samplePlaneReader import samplePlaneReader
from ofReader.triangleInterp import TriangleInterp
import math
import pyvista as pv


class MapParticleToPlane:
    
    def _triangulate(self,axMinMax,radMinMax,nX,nY):
        xAxis = np.linspace(axMinMax[0],axMinMax[1],nX+1)
        yAxis = np.linspace(radMinMax[0],radMinMax[1],nY+1)
        if not self._tri:
            # First create a continuous list of points the triangles can refer to
            self._triPoints = np.zeros(((nX+1)*(nY+1),2))
            for i in range(nX+1):
                for j in range(nY+1):
                    self._triPoints[i*(nY+1)+j,0] = xAxis[i]
                    self._triPoints[i*(nY+1)+j,1] = yAxis[j]

            for i in range(nX):
                for j in range(nY):
                    self._tri.append((i*(nY+1)+j,(i+1)*(nY+1)+j,(i+1)*(nY+1)+(j+1)))
                    self._tri.append((i*(nY+1)+j,i*(nY+1)+(j+1),(i+1)*(nY+1)+(j+1)))
                    

    def _magnitude(self,vector):
        return math.sqrt(sum(pow(element, 2) for element in vector))

    def _createPlaneFromParticleData(self,nX,nY,xBounds,yBounds):
        xMin = xBounds[0]
        xMax = xBounds[1]

        yMin = yBounds[0]
        yMax = yBounds[1]     

        self._counts = np.zeros((nX,nY))

        # Create the triangulation
        self._triangulate((xMin,xMax),(yMin,yMax),nX,nY)

        # # Create an interpolator for the plotOverLine function
        # points = []
        # values = []
        # for i in range(nX):
        #     for j in range(nY):
        #         values.append(self._plane[i,j])
        #         points.append(
        #             [0.5*(_xAxis[i]+self._xAxis[i+1]),
        #              0.5*(self._yAxis[j]+self._yAxis[j+1])])
        
        # self._interp = LinearNDInterpolator(points,values)

    def _createPlaneFromSamplePlane(self,filePath):
        reader = samplePlaneReader()
        reader.readFromFile(filePath)
        self._tri = reader._tri
        self._triPoints = reader._triPoints

    def __init__(self):
        """Initialize a empty mapping object"""
        self._tri = []
        self._triValues = []
        self._triPoints = []

    def createPlane(self,**kwargs):
        """Generate a 2D plane for mapping the particle data

        There exist two general ways to create this plane:
        1) By providing the position data of the particles with the coords
           option to provide the x-, and y-axis index. Optionally set the 
           cylinderDomain flag to true to get a radial component from the 
           position data.
        2) An existing plane can be read in with the samplePlaneReader tool.
           For this option the input is the file path to the sample plane.
    
        Optional Parameters:
        --------------------
        pos : numpy array
            Positions of the particles as a 2D numpy array of dimension [n,3]
            where each row is one particle
        coords :  Tuple
            Provide the coordinates of the 2D plane. First entry is x-axis, index
            second entry is the y-axis index
            components
            e.g.: (1,0)   means the y coordinate of the particles is the x-axis
                          in the plane and the x-coordinate of the particles is 
                          the y-axis in the plane.
        cylinderDomain : bool
            Switch on if the domain is a rotational cylinder with the 
            x-axis as the axial component and the remaining two coordinate
            directions as the radial component
        nX : int
            Number of bins in the 2D plane on the x axis
        nY : int
            Number of bins in the 2D plane on the y axis
        xBounds : Tuple
            Tuple of two values providing the min/max value of the axial component
        yBounds : Tuple
            Tuple of two values providing the min/max value of the radial component
        filePath : string
            Path to an existing sample plane that can be read with the
            samplePlaneReader

        Examples:
        ------

        # First generate an empty mapping object
        mapper = MapParticleToPlane()
        
        # Generate a plane with the read in position values of a particle list
        # Here the axial axis is the z-axis
        mapper.createPlane(pos=particlePos,coords=(2,0,1),xBounds=(0,35))
        
        # Alternative option is to load an existing sample plane
        mapper.createPlane(filePath='path/to/existing/plane')

        # Map the particle data to the plane
        mapper.map(pos,val)
        """
        # Default coordinate system
        self._coords = (0,1)
        self._cylinderDomain = False

        if 'coords' in kwargs:
            self._coords = kwargs['coords']

        if 'cylinderDomain' in kwargs:
            self._coords = kwargs['cylinderDomain']

        if 'pos' in kwargs:
            nX  = 100    # Number of axial bins of the mapped plane
            nY = 100    # Number of radial bins of the mapped plane

            pos = kwargs['pos']

            if 'nX' in kwargs:
                nX = kwargs['nX']

            if 'nY' in kwargs:
                nY = kwargs['nY']

            if 'xBounds' in kwargs:
                xBounds = kwargs['xBounds']
            else:
                xBounds = (np.min(pos[:,self._coords[0]]),
                           np.max(pos[:,self._coords[0]]))

            if 'yBounds' in kwargs:
                yBounds = kwargs['yBounds']
            else:
                if self._cylinderDomain:
                    cylinderCoords = [0,1,2]

                    # Remove the x coordinate
                    cylinderCoords.remove(self._coords[0])

                    # Determine the other two directions
                    radInd0 = cylinderCoords[0]
                    radInd1 = cylinderCoords[1]

                    yBounds = (np.min(np.sqrt(pos[:,radInd0]**2+pos[:,radInd1]**2)),
                               np.max(np.sqrt(pos[:,radInd0]**2+pos[:,radInd1]**2)))
                else:
                    yBounds = (np.min(pos[:,self._coords[1]]),
                               np.max(pos[:,self._coords[1]]))

            self._createPlaneFromParticleData(nX,nY,xBounds,yBounds)

        elif 'filePath' in kwargs:
            self._createPlaneFromSamplePlane(kwargs['filePath'])
        else:
            print("Either provide pos or filePath")
            return
        
        # Create the triangulation maplotlib object for finding the closest
        # triangle
        self._triInterp = TriangleInterp(self._triPoints,self._tri)
        self._triFinder = self._triInterp.get_trifinder()
        
    
    def writeVTKFile(self,filename):
        """Write the plane as a vtk file
        
        Input:
        ------
            filename : string
            Path and filename to write the vtu file

        Usage:
        ------

            plane = MapParticleToPlane()    # Generate the plane object
            plane.createPlane()             # Create a plane, see for options
            plane.map(field)                # map a field to the plane
            plane.writeVTKFile('/home/Docs/myFile.vtu')
        """
        
        # Get all triangles
        triList = self._tri
        triPoints = self._triPoints
        cell_points = np.hstack([triPoints, np.zeros((triPoints.shape[0], 1))])

        # Create cells from the triangles for the vtk file
        cells = []
        cell_type = []
        for tri in triList:
            cells.append(len(tri))
            # Cell type is triangle
            cell_type.append(5)
            for i in range(len(tri)):
                cells.append(tri[i])

        mesh = pv.UnstructuredGrid(cells,cell_type,cell_points)
        mesh.cell_data["values"] = self._triValues

        mesh.save(filename)
        
        
    def map(self,pos,val):
        # Loop over all particles and store them in the bin
        counts = np.zeros(len(self._tri))
        self._triValues = np.zeros(len(self._tri))
        for p,v in zip(pos,val):
            # Convert the point to the 2D axis system
            point2D = [p[self._coords[0]],self._magnitude([p[self._coords[1]],p[self._coords[2]]])]
            triIndex = self._triFinder(*point2D)
            # If -1 the point was not found
            if (triIndex == -1):
                continue
            self._triValues[triIndex] += v
            counts[triIndex] +=1
        
        self._triValues /=counts

        # Set the field for the interpolation method
        self._triInterp.setField(self._triValues)

    def plotOverLine(self,ax,point1,point2,nPoints=100,**kwargs):
        """Plot results along a sample line of the plane
        
        Create the line with two points given in the plane coordinate system
        of x,y corrdinates. 

        Options:
        --------

        nPoints : int
            Number of sample points along the sample line

        scaleCoordinates : float
            Scale the coordinates of the sampled line for visualization
        
        scale : float
            Scale the results for visualization in the plot, e.g.,
            map.plot(ax,[0,0],[0,1],scale=1E+6) to scale sampled diameters to 
            micro meter
        """
        # Make point into a numpy array
        point1 = np.array(point1)
        point2 = np.array(point2)
        
        scaleCoordinates = 1.0  # To scale the coordinates
        scale = 1.0             # To scale the values

        if 'scale' in kwargs:
            scale = kwargs['scale']
            kwargs.pop('scale')

        if 'scaleCoordinates' in kwargs:
            scaleCoordinates = kwargs['scaleCoordinates']
            kwargs.pop('scaleCoordinates')

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
            v[i] = self._triInterp(*q[i])

        return ax.plot(x*scaleCoordinates,v*scale,**kwargs)

    def plot(self,ax,**kwargs):
        """Plot the mapped data as a pcolor plot and return the axis.
        Here, the tripcolor is used to allow for a better alpha value.
        pcolor only supports a single float whereas the tripcolor or the 
        matplotlib Collection object allows a list of floats.
        """

        alpha = np.ones(len(self._tri))

        vMin = np.min(self._triValues)
        vMax = np.max(self._triValues)

        
        scaleCoordinates = 1.0  # To scale the coordinates
        scale = 1.0             # To scale the values

        if 'vmin' in kwargs:
            vMin = kwargs['vmin']

        if 'vmax' in kwargs:
            vMax = kwargs['vmax']
        
        if 'scale' in kwargs:
            scale = kwargs['scale']
            kwargs.pop('scale')

        if 'scaleCoordinates' in kwargs:
            scaleCoordinates = kwargs['scaleCoordinates']
            kwargs.pop('scaleCoordinates')

        if 'transparent' in kwargs:
            if kwargs['transparent']==True:
                alpha = (np.array(self._triValues)*scale-vMin)/(vMax-vMin)
                alpha = np.clip(alpha,0,1)
            kwargs.pop('transparent')

        return ax.tripcolor(
            self._triPoints[:,0]*scaleCoordinates,
            self._triPoints[:,1]*scaleCoordinates,
            self._triValues*scale,
            triangles=self._tri,
            alpha=alpha,
            **kwargs) 

