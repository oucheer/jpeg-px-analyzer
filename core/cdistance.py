# -*- coding: utf-8 -*-
"""
C语言距离计算模块的Python ctypes封装
"""

import os
import ctypes
import numpy as np
import numpy.ctypeslib as npct

_dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distance_calculator.dll")

try:
    _lib = ctypes.CDLL(_dll_path)
    _dll_loaded = True
except OSError as e:
    print(f"Warning: Failed to load DLL: {e}")
    print("Will fall back to Python implementation")
    _dll_loaded = False

if _dll_loaded:
    _lib.pixels_to_mm.argtypes = [ctypes.c_int, ctypes.c_int]
    _lib.pixels_to_mm.restype = ctypes.c_float

    _lib.detect_horizontal_line.argtypes = [
        npct.ndpointer(ctypes.c_uint8, ndim=1, flags='C_CONTIGUOUS'),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int)
    ]
    _lib.detect_horizontal_line.restype = ctypes.c_int

    _lib.detect_vertical_line.argtypes = [
        npct.ndpointer(ctypes.c_uint8, ndim=1, flags='C_CONTIGUOUS'),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int)
    ]
    _lib.detect_vertical_line.restype = ctypes.c_int

    _lib.calculate_confidence.argtypes = [
        npct.ndpointer(ctypes.c_uint8, ndim=1, flags='C_CONTIGUOUS'),
        npct.ndpointer(ctypes.c_uint8, ndim=1, flags='C_CONTIGUOUS'),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ]
    _lib.calculate_confidence.restype = ctypes.c_int


def pixels_to_mm(pixels, dpi):
    if _dll_loaded:
        return float(_lib.pixels_to_mm(int(pixels), int(dpi)))
    else:
        if dpi <= 0:
            dpi = 300
        result = pixels * 25.4 / dpi
        return round(result, 1)


def detect_horizontal_line(binary_array):
    if _dll_loaded:
        if binary_array is None or binary_array.size == 0:
            return -1

        h, w = binary_array.shape
        binary_flat = binary_array.flatten().astype(np.uint8)

        out_pos = ctypes.c_int(0)
        result = _lib.detect_horizontal_line(
            binary_flat,
            w, h,
            ctypes.byref(out_pos)
        )

        if result:
            return int(out_pos.value)
        return -1
    else:
        return _python_detect_horizontal_line(binary_array)


def detect_vertical_line(binary_array):
    if _dll_loaded:
        if binary_array is None or binary_array.size == 0:
            return -1

        h, w = binary_array.shape
        binary_flat = binary_array.flatten().astype(np.uint8)

        out_pos = ctypes.c_int(0)
        result = _lib.detect_vertical_line(
            binary_flat,
            w, h,
            ctypes.byref(out_pos)
        )

        if result:
            return int(out_pos.value)
        return -1
    else:
        return _python_detect_vertical_line(binary_array)


def calculate_confidence(binary_array, gray_array, line_pos, dimension, axis):
    if _dll_loaded:
        if binary_array is None or gray_array is None:
            return 50

        h, w = binary_array.shape
        binary_flat = binary_array.flatten().astype(np.uint8)
        gray_flat = gray_array.flatten().astype(np.uint8)

        if axis == 'y':
            axis_val = 1
        else:
            axis_val = 0

        return int(_lib.calculate_confidence(
            binary_flat,
            gray_flat,
            int(line_pos),
            dimension,
            axis_val
        ))
    else:
        return _python_calculate_confidence(binary_array, gray_array, line_pos, dimension, axis)


def _python_detect_horizontal_line(binary_array):
    if binary_array is None:
        return -1

    h, w = binary_array.shape

    vertical_projection = np.sum(binary_array, axis=1) / 255

    threshold = w * 0.3

    in_line = False
    line_start = 0
    line_end = 0

    for y in range(h):
        if vertical_projection[y] > threshold:
            if not in_line:
                line_start = y
                in_line = True
        else:
            if in_line:
                line_end = y
                line_center = (line_start + line_end) // 2
                return line_center

    if in_line:
        return line_start

    return -1


def _python_detect_vertical_line(binary_array):
    if binary_array is None:
        return -1

    h, w = binary_array.shape

    horizontal_projection = np.sum(binary_array, axis=0) / 255

    threshold = h * 0.3

    in_line = False
    line_start = 0
    line_end = 0

    for x in range(w):
        if horizontal_projection[x] > threshold:
            if not in_line:
                line_start = x
                in_line = True
        else:
            if in_line:
                line_end = x
                line_center = (line_start + line_end) // 2
                return line_center

    if in_line:
        return line_start

    return -1


def _python_calculate_confidence(binary_array, gray_array, line_pos, dimension, axis):
    if binary_array is None or gray_array is None:
        return 50

    h, w = binary_array.shape

    if axis == 'y':
        line_region = binary_array[max(0, line_pos-5):min(h, line_pos+5), :]
        gray_region = gray_array[max(0, line_pos-5):min(h, line_pos+5), :]
    else:
        line_region = binary_array[:, max(0, line_pos-5):min(w, line_pos+5)]
        gray_region = gray_array[:, max(0, line_pos-5):min(w, line_pos+5)]

    if line_region.size == 0:
        return 50

    black_density = np.sum(line_region > 0) / line_region.size
    gray_value = np.mean(gray_region)
    contrast = (255 - gray_value) / 255
    continuity = black_density

    confidence = min(100, int(
        (black_density * 40 +
         contrast * 30 +
         continuity * 30)
    ))

    return max(10, confidence)


def is_c_available():
    return _dll_loaded
