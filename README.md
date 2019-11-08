# RealTime Motion Detection

You can download the video clip which is used in the demo at: https://box.bw-sw.com/f/c629c692d5c04b7caac6/?dl

Work example at: https://youtu.be/FCme11alEmc

## Detector usage

See `example.py` for usage.

## Detector parameters

* `bg_subs_scale_percent` - how much to scale initial frame before movement detection occurs (default 1/4);
* `bg_history` - the length of background accumulator ring buffer (default 15);
* `bg_history_collection_period_max` - defines how often update background ring buffer with frames from movement (default 1 - every frame);
* `movement_frames_history` - how much frames to keep in movement accumulator ring buffer (default 5);
* `brightness_discard_level` - threshold which is used to detect movement from the noise (default 20);
* `pixel_compression_ratio` - how much to compress the initial video for boxes search (default 20), means that every 20x20 px of initial frame will be resized to 1x1 of detection frame;
* `group_boxes` - group overlapping boxes into a single one or just keep them as they are (default True);
* `expansion_step` - how big is expansion algoritm step when it searches for boxes, lower steps lead to smaller performance and close objects are detected as separate, bigger step leads to faster algorithm performance and close objects can be detected as a single one.

## Sample usage

```python
import cv2
from time import time
from detector import MovementDetector

if __name__ == "__main__":

    cap = cv2.VideoCapture('helmets-v1-55.mp4')

    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    pixel_compression_ratio = 10

    detector = MovementDetector(pixel_compression_ratio=pixel_compression_ratio,
                                bg_history=20,
                                expansion_step=5)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        begin = time()
        detector.detect(frame)
        end = time()
        print(detector.count, 1000 * (end - begin), len(detector.bg_frames), len(detector.boxes))
        cv2.imshow('last_frame', detector.last_frame)
        cv2.imshow('detect_frame', detector.detection)
        cv2.imshow('diff_frame', detector.color_movement)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
```

## Author

The code is created by Ivan Kudriavtsev from [Bitworks Software](https://bitworks.software/) &ndash; custom software development company with focus on scalable, BigData & ML solutions for customers worldwide.

![Bitworks Software](https://github.com/bwsw/cloudstack-ui/blob/master/screens/15047882.png)
