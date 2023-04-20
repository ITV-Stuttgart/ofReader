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

## Tests

To execute the tests:
```bash
python3 setup.py pytest
```
