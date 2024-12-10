from setuptools import find_packages, setup

setup(
    name='ofReader',
    packages=find_packages(include=['ofReader']),
    version='0.2.2',
    description='Library to read OpenFOAM data into python for post processing',
    author='Jan Wilhelm Gaertner',
    license='GNUv3',
	install_requires=['numpy','tqdm'],
	setup_requires=['pytest-runner'],
	tests_require=['pytest==6.2.5'],
	test_suite='tests',
)
