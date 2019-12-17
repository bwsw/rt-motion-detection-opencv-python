import sys

import subprocess
from setuptools import setup
from distutils.command.build import build


class Build(build):
    def run(self):
        if subprocess.call(["make"]) != 0:
            sys.exit(-1)


setup(
    name='motion detector optimization',
    packages=['opti_module'],
    cmdclass={
        'build': Build,
    }
)
