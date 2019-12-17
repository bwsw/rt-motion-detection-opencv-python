from ctypes import PyDLL
from sys import exit
from os import path

my_path = path.abspath(path.dirname(__file__))
path = path.join(my_path, "./bin/libmotion_detector_optimization.so")

try:
    lib = PyDLL(path)
except OSError:
    print("Error when loading lib")
    exit(1)


def scan():
    return lib.c_scan()
