import numpy as np
from rectpack import newPacker
from numba import jit


def pack_images(frame, boxes, width, height):
    packer = newPacker(rotation=False)

    for b in boxes:
        packer.add_rect(height=b[2] - b[0], width=b[3] - b[1], rid=b)

    for i in range(0, int((frame.shape[0] + height) / height + 1) * int((frame.shape[1] + width) / width + 1)):
        packer.add_bin(height=width, width=height)
    packer.pack()
    rectangles = packer.rect_list()
    return copy_images(frame, rectangles, height, width)


def copy_images(frame, rectangles, height, width):
    results = []
    box_map = []
    for rect in rectangles:
        b, x, y, w, h, rid = rect
        if b + 1 > len(results):
            results.append(np.zeros((height, width, 3), dtype=frame.dtype))
        img = frame[rid[1]:rid[3], rid[0]:rid[2]]
        results[b][x:x + w, y:y + h] = img
        box_map.append((b, (x, y, x + w, y + h), (rid[1], rid[0], rid[3], rid[2])))

    return results, box_map
