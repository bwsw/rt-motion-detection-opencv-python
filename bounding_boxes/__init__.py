from ctypes import PyDLL, py_object, c_int
from sys import exit
from os import path
import numpy as np

my_path = path.abspath(path.dirname(__file__))
path = path.join(my_path, "./bin/libmotion_detector_optimization.so")

try:
    lib = PyDLL(path)
    lib.c_scan.restype = py_object
    lib.c_scan.argtypes = [py_object, c_int]
    lib.c_find_bounding_boxes.restype = py_object
    lib.c_find_bounding_boxes.argtypes = [py_object]
    lib.c_pack.restype = py_object
    lib.c_pack.argtypes = [py_object, py_object]
except OSError:
    print("Error when loading lib")
    exit(1)


def scan(img: np.ndarray, expansion_step: int):
    return lib.c_scan(img, expansion_step)


def optimize_bounding_boxes(rectangles):
    if rectangles is None or not len(rectangles):
        return []
    return lib.c_find_bounding_boxes(rectangles)


def pack(rects: list, bins: list):
    return lib.c_pack(rects, bins)