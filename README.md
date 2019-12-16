# Noise-Tolerant High Performance Motion Detector

The motion detector presented here is developed to be noise-tolerant &ndash; webcam noise, light noise, athmosphere turbulence noise, different kinds of tremblings can be successfully handled.

You can download the video clip which is used in the demo at: https://box.bw-sw.com/f/c629c692d5c04b7caac6/?dl

Place it in the `tmp` directory.

Algorithm demonstration video screencast can be found at: https://youtu.be/FCme11alEmc

## Detector usage and parameters

* `bg_subs_scale_percent` &ndash; how much to scale initial frame before movement detection occurs (default: **1/4**);
* `bg_history` &ndash; the length of background accumulator ring buffer (default: **15**);
* `bg_history_collection_period_max` &ndash; defines how often update background ring buffer with frames from movement (default: **1** &ndash; every frame);
* `movement_frames_history` &ndash; how much frames to keep in movement accumulator ring buffer (default: **5**);
* `brightness_discard_level` &ndash; threshold which is used to detect movement from the noise (default: **20**);
* `pixel_compression_ratio` &ndash; how much to compress the initial video for boxes search (default: **0.1**), means that every **10x10 px** of initial frame will be resized to **1x1 px** of detection frame;
* `group_boxes` &ndash; group overlapping boxes into a single one or just keep them as they are (default: **True**);
* `expansion_step` &ndash; how big is expansion algorithm step when it searches for boxes, lower steps lead to smaller performance and close objects are detected as separate, bigger step leads to faster algorithm performance and close objects can be detected as a single one (default: **1**).

```python
import cv2
import numpy as np

from time import time
from detector import MotionDetector
from packer import pack_images

if __name__ == "__main__":

    cap = cv2.VideoCapture('tmp/helmets-v1-55.mp4')

    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    detector = MotionDetector(bg_history=15,
                              bg_subs_scale_percent=0.25,
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
                                           box_filter=lambda b: ((b[2] - b[0]) * (b[3] - b[1])) > 1000)
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
        # cv2.imshow('detect_frame', detector.detection)
        # cv2.imshow('diff_frame', detector.color_movement)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

```

## Performance

The performance depends **greatly** from the values of following detector parameters:

* Background substraction scale [`bg_subs_scale_percent`] (default 1/4), which leads to 480x230 frame for initial 1480x920 frame.
* Size of the frame which is used to search for bounding boxes [`pixel_compression_ratio`] (default 1/10), which leads to 148x92 for initial 1480x920 frame.
* Expansion step [`expansion_step`] which is used to find bounding boxes.

So, for the sample [video](https://box.bw-sw.com/f/c629c692d5c04b7caac6/?dl) (1480x920@30FPS) and all these parameters set to default the expected performance results for a single frame processing are:

* Mean frame processing time is `8.7262 ms`
* Standard deviation is `8.9909 ms`

on `Intel(R) Core(TM) i5-7440HQ CPU @ 2.80GHz` CPU.
