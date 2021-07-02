#!/usr/bin/env python

import subprocess
import sys
from distutils.command.build import build
from distutils.command.clean import clean

from setuptools import setup


class Build(build):
    def run(self):
        if subprocess.call(["make"]) != 0:
            sys.exit(-1)


class Clean(clean):
    def run(self):
        if subprocess.call(["make", "clean"]) != 0:
            sys.exit(-1)


class FClean(clean):
    def run(self):
        if subprocess.call(["make", "fclean"]) != 0:
            sys.exit(-1)


class Rebuild(FClean, Build):
    def run(self):
        if subprocess.call(["make", "re"]) != 0:
            sys.exit(-1)

setup(
    name='motion_detector_python',
    version='1.0',
    packages=['motion_detector'],
    package_data={'motion_detector': ['./bin/libmotion_detector_optimization.so']},
    cmdclass={
        'build': Build,
        'clean': Clean,
        'fclean': FClean,
        'rebuild': Rebuild
    }
)
