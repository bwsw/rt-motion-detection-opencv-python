import cv2
import numpy as np

from numba import jit
from collections import deque
from time import sleep
from opti_module.c_funcs import scan

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
def numba_intersection(a, b):
    start_x = max(min(a[0], a[2]), min(b[0], b[2]))
    start_y = max(min(a[1], a[3]), min(b[1], b[3]))
    end_x = min(max(a[0], a[2]), max(b[0], b[2]))
    end_y = min(max(a[1], a[3]), max(b[1], b[3]))

    if start_x < end_x and start_y < end_y:
        return True
    else:
        return False


@jit(nopython=True)
def numba_combine_rectangles(a, b):  # create bounding box for rect A & B
    start_x = min(a[0], b[0])
    start_y = min(a[1], b[1])
    end_x = max(a[2], b[2])
    end_y = max(a[3], b[3])
    return start_x, start_y, end_x, end_y


@jit(nopython=True, parallel=True)
def numba_combinations(rectangles):
    res = []
    for a in rectangles:
        for b in rectangles:
            if a != b:
                res.append((a, b))
    return res


def find_bounding_boxes(rectangles):
    if rectangles is None or not len(rectangles):
        return []

    intersected = True
    while intersected and len(rectangles) > 1:
        new_rectangles = set()
        remove_rectangles = set()
        for a, b in numba_combinations(rectangles):
            if numba_intersection(a, b):
                new_rectangles.add(numba_combine_rectangles(a, b))
                intersected = True
                remove_rectangles.add(a)
                remove_rectangles.add(b)

        if len(new_rectangles) == 0:
            intersected = False
        else:
            rectangles = rectangles.difference(remove_rectangles).union(new_rectangles)

    return rectangles


@jit(nopython=True)
def numba_inaccessible_point(r: int, c: int, height: int, width: int, avoid_pts: np.ndarray):
    return r < 0 or c < 0 or r >= height or c >= width or avoid_pts[r, c] == 1


@jit(nopython=True)
def numba_get_neighbors(expansion_step: int, r: int, c: int, height: int, width: int, avoid_points: np.ndarray):
    nl = []
    for i in range(-expansion_step, expansion_step + 1):
        for j in range(-expansion_step, expansion_step + 1):
            if not numba_inaccessible_point(r + i, c + j, height, width, avoid_points):
                avoid_points[r + i, c + j] = 1
                if abs(i) == expansion_step or abs(j) == expansion_step:
                    nl.append((r + i, c + j))

    return nl


@jit(nopython=True)
def numba_scale_box(b: (int, int, int, int), scale: float):
    return int(b[0] / scale), int(b[1] / scale), int(b[2] / scale), int(b[3] / scale)


@jit(nopython=True)
def numba_scan_box(expansion_step: int, height: int, width: int, avoid_points: np.ndarray, r: int, c: int):
    c_min = MAX_DIMENSION
    r_min = MAX_DIMENSION
    c_max = 0
    r_max = 0
    nl = [(r, c)]
    while len(nl) > 0:
        r, c = nl.pop()

        c_min = min(c_min, c)
        r_min = min(r_min, r)
        c_max = max(c_max, c)
        r_max = max(r_max, r)

        nl = nl + numba_get_neighbors(expansion_step, r, c, height, width, avoid_points)

    c_min = max(0, int(c_min - expansion_step))
    r_min = max(0, int(r_min - expansion_step))

    c_max = min(width - 1, int(c_max + expansion_step))
    r_max = min(height - 1, int(r_max + expansion_step))

    return [c_min, r_min, c_max, r_max]


class Scanner:
    def __init__(self, image, expansion_step=1):
        self.avoid_points = np.ones(image.shape, dtype=image.dtype)
        self.img = image
        self.expansion_step = expansion_step
        self.boxes = list()
        self.scan_points = list(np.argwhere(image > 0))
        self.height = image.shape[0]
        self.width = image.shape[1]
        for p in self.scan_points:
            self.avoid_points[p[0], p[1]] = 0

    def __update_boxes(self, cluster):
        self.boxes.append(cluster)

    def scan(self):
        while len(self.scan_points):
            (r, c) = self.scan_points.pop()
            if not self.__inaccessible_point(r, c):
                box = numba_scan_box(self.expansion_step, self.height, self.width, self.avoid_points, r, c)
                self.__update_boxes((*box,))
        return self.boxes

    def __inaccessible_point(self, r, c):
        return numba_inaccessible_point(r, c, self.height, self.width, self.avoid_points)


class MotionDetector:
    def __init__(self,
                 bg_subs_scale_percent=0.25,
                 bg_history=15,
                 movement_frames_history=5,  # what amount of frames to use for
                 # current movement (to decrease the noise)
                 brightness_discard_level=20,  # if the pixel brightness is lower than
                 # this threshold, it's background
                 pixel_compression_ratio=0.1,
                 group_boxes=True,
                 expansion_step=1):
        self.bg_subs_scale_percent = bg_subs_scale_percent
        self.bg_history = bg_history
        self.group_boxes = group_boxes
        self.expansion_step = expansion_step
        self.movement_fps_history = movement_frames_history
        self.brightness_discard_level = brightness_discard_level
        self.pixel_compression_ratio = pixel_compression_ratio

        self.bg_frames = deque(maxlen=bg_history)
        self.movement_frames = deque(maxlen=movement_frames_history)
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
        return boxes

    def __get_movement_zones(self, f):
        boxes = []

        # wait until the bg gets established to decrease the level of initial unstable noise
        if len(self.bg_frames) >= self.bg_history / 2:
            boxes = scan(f, self.expansion_step)
            if self.group_boxes:
                boxes = find_bounding_boxes(set(boxes))

        self.detection_boxed = self.detection.copy()
        for b in boxes:
            cv2.rectangle(self.detection_boxed, (b[0], b[1]), (b[2], b[3]), 250, 1)

        orig_boxes = []
        for b in boxes:
            orig_boxes.append(numba_scale_box(b, self.pixel_compression_ratio))

        self.boxes = orig_boxes
        return orig_boxes
