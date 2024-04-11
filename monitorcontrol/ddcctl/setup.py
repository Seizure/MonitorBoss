from Cython.Build import cythonize
from setuptools import Extension
from setuptools import setup

setup(
    name='macosddc',
    ext_modules=cythonize([
        Extension('macosddc', ['macosddc.pyx', 'ddcctl.m'])
    ]),
)
