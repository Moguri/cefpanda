from setuptools import setup

__version__ = ''
#pylint: disable=exec-used
exec(open('cefpanda/version.py').read())

setup(
    name='cefpanda',
    version=__version__,
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
