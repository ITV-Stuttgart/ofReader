import matplotlib.tri as tri

class TriangleInterp:

    def __init__(self,triVertices,triangles):
        """Create an interpolation class that uses different interpolation
        schemes

        Currently only face center values are supported
        """

        self._Triangulation = tri.Triangulation(triVertices[:,0],triVertices[:,1],triangles)
        self._triFinder = self._Triangulation.get_trifinder()
    
    def setField(self,centerValues):
        if (len(centerValues) != len(self._Triangulation.triangles)):
            raise TypeError(f"Fatal Error: centerValues must have same size as triangles\nlen(centerValues)={len(centerValues)}\tlen(triangles)={len(self._Triangulation.triangles)}")
        self._triFaceCenterValues = centerValues 

    def get_trifinder(self):
        return self._triFinder

    def __call__(self,x,y):
        """Interpolate the value at the given x,y position"""

        # Find the triangle (x,y) is located in
        ind = self._triFinder(x,y)
        if ind == -1:
            print("Point outside of domain")
            return -1
        return self._triFaceCenterValues[ind]


        
    
