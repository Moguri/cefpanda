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
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest',
        'pylint==2.3.*',
        'pytest-pylint',
    ],
)
