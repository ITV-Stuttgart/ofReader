import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy.interpolate import LinearNDInterpolator
from ofReader.samplePlaneReader import samplePlaneReader
from ofReader.triangleInterp import TriangleInterp
import math


class MapParticleToPlane:
    
    def _triangulate(self,axMinMax,radMinMax,numAx,numRad):
        xAxis = np.linspace(axMinMax[0],axMinMax[1],numAx+1)
        yAxis = np.linspace(radMinMax[0],radMinMax[1],numRad+1)
        if not self._tri:
            nAx, nRad = self._plane.shape

            # First create a continuous list of points the triangles can refer to
            self._triPoints = np.zeros(((nAx+1)*(nRad+1),2))
            for i in range(nAx+1):
                for j in range(nRad+1):
                    self._triPoints[i*(nRad+1)+j,0] = xAxis[i]
                    self._triPoints[i*(nRad+1)+j,1] = yAxis[j]

            for i in range(nAx):
                for j in range(nRad):
                    self._tri.append((i*(nRad+1)+j,(i+1)*(nRad+1)+j,(i+1)*(nRad+1)+(j+1)))
                    self._tri.append((i*(nRad+1)+j,i*(nRad+1)+(j+1),(i+1)*(nRad+1)+(j+1)))
                    

    def _magnitude(self,vector):
        return math.sqrt(sum(pow(element, 2) for element in vector))

    def _createPlaneFromParticleData(self,numAx,numRad,xBounds,yBounds):
        axInd   = self._coords[0]     # axial index
        radInd0 = self._coords[1]     # radial index
        radInd1 = self._coords[2]     # radial index 2

        axMin = xBounds[0]
        axMax = xBounds[1]

        radMin = yBounds[0]
        radMax = yBounds[1]     

        self._counts = np.zeros((numAx,numRad))

        # Create the triangulation
        self._triangulate((axMin,axMax),(radMin,radMax),numAx,numRad)

        # # Create an interpolator for the plotOverLine function
        # points = []
        # values = []
        # for i in range(numAx):
        #     for j in range(numRad):
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
           option to give the axial axis (first entry), and the two radial axis
           as a python tuple.
        2) An existing plane can be read in with the samplePlaneReader tool.
           For this option the input is the file path to the sample plane.
    
        Optional Parameters:
        --------------------
        pos : numpy array
            Positions of the particles as a 2D numpy array of dimension [n,3]
            where each row is one particle
        coords :  Tuple
            Provide the coordinates of the 2D plane. First entry is the axial
            or x-axis, second and third entry are the indices for the radial
            components
            e.g.: (1,0,2) means the y-axis is the axial direction and x-axis 
                          and z-axis are the radial components
        numAx : int
            Number of axial bins in the 2D plane
        numRad : int
            Number of radial bins in the 2D plane
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
        self._coords = (0,1,2)

        if 'coords' in kwargs:
            self._coords = kwargs['coords']

        if 'pos' in kwargs:
            numAx  = 100    # Number of axial bins of the mapped plane
            numRad = 100    # Number of radial bins of the mapped plane

            pos = kwargs['pos']

            if 'numAx' in kwargs:
                numAx = kwargs['numAx']

            if 'numRad' in kwargs:
                numRad = kwargs['numRad']

            if 'xBounds' in kwargs:
                xBounds = kwargs['xBounds']
            else:
                xBounds = (np.min(pos[:,self._coords[0]]),np.max(pos[:,self._coords[1]]))

            if 'yBounds' in kwargs:
                yBounds = kwargs['yBounds']
            else:
                yBounds = (np.min(np.sqrt(pos[:,self._coords[1]]**2+pos[:,self._coords[2]]**2)),np.max(np.sqrt(pos[:,self._coords[1]]**2+pos[:,self._coords[2]]**2)))

            self._createPlaneFromParticleData(pos,numAx,numRad,xBounds,yBounds)

        elif 'filePath' in kwargs:
            self._createPlaneFromSamplePlane(kwargs['filePath'])
        else:
            print("Either provide pos or filePath")
            return
        
        # Create the triangulation maplotlib object for finding the closest
        # triangle
        self._triInterp = TriangleInterp(self._triPoints,self._tri)
        self._triFinder = self._triInterp.get_trifinder()
        
        
        
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
            v[i] = self._triInterp(*q[i])

        return ax.plot(x,v,**kwargs)

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
                alpha = (np.array(self._triValues)-vMin)/(vMax-vMin)
                alpha = np.clip(alpha,0,1)
            kwargs.pop('transparent')

        return ax.tripcolor(
            self._triPoints[:,0]*scaleCoordinates,
            self._triPoints[:,1]*scaleCoordinates,
            self._triValues*scale,
            triangles=self._tri,
            alpha=alpha,
            **kwargs) 

