import cv2
import numpy as np

from numba import jit
from collections import deque

import itertools

MAX_DIMENSION = 100000000


def gen_movement_frame(frames, shape):
    acc = np.zeros(shape, dtype='float32')
    i = 0
    for f in frames:
        i += 1
        acc += f * i
    acc = acc / ((1 + i) / 2 * i)
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


def find_bounding_boxes(rectangles):
    if rectangles is None or not len(rectangles):
        return []

    intersected = True
    while intersected and len(rectangles) > 1:
        rectangles = list(set(rectangles))
        new_rectangles = []
        for a, b in itertools.combinations(rectangles, 2):
            if numba_intersection(a, b):
                new_rect = numba_combine_rectangles(a, b)
                new_rectangles.append(new_rect)
                intersected = True
                if a in rectangles:
                    rectangles.remove(a)

                if b in rectangles:
                    rectangles.remove(b)

        if len(new_rectangles) == 0:
            intersected = False
        else:
            rectangles = rectangles + new_rectangles

    return rectangles


@jit(nopython=True)
def numba_inaccessible_point(r: int, c: int, height: int, width: int, avoid_pts: np.ndarray):
    return r < 0 or c < 0 or r >= height or c >= width or avoid_pts[r, c] == 1


@jit(nopython=True)
def numba_get_neighbors(expansion_step: int, r: int, c: int, last_r: int, last_c: int, height: int, width: int,
                        avoid_points: np.ndarray):
    nl = []
    for i in range(-expansion_step, expansion_step + 1):
        for j in range(-expansion_step, expansion_step + 1):
            if not ((last_r + expansion_step >= r + i >= last_r - expansion_step) and (
                    last_c + expansion_step >= c + j >= last_c - expansion_step)) and \
                    not numba_inaccessible_point(r + i, c + j, height, width, avoid_points):
                avoid_points[r + i, c + j] = 1
                if abs(i) == expansion_step or abs(j) == expansion_step:
                    nl.append((r + i, c + j, r, c))

    return nl


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
                self.__update_boxes(self.__scan_box(r, c))
        return self.boxes

    def __inaccessible_point(self, r, c):
        return numba_inaccessible_point(r, c, self.height, self.width, self.avoid_points)

    def __scan_box(self, r, c):
        c_min = MAX_DIMENSION
        r_min = MAX_DIMENSION
        c_max = 0
        r_max = 0
        nl = [(r, c, -1, -1)]
        while len(nl) > 0:
            (r, c, last_r, last_c) = nl.pop()

            if c_min > c:
                c_min = c

            if r_min > r:
                r_min = r

            if c_max < c:
                c_max = c

            if r_max < r:
                r_max = r

            nl = self.__get_neighbours(r, c, last_r, last_c, nl)

        return (*[i if i >= 0 else 0 for i in
                  [int(c_min - self.expansion_step), int(r_min - self.expansion_step),
                   int(c_max + self.expansion_step), int(r_max + self.expansion_step)]],)

    def __get_neighbours(self, r, c, last_r, last_c, nl):
        return nl + numba_get_neighbors(self.expansion_step, r, c, last_r, last_c, self.height, self.width,
                                        self.avoid_points)


class MovementDetector:
    def __init__(self,
                 bg_subs_scale_percent=0.25,
                 bg_history=15,
                 bg_history_collection_period_max=1,
                 movement_frames_history=5,  # what amount of frames to use for
                 # current movement (to decrease the noise)
                 brightness_discard_level=20,  # if the pixel brightness is lower than
                 # this threshold, it's background
                 pixel_compression_ratio=20,
                 group_boxes=True,
                 expansion_step=1):
        self.bg_subs_scale_percent = bg_subs_scale_percent
        self.bg_history = bg_history
        self.group_boxes = group_boxes
        self.expansion_step = expansion_step
        self.bg_history_collection_period_max = bg_history_collection_period_max
        self.movement_fps_history = movement_frames_history
        self.brightness_discard_level = brightness_discard_level
        self.pixel_compression_ratio = pixel_compression_ratio

        self.bg_frames = deque(maxlen=bg_history)
        self.movement_frames = deque(maxlen=movement_frames_history)
        self.count = 0
        self.bg_skip = 1
        self.background_frame = None
        self.boxes = None
        self.movement = None
        self.color_movement = None
        self.gs_movement = None
        self.detection = None
        self.last_frame = None

    @classmethod
    def scale_and_blur(cls, f, width, height):
        return cv2.GaussianBlur(cv2.resize(f, (width, height), interpolation=cv2.INTER_CUBIC), (5, 5), 0)

    def __update_background(self, frame_fp32):
        if self.movement_frames.maxlen == len(self.movement_frames):
            current_frame = self.movement_frames[0]
        else:
            current_frame = frame_fp32

        if self.background_frame is None:
            self.background_frame = frame_fp32
        else:
            if self.count % self.bg_skip == 0:
                self.background_frame = self.background_frame + current_frame

                if self.bg_frames.maxlen == len(self.bg_frames):
                    subs_frame = self.bg_frames[0]
                    self.background_frame = self.background_frame - subs_frame

                self.bg_frames.append(current_frame)

                if self.bg_skip < self.bg_history_collection_period_max:
                    self.bg_skip += 1

    def __detect_movement(self, frame_fp32):
        self.movement_frames.append(frame_fp32)
        movement_frame = gen_movement_frame(self.movement_frames, frame_fp32.shape)
        movement = cv2.absdiff(movement_frame, self.background_frame / len(self.bg_frames))
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

        detect_width = int(f.shape[1] / self.pixel_compression_ratio)
        detect_height = int(f.shape[0] / self.pixel_compression_ratio)

        self.last_frame = self.__class__.scale_and_blur(f, width, height)

        nf_fp32 = self.last_frame.astype('float32')

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
            boxes = Scanner(f, self.expansion_step).scan()
            if self.group_boxes:
                boxes = find_bounding_boxes(boxes)

        for r in boxes:
            cv2.rectangle(self.detection, (r[0], r[1]), (r[2], r[3]), 250, 1)

        self.boxes = boxes
        return boxes
