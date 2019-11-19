import cv2
import numpy as np

from time import time
from detector import MotionDetector
from packer import pack_images
from numba import jit


@jit(nopython=True)
def filter_fun(b):
    return ((b[2] - b[0]) * (b[3] - b[1])) > 1000


if __name__ == "__main__":

    cap = cv2.VideoCapture('tmp/helmets-v1-55.mp4')

    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    detector = MotionDetector(bg_history=20,
                              group_boxes=False,
                              expansion_step=5)

    # group_boxes=True can be used if one wants to get less boxes, which include all overlapping boxes

    b_height = 512
    b_width = 512

    res = []
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if frame is None:
            break
        begin = time()
        boxes = detector.detect(frame)
        # boxes hold all boxes around motion parts

        ## this code cuts motion areas from initial image and
        ## fills "bins" of 512x512 with such motion areas.
        ##
        results = []
        if boxes:
            results, box_map = pack_images(frame=frame, boxes=boxes, width=b_width, height=b_height,
                                           box_filter=filter_fun)
            # box_map holds list of mapping between image placement in packed bins and original boxes

        ## end

        for b in boxes:
            cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), (0, 0, 255), 1)

        end = time()
        res.append(1000 * (end - begin))
        print("StdDev: %.4f" % np.std(res), "Mean: %.4f" % np.mean(res), "Boxes found: ", len(boxes))

        idx = 0
        for r in results:
            idx += 1
            cv2.imshow('packed_frame_%d' % idx, r)

        cv2.imshow('last_frame', frame)
        cv2.imshow('detect_frame', detector.detection)
        # cv2.imshow('diff_frame', detector.color_movement)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
