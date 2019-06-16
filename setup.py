from setuptools import setup

setup(
    name='cefpanda',
    version='0.1',
    description='Panda3D-friendly wrapper around cefpython',
    url='https://github.com/Moguri/cefpanda',
    author='Mitchell Stokes',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    packages=['cefpanda'],
    install_requires=[
        'panda3d',
        'cefpython3',
    ]
)
