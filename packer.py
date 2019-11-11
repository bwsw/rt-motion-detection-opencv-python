import numpy as np


class DetectionsPacker:

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def pack(self, f, boxes):
        from rectpack import newPacker

        height = self.height
        width = self.width

        packer = newPacker(rotation=False)

        for b in boxes:
            packer.add_rect(height=b[2] - b[0], width=b[3] - b[1], rid=b)

        results = []
        for i in range(0, int(f.shape[0] * f.shape[1] / (height * width)) + 2):
            packer.add_bin(height=width, width=height)
        packer.pack()

        rects = packer.rect_list()

        for rect in rects:
            b, x, y, w, h, rid = rect
            if b + 1 > len(results):
                results.append(np.zeros((height, width, 3), dtype=f.dtype))
            img = f[rid[1]:rid[3], rid[0]:rid[2]]
            results[b][x:x + w, y:y + h] = img

        return results
