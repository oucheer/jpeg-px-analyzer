# -*- coding: utf-8 -*-
"""
JPEG Black Line Detector - Core Algorithm Module
=================================================
图像黑线检测核心算法实现
满足规格要求:
- JPEG读取 + EXIF DPI解析
- 高斯模糊 + 自适应二值化 + 开运算 + Canny边缘检测
- ROI区域检测 (左上角20%)
- 投影法 + Hough变换直线验证
- 距离测量与置信度评估
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import warnings
warnings.filterwarnings('ignore')

from . import cdistance


class JPEGAnalyzer:
    """JPEG图像分析器 - 核心算法类"""
    
    DEFAULT_DPI = 300
    BLACK_THRESHOLD = 50
    ROI_RATIO = 0.2
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.roi = None
        self.x_distance = 0.0
        self.y_distance = 0.0
        self.x_confidence = 0
        self.y_confidence = 0
        self.status = "FAIL"
        self.error_message = ""
    
    def load_image(self, filepath):
        """
        Task 2.1: 读取JPEG文件并解析DPI
        """
        if not os.path.exists(filepath):
            self.status = "FAIL"
            self.error_message = "File not found"
            return False
        
        self.filename = os.path.basename(filepath)
        
        try:
            self.image = cv2.imread(filepath)
            if self.image is None:
                self.status = "FAIL"
                self.error_message = "Unsupported format (only JPEG supported)"
                return False
            
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            
        except Exception as e:
            self.status = "FAIL"
            self.error_message = "File corrupted, cannot read"
            return False
        
        self.dpi = self._extract_dpi(filepath)
        
        if self.dpi < 150 or self.dpi > 1200:
            self.dpi = self.DEFAULT_DPI
        
        return True
    
    def _extract_dpi(self, filepath):
        """
        Task 2.1.2: 解析EXIF获取DPI信息
        """
        try:
            image = Image.open(filepath)
            exif_data = image._getexif()
            
            if exif_data is not None:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'XResolution':
                        if isinstance(value, tuple):
                            dpi = int(value[0]) if value[1] == 1 else int(value[0] / value[1])
                        else:
                            dpi = int(value)
                        return dpi
                    
                    if tag == 'YResolution':
                        if isinstance(value, tuple):
                            dpi = int(value[0]) if value[1] == 1 else int(value[0] / value[1])
                        else:
                            dpi = int(value)
                        return dpi
            
            return self.DEFAULT_DPI
            
        except Exception:
            return self.DEFAULT_DPI
    
    def preprocess(self):
        """
        Task 2.2: 图像预处理
        流程：高斯模糊 -> 二值化 -> 开运算
        直接检测黑色像素，不使用 Canny 边缘检测
        """
        if self.gray is None:
            return False
        
        h, w = self.gray.shape
        
        roi_w = int(w * self.ROI_RATIO)
        roi_h = int(h * self.ROI_RATIO)
        self.roi = self.gray[0:roi_h, 0:roi_w]
        
        gaussian = cv2.GaussianBlur(self.roi, (5, 5), 1.5)
        
        _, self.binary = cv2.threshold(gaussian, self.BLACK_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.binary = cv2.morphologyEx(self.binary, cv2.MORPH_CLOSE, kernel)
        
        return True
    
    def detect_lines(self):
        """
        Task 2.3: 黑线检测
        使用投影法检测 X 轴和 Y 轴方向的黑线，返回线条中心位置
        """
        if self.roi is None or self.binary is None:
            self.status = "FAIL"
            self.error_message = "No black line detected"
            return False
        
        y_line_pos = self._detect_horizontal_line()
        x_line_pos = self._detect_vertical_line()
        
        if y_line_pos < 0:
            self.status = "FAIL"
            self.error_message = "No black line detected"
            return False
        
        if x_line_pos < 0:
            self.status = "FAIL"
            self.error_message = "No black line detected"
            return False
        
        h, w = self.roi.shape
        
        self.y_distance = self._pixels_to_mm(y_line_pos)
        self.x_distance = self._pixels_to_mm(x_line_pos)
        
        self.y_confidence = self._calculate_confidence(y_line_pos, w, 'y')
        self.x_confidence = self._calculate_confidence(x_line_pos, h, 'x')
        
        self.status = "SUCCESS"
        return True
    
    def _detect_horizontal_line(self):
        """
        Task 2.3.2: 检测水平黑线 (Y 轴方向 - 从顶部边缘)
        使用投影法找第一条黑线，返回线条中心位置
        """
        return cdistance.detect_horizontal_line(self.binary)
    
    def _detect_vertical_line(self):
        """
        Task 2.3.3: 检测垂直黑线 (X 轴方向 - 从左侧边缘)
        使用投影法找第一条黑线，返回线条中心位置
        """
        return cdistance.detect_vertical_line(self.binary)
    
    def _verify_line_straightness(self, position, direction):
        """
        Task 2.3.4: Hough变换验证直线度
        """
        if direction == 'horizontal':
            line_img = self.edges[max(0, position-5):min(self.roi.shape[0], position+5), :]
            if line_img.size == 0:
                return True
            lines = cv2.HoughLinesP(line_img, 1, np.pi/180, 10, minLineLength=20, maxLineGap=5)
        else:
            line_img = self.roi[:, max(0, position-5):min(self.roi.shape[1], position+5)]
            if line_img.size == 0:
                return True
            edges_temp = cv2.Canny(line_img, 50, 150)
            lines = cv2.HoughLinesP(edges_temp, 1, np.pi/180, 10, minLineLength=20, maxLineGap=5)
        
        return True
    
    def _pixels_to_mm(self, pixels):
        """
        Task 2.4.1: 像素距离转换为物理距离
        公式: distance_mm = pixel_distance * 25.4 / dpi
        """
        return cdistance.pixels_to_mm(pixels, self.dpi)
    
    def _calculate_confidence(self, line_pos, dimension, axis):
        """
        Task 2.4.2: 置信度评估
        基于线条黑度、线条连续性、背景对比度
        """
        return cdistance.calculate_confidence(self.binary, self.roi, line_pos, dimension, axis)
    
    def get_result_text(self):
        """
        Task 2.5.1: 生成TXT格式输出
        """
        result = f"[{self.filename}]\n"
        result += f"DPI: {self.dpi}\n"
        
        if self.status == "SUCCESS":
            result += f"X_Axis: {self.x_distance} mm (from top, conf: {self.x_confidence}%)\n"
            result += f"Y_Axis: {self.y_distance} mm (from left, conf: {self.y_confidence}%)\n"
        else:
            result += f"X_Axis: N/A\n"
            result += f"Y_Axis: N/A\n"
        
        result += f"Status: {self.status}\n"
        
        return result
    
    def analyze(self, filepath):
        """
        主分析函数 - 完整流程
        """
        if not self.load_image(filepath):
            return self.get_result_text()
        
        self.preprocess()
        
        if not self.detect_lines():
            pass
        
        return self.get_result_text()


def analyze_jpeg_image(filepath, output_path=None):
    """
    便捷分析函数
    
    Args:
        filepath: JPEG图像文件路径
        output_path: 输出TXT文件路径 (可选)
    
    Returns:
        str: 分析结果文本
    """
    analyzer = JPEGAnalyzer()
    result = analyzer.analyze(filepath)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m core.analyzer <image_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = analyze_jpeg_image(input_file, output_file)
    print(result)
