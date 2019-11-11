import cv2
import numpy as np
from time import time
from detector import MotionDetector

if __name__ == "__main__":

    cap = cv2.VideoCapture('tmp/helmets-v1-55.mp4')

    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    detector = MotionDetector(bg_history=20)
    # , expansion_step=5

    res = []
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if frame is None:
            break
        begin = time()
        boxes = detector.detect(frame)
        end = time()
        res.append(1000 * (end - begin))
        print("StdDev: %.4f" % np.std(res), "Mean: %.4f" % np.mean(res), "Boxes found: ", len(boxes))

        for b in boxes:
            cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), (250, 255, 255), 1)

        cv2.imshow('orig_frame', frame)
        cv2.imshow('last_frame', detector.frame)
        cv2.imshow('detect_frame', detector.detection)
        cv2.imshow('diff_frame', detector.color_movement)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
