from ofReader.fvMesh import fvMesh
import matplotlib.pyplot as plt
import numpy as np

mesh = fvMesh('tests/testCase')

centers = np.array(mesh.centers())

# fig = plt.figure()
# ax = fig.add_subplot(projection='3d')
# ax.scatter(centers[:,0],centers[:,1],centers[:,2])
# plt.savefig('test.png',format='png')

