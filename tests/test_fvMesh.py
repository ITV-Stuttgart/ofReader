from ofReader.fvMesh import fvMesh
import matplotlib.pyplot as plt
import numpy as np
import math

mesh = fvMesh('tests/testCase')

centers = np.array(mesh.centers())


V =mesh.volumes()
# Add up all cell volumes, must equal 1.0
totalVolume = 0
for e in V:
    totalVolume = totalVolume + e

assert math.isclose(totalVolume,1.0)

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.scatter(centers[:,0],centers[:,1],centers[:,2])
plt.savefig('test.png',format='png')

