# -*- coding: utf-8 -*-
"""
C扩展接口模块 - Python绑定
"""

import ctypes
import numpy as np
import os

class LineDetector:
    """C语言线条检测器的Python封装"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._lib = None
        self._load_library()
    
    def _load_library(self):
        """加载C DLL"""
        dll_paths = [
            os.path.join(os.path.dirname(__file__), 'distance', 'line_detector.dll'),
            os.path.join(os.path.dirname(__file__), '..', 'core', 'distance', 'line_detector.dll'),
            r"d:\work\AI\AI Use\jpeg analyzer\core\distance\line_detector.dll",
        ]
        
        for dll_path in dll_paths:
            if os.path.exists(dll_path):
                try:
                    self._lib = ctypes.CDLL(dll_path)
                    self._setup_functions()
                    return
                except Exception as e:
                    print(f"Failed to load {dll_path}: {e}")
        
        raise RuntimeError("Failed to load line_detector.dll")
    
    def _setup_functions(self):
        """设置函数签名"""
        self._lib.detect_lines_multi_strategy.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int)
        ]
        self._lib.detect_lines_multi_strategy.restype = ctypes.c_int
        
        self._lib.pixels_to_mm.argtypes = [ctypes.c_int, ctypes.c_int]
        self._lib.pixels_to_mm.restype = ctypes.c_float
        
        self._lib.gaussian_blur_uint8.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int
        ]
        self._lib.gaussian_blur_uint8.restype = ctypes.c_int
        
        self._lib.sobel_edge_detection.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int
        ]
        self._lib.sobel_edge_detection.restype = ctypes.c_int
    
    def detect_lines(self, gray_array, edge_margin=15):
        """检测线条位置
        
        Args:
            gray_array: numpy灰度图像数组 (H x W)
            edge_margin: 边缘忽略距离
            
        Returns:
            tuple: (vertical_px, horizontal_px) 或 (None, None) 如果失败
        """
        if not isinstance(gray_array, np.ndarray):
            raise ValueError("gray_array must be a numpy array")
        
        if gray_array.dtype != np.uint8:
            gray_array = gray_array.astype(np.uint8)
        
        h, w = gray_array.shape
        
        gray_flat = gray_array.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        
        vertical_px = ctypes.c_int()
        horizontal_px = ctypes.c_int()
        
        result = self._lib.detect_lines_multi_strategy(
            gray_flat,
            ctypes.c_int(w),
            ctypes.c_int(h),
            ctypes.c_int(edge_margin),
            ctypes.byref(vertical_px),
            ctypes.byref(horizontal_px)
        )
        
        if result == 1:
            return vertical_px.value, horizontal_px.value
        else:
            return None, None
    
    def pixels_to_mm(self, pixels, dpi=600):
        """像素转毫米
        
        Args:
            pixels: 像素值
            dpi: DPI
            
        Returns:
            float: 毫米值
        """
        return self._lib.pixels_to_mm(ctypes.c_int(pixels), ctypes.c_int(dpi))


_line_detector = None

def get_line_detector():
    """获取线条检测器单例"""
    global _line_detector
    if _line_detector is None:
        _line_detector = LineDetector()
    return _line_detector


def detect_lines(gray_array, edge_margin=15):
    """便捷函数：检测线条位置
    
    Args:
        gray_array: numpy灰度图像数组
        edge_margin: 边缘忽略距离
        
    Returns:
        tuple: (vertical_px, horizontal_px)
    """
    detector = get_line_detector()
    return detector.detect_lines(gray_array, edge_margin)


def pixels_to_mm(pixels, dpi=600):
    """便捷函数：像素转毫米"""
    detector = get_line_detector()
    return detector.pixels_to_mm(pixels, dpi)
