from collections import deque

import cv2
import numpy as np
from numba import jit

from bounding_boxes import scan, optimize_bounding_boxes

MAX_DIMENSION = 100000000


def gen_movement_frame(frames: list, shape):
    acc = np.zeros(shape, dtype='float32')
    i = 0
    for f in frames:
        i += 1
        acc += f * i
    acc = acc / ((1 + i) / 2 * i)
    acc[acc > 254] = 255
    return acc


@jit(nopython=True)
def numba_scale_box(b: (int, int, int, int), scale: float):
    return int(b[0] / scale), int(b[1] / scale), int(b[2] / scale), int(b[3] / scale)


class MotionDetector:
    def __init__(self,
                 bg_subs_scale_percent=0.25,
                 bg_skip_frames=50,
                 bg_history=15,
                 movement_frames_history=5,  # what amount of frames to use for
                 # current movement (to decrease the noise)
                 brightness_discard_level=20,  # if the pixel brightness is lower than
                 # this threshold, it's background
                 pixel_compression_ratio=0.1,
                 group_boxes=True,
                 expansion_step=1):
        self.bg_subs_scale_percent = bg_subs_scale_percent
        self.bg_skip_frames = bg_skip_frames
        self.bg_history = bg_history
        self.group_boxes = group_boxes
        self.expansion_step = expansion_step
        self.movement_fps_history = movement_frames_history
        self.brightness_discard_level = brightness_discard_level
        self.pixel_compression_ratio = pixel_compression_ratio

        self.bg_frames = deque(maxlen=bg_history)
        self.movement_frames = deque(maxlen=movement_frames_history)
        self.orig_frames = deque(maxlen=movement_frames_history)
        self.count = 0
        self.background_acc = None
        self.background_frame = None
        self.boxes = None
        self.movement = None
        self.color_movement = None
        self.gs_movement = None
        self.detection = None
        self.detection_boxed = None
        self.frame = None

    @classmethod
    def prepare(cls, f, width, height):
        return cv2.GaussianBlur(cv2.resize(f, (width, height), interpolation=cv2.INTER_CUBIC), (5, 5), 0)

    def __update_background(self, frame_fp32):
        if not self.count % self.bg_skip_frames == 0:
            return

        if self.movement_frames.maxlen == len(self.movement_frames):
            current_frame = self.movement_frames[0]
        else:
            current_frame = frame_fp32

        if self.background_acc is None:
            self.background_acc = frame_fp32
        else:
            self.background_acc = self.background_acc + current_frame

            if self.bg_frames.maxlen == len(self.bg_frames):
                subs_frame = self.bg_frames[0]
                self.background_acc = self.background_acc - subs_frame

        self.bg_frames.append(current_frame)

    def __detect_movement(self, frame_fp32):
        self.movement_frames.append(frame_fp32)
        movement_frame = gen_movement_frame(list(self.movement_frames), frame_fp32.shape)
        self.background_frame = self.background_acc / len(self.bg_frames)
        self.background_frame[self.background_frame > 254] = 255
        if len(self.bg_frames):
            movement = cv2.absdiff(movement_frame, self.background_frame)
        else:
            movement = np.zeros(movement_frame.shape)
        self.color_movement = movement
        movement[movement < self.brightness_discard_level] = 0
        movement[movement > 0] = 254
        movement = movement.astype('uint8')
        movement = cv2.cvtColor(movement, cv2.COLOR_BGR2GRAY)
        movement[movement > 0] = 254
        return movement

    def detect(self, f):
        self.orig_frames.append(f)

        width = int(f.shape[1] * self.bg_subs_scale_percent)
        height = int(f.shape[0] * self.bg_subs_scale_percent)

        detect_width = int(f.shape[1] * self.pixel_compression_ratio)
        detect_height = int(f.shape[0] * self.pixel_compression_ratio)

        self.frame = self.__class__.prepare(f, width, height)
        nf_fp32 = self.frame.astype('float32')
        self.__update_background(nf_fp32)

        self.movement = self.__detect_movement(nf_fp32)
        self.detection = cv2.resize(self.movement, (detect_width, detect_height), interpolation=cv2.INTER_CUBIC)
        boxes = self.__get_movement_zones(self.detection)

        self.count += 1

        if self.movement_frames.maxlen != len(self.movement_frames) or self.bg_frames.maxlen != len(self.bg_frames):
            return [], f

        return boxes, self.orig_frames[0]

    def __get_movement_zones(self, f):
        boxes = []

        # wait until the bg gets established to decrease the level of initial unstable noise
        if len(self.bg_frames) >= self.bg_history / 2:
            boxes = scan(f, self.expansion_step)
            if self.group_boxes:
                boxes = optimize_bounding_boxes(boxes)

        self.detection_boxed = self.detection.copy()
        for b in boxes:
            cv2.rectangle(self.detection_boxed, (b[0], b[1]), (b[2], b[3]), 250, 1)

        orig_boxes = []
        for b in boxes:
            orig_boxes.append(numba_scale_box(b, self.pixel_compression_ratio))

        self.boxes = orig_boxes
        return orig_boxes
