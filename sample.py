import cv2
import numpy as np

from time import time
from detector import MotionDetector
from packer import pack_images
from numba import jit


@jit(nopython=True)
def filter_fun(b):
    return ((b[2] - b[0]) * (b[3] - b[1])) > 300


if __name__ == "__main__":

    cap = cv2.VideoCapture('../video/output.mp4')
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    detector = MotionDetector(bg_history=5,
                              movement_frames_history=2,
                              brightness_discard_level=5,
                              bg_subs_scale_percent=0.2,
                              pixel_compression_ratio=0.1,
                              group_boxes=True,
                              expansion_step=5)

    # group_boxes=True can be used if one wants to get less boxes, which include all overlapping boxes

    b_height = 320
    b_width = 320

    res = []
    fc = dict()
    ctr = 0
    while True:
        # Capture frame-by-frame
        begin = time()
        ret, frame = cap.read()
        if frame is None:
            break

        boxes, frame = detector.detect(frame)
        # boxes hold all boxes around motion parts

        ## this code cuts motion areas from initial image and
        ## fills "bins" of 320x320 with such motion areas.
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
        it = (end - begin) * 1000

        res.append(it)
        print("StdDev: %.4f" % np.std(res), "Mean: %.4f" % np.mean(res), "Last: %.4f" % it,
              "Boxes found: ", len(boxes))

        # idx = 0
        # for r in results:
        #      idx += 1
        #      cv2.imshow('packed_frame_%d' % idx, r)

        ctr += 1
        nc = len(results)
        if nc in fc:
            fc[nc] += 1
        else:
            fc[nc] = 0

        if ctr % 100 == 0:
            print("Total Frames: ", ctr, "Packed Frames:", fc)

        # cv2.imshow('last_frame', frame)
        # cv2.imshow('detect_frame', detector.detection_boxed)
        # cv2.imshow('diff_frame', detector.color_movement)
        #
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    print(fc, ctr)
