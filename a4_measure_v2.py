# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 优化版 v2
针对用户实际需求：
- 自动检测图像中的线条位置
- 计算边缘到线条的距离（mm）
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasurementV2:
    """A4 纸张测量工具 v2 - 优化版"""
    
    DEFAULT_DPI = 300
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.width = 0
        self.height = 0
        
        # 测量结果
        self.horizontal_mm = 0.0
        self.vertical_mm = 0.0
        self.horizontal_px = 0
        self.vertical_px = 0
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
    
    def load_image(self, filepath):
        """加载图像并解析 DPI"""
        if not os.path.exists(filepath):
            self.status = "FAIL"
            self.error_message = "File not found"
            return False
        
        self.filename = os.path.basename(filepath)
        
        try:
            self.image = cv2.imread(filepath)
            if self.image is None:
                self.status = "FAIL"
                self.error_message = "Unsupported format"
                return False
            
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.height, self.width = self.gray.shape
            
        except Exception as e:
            self.status = "FAIL"
            self.error_message = "File corrupted"
            return False
        
        self.dpi = self._extract_dpi(filepath)
        return True
    
    def _extract_dpi(self, filepath):
        """解析 EXIF DPI"""
        try:
            image = Image.open(filepath)
            exif_data = image._getexif()
            
            if exif_data is not None:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['XResolution', 'YResolution']:
                        if isinstance(value, tuple):
                            return int(value[0]) if value[1] == 1 else int(value[0] / value[1])
                        else:
                            return int(value)
            
            return self.DEFAULT_DPI
            
        except Exception:
            return self.DEFAULT_DPI
    
    def analyze(self):
        """
        分析图像，检测线条位置并计算距离
        """
        if self.gray is None:
            self.status = "FAIL"
            self.error_message = "Image not loaded"
            return False
        
        # 尝试多种策略
        strategies = [
            self._detect_deep_lines,      # 检测深色粗线条
            self._detect_any_lines,        # 检测任何可见线条
            self._detect_grid_lines,       # 检测网格线
        ]
        
        for strategy in strategies:
            if strategy():
                self.status = "SUCCESS"
                return True
        
        self.status = "FAIL"
        self.error_message = "No lines detected in image"
        return False
    
    def _detect_deep_lines(self):
        """策略1: 检测深色粗线条"""
        # 扩大 ROI 区域到中心，以便更好地捕捉线条
        roi_w = min(int(self.width * 0.4), 800)
        roi_h = min(int(self.height * 0.4), 1000)
        
        # 检查图像中心区域
        for offset_y in [0, 50, 100, 150, 200]:
            for offset_x in [0, 50, 100, 150, 200]:
                roi = self.gray[offset_y:offset_y+roi_h, offset_x:offset_x+roi_w]
                if roi.size == 0:
                    continue
                
                # 检测深色线条
                _, binary = cv2.threshold(roi, 80, 255, cv2.THRESH_BINARY_INV)
                
                # 投影分析
                v_proj = np.sum(binary, axis=0)
                h_proj = np.sum(binary, axis=1)
                
                # 找第一个峰值
                vertical_line = self._find_first_peak(v_proj)
                horizontal_line = self._find_first_peak(h_proj)
                
                if vertical_line > 0 and horizontal_line > 0:
                    # 转换为原图坐标
                    self.vertical_px = vertical_line + offset_x
                    self.horizontal_px = horizontal_line + offset_y
                    
                    # 转换为毫米
                    self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi, 2)
                    self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi, 2)
                    
                    return True
        
        return False
    
    def _detect_any_lines(self):
        """策略2: 检测任何可见线条"""
        roi_w = min(int(self.width * 0.3), 600)
        roi_h = min(int(self.height * 0.3), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 边缘检测
        edges = cv2.Canny(roi, 20, 60)
        
        # 投影
        v_proj = np.sum(edges, axis=0)
        h_proj = np.sum(edges, axis=1)
        
        # 找峰值
        vertical_line = self._find_first_peak(v_proj)
        horizontal_line = self._find_first_peak(h_proj)
        
        if vertical_line > 0 and horizontal_line > 0:
            self.vertical_px = vertical_line
            self.horizontal_px = horizontal_line
            
            self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi, 2)
            self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi, 2)
            
            return True
        
        return False
    
    def _detect_grid_lines(self):
        """策略3: 检测网格线"""
        roi_w = min(int(self.width * 0.3), 600)
        roi_h = min(int(self.height * 0.3), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 形态学梯度
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(roi, cv2.MORPH_GRADIENT, kernel)
        
        # 阈值
        _, binary = cv2.threshold(gradient, 15, 255, cv2.THRESH_BINARY)
        
        # 投影
        v_proj = np.sum(binary, axis=0)
        h_proj = np.sum(binary, axis=1)
        
        # 找峰值
        vertical_line = self._find_first_peak(v_proj)
        horizontal_line = self._find_first_peak(h_proj)
        
        if vertical_line > 0 and horizontal_line > 0:
            self.vertical_px = vertical_line
            self.horizontal_px = horizontal_line
            
            self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi, 2)
            self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi, 2)
            
            return True
        
        return False
    
    def _find_first_peak(self, projection):
        """找第一个峰值位置"""
        if len(projection) == 0:
            return 0
        
        max_val = np.max(projection)
        if max_val == 0:
            return 0
        
        threshold = max_val * 0.1  # 10%阈值
        
        # 找第一个超过阈值的点
        for i in range(len(projection)):
            if projection[i] > threshold:
                # 检查是否是局部最大值
                if i > 0 and i < len(projection) - 1:
                    if projection[i] >= projection[i-1] and projection[i] >= projection[i+1]:
                        return i
                elif i == 0 and projection[i] >= projection[i+1]:
                    return i
                elif i == len(projection) - 1 and projection[i] >= projection[i-1]:
                    return i
        
        return 0
    
    def generate_report(self):
        """生成报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 60)
        report.append("A4 纸张测量报告 (v2)")
        report.append("=" * 60)
        report.append(f"\n测量时间：{timestamp}")
        report.append(f"图像文件：{self.filename}")
        report.append(f"图像尺寸：{self.width} × {self.height} 像素")
        report.append(f"DPI: {self.dpi}")
        
        if self.status == "SUCCESS":
            report.append("\n" + "-" * 60)
            report.append("测量结果")
            report.append("-" * 60)
            
            report.append(f"\n【箭头 1 - 水平距离】")
            report.append(f"  纸张上边缘 → 水平线条")
            report.append(f"  像素距离：{self.horizontal_px} px")
            report.append(f"  计算距离：{self.horizontal_mm} mm")
            
            report.append(f"\n【箭头 2 - 垂直距离】")
            report.append(f"  纸张左边缘 → 垂直线条")
            report.append(f"  像素距离：{self.vertical_px} px")
            report.append(f"  计算距离：{self.vertical_mm} mm")
            
            report.append("\n" + "-" * 60)
            report.append("计算过程")
            report.append("-" * 60)
            report.append(f"  毫米 = 像素 × 25.4 ÷ DPI")
            report.append(f"  ")
            report.append(f"  水平：{self.horizontal_px} × 25.4 ÷ {self.dpi} = {self.horizontal_mm} mm")
            report.append(f"  垂直：{self.vertical_px} × 25.4 ÷ {self.dpi} = {self.vertical_mm} mm")
            
            report.append("\n" + "-" * 60)
            report.append("坐标系定义")
            report.append("-" * 60)
            report.append("  原点 (0,0): 纸张左上角")
            report.append("  X轴: 水平向右")
            report.append("  Y轴: 垂直向下")
            
        else:
            report.append(f"\n测量失败：{self.error_message}")
        
        report.append("\n" + "=" * 60)
        report.append(f"状态：{self.status}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def analyze_file(self, filepath):
        """分析文件"""
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze()
        return self.generate_report()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python a4_measure_v2.py <image_file>")
        sys.exit(1)
    
    tool = A4MeasurementV2()
    report = tool.analyze_file(sys.argv[1])
    print(report)


if __name__ == "__main__":
    main()
