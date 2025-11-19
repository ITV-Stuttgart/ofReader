import numpy as np
from ofReader.ofBoundaryData import ofBoundaryData

class ofVolField:
    """Volume field of vectors or scalars
    """

    def __init__(self):
        self._internal_data = np.zeros(1)
        self._boundary = ofBoundaryData()

    @property
    def internal_data(self):
        return self._internal_data
    
    @property
    def boundary(self):
        return self._boundary.patches
    
    @boundary.setter
    def boundary(self,boundary):
        self._boundary = boundary

    @internal_data.setter
    def internal_data(self,data):
        self._internal_data = data