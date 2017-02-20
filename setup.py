from setuptools import setup

setup(
    name='cefpanda',
    version='0.1',
    description='Panda3D-friendly wrapper around cefpython',
    url='https://github.com/Moguri/cefpanda',
    author='Mitchell Stokes',
    license='MIT',
    packages=['cefpanda'],
    install_requires=[
        'panda3d',
        'cefpython3',
    ]
)
