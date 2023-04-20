from ofReader import sampleLineReader
import numpy as np


def test_sampleLineReader():
    data = sampleLineReader('tests/zAxisCenterLine_alpha.liquid_k_rho_sigma.csv')
    # Check that the var names are read correctly
    keys = ['x','alpha.liquid','k','rho','sigma']
    for key,testKey in zip(data,keys):
        assert key == testKey
