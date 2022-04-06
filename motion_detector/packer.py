import numpy as np

from .bounding_boxes import pack


def pack_images(frame, boxes, width, height, box_filter=lambda x: True):
    list_rects = list()
    list_bins = list()

    for b in boxes:
        if box_filter(b):
            list_rects.append((b[2] - b[0], b[3] - b[1], b,))
    list_bins.append((width, height, int((frame.shape[0] + height) / height + 1) * int((frame.shape[1] + width) / width + 1),))

    rectangles = pack(rects=list_rects, bins=list_bins)
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
        box_map.append((b, (x, y, x + w, y + h), (rid[0], rid[1], rid[2], rid[3])))

    return results, box_map
