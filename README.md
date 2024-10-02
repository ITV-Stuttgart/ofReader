# ofRader - Python Library for OpenFOAM

Python functions to read OpenFOAM data for postprocessing.

## Installation

Execute the following within this directory:

```bash
python setup.py bdist_wheel
pip install dist/ofReader-0.1.0-py3-none-any.whl
```

## Usage

After installing the python library import it with

```python
from ofReader import sampleLineReader

# Load data from a sample line
data = sampleLineReader('../postProcessing/sample/line_alpha.liquid_k_rho_sigma.csv')
# Access data sets by name of the field, e.g.:
# data['x'] => for position
# data['alpha.liquid'] => for the liquid.alpha field
# data['k'] => for the turb. kin. energy
```

## Load OpenFOAM Fields and Mesh

The OpenFOAM fields can be read with
```python
from ofReader.ofFileReader import readOpenFOAMFile
# E.g. read the velocity field of time step 0.005s
pathToFile = '0.005/U'
eulerianData = readOpenFOAMFile(pathToFile)

# This also works for Lagrangian data
pathToLagrangianData = '0.005/lagrangian/cloudName/pos'
lagrangianData = readOpenFOAMFile(pathToFile)
```

For the Eulerian fields the position of the entries is stored in the fvMesh 
object. Therefore, a fvMesh python class is provided which can read the 
mesh and provides an interface for the cells:
```python
from ofReader.fvMesh import fvMesh
mesh = fvMesh(pathToCase)
# Get cell center points as list of arrays
center = mesh.centers()
```


## Tests

To execute the tests:
```bash
python3 setup.py pytest
```
