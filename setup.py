from setuptools import setup

__version__ = ''
#pylint: disable=exec-used
exec(open('cefpanda/version.py').read())

setup(
    version=__version__,
    keywords='panda3d gamedev',
    packages=['cefpanda'],
    install_requires=[
        'panda3d',
        'cefpython3',
    ]
)
