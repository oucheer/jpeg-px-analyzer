# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 智能自动检测版
自动从图像中检测并计算实际距离
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4SmartMeasurement:
    """A4 纸张智能测量工具"""
    
    DEFAULT_DPI = 300
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.width = 0
        self.height = 0
        
        # 测量结果
        self.horizontal_mm = 0.0  # 水平距离（毫米）
        self.vertical_mm = 0.0   # 垂直距离（毫米）
        self.horizontal_px = 0   # 水平距离（像素）
        self.vertical_px = 0      # 垂直距离（像素）
        
        # 置信度
        self.horizontal_confidence = 0
        self.vertical_confidence = 0
        
        # 检测到的线条信息
        self.detected_lines = []
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
        self.detection_method = ""
    
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
        智能分析 - 自动检测并计算距离
        使用多种策略组合来提高准确性
        """
        if self.gray is None:
            self.status = "FAIL"
            self.error_message = "Image not loaded"
            return False
        
        # 策略1: 使用形态学梯度检测边缘
        if self._detect_with_morphology_gradient():
            self.detection_method = "Morphology Gradient"
            return self._finalize()
        
        # 策略2: 使用自适应边缘检测
        if self._detect_with_adaptive_edges():
            self.detection_method = "Adaptive Edge"
            return self._finalize()
        
        # 策略3: 使用投影法结合形态学
        if self._detect_with_projection_morphology():
            self.detection_method = "Projection + Morphology"
            return self._finalize()
        
        # 策略4: 直接边缘检测
        if self._detect_with_canny():
            self.detection_method = "Canny Edge"
            return self._finalize()
        
        self.status = "FAIL"
        self.error_message = "No clear grid lines detected"
        return False
    
    def _detect_with_morphology_gradient(self):
        """策略1: 形态学梯度检测"""
        # 扩展 ROI 区域以更好地捕捉线条
        roi_w = min(int(self.width * 0.25), 600)
        roi_h = min(int(self.height * 0.25), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 形态学梯度
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(roi, cv2.MORPH_GRADIENT, kernel)
        
        # 自适应阈值
        mean_val = np.mean(gradient)
        _, binary = cv2.threshold(gradient, mean_val * 0.5, 255, cv2.THRESH_BINARY)
        
        return self._extract_lines_from_binary(roi, binary)
    
    def _detect_with_adaptive_edges(self):
        """策略2: 自适应边缘检测"""
        roi_w = min(int(self.width * 0.25), 600)
        roi_h = min(int(self.height * 0.25), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 高斯模糊减少噪声
        blurred = cv2.GaussianBlur(roi, (3, 3), 0)
        
        # 自适应阈值 - 处理光照不均
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 5
        )
        
        # 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return self._extract_lines_from_binary(roi, binary)
    
    def _detect_with_projection_morphology(self):
        """策略3: 投影法 + 形态学"""
        roi_w = min(int(self.width * 0.25), 600)
        roi_h = min(int(self.height * 0.25), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 边缘检测
        edges = cv2.Canny(roi, 30, 100)
        
        # 膨胀连接断开的边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        return self._extract_lines_from_binary(roi, dilated)
    
    def _detect_with_canny(self):
        """策略4: Canny 边缘检测"""
        roi_w = min(int(self.width * 0.25), 600)
        roi_h = min(int(self.height * 0.25), 800)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 双阈值 Canny
        edges = cv2.Canny(roi, 20, 80)
        
        # 膨胀
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        return self._extract_lines_from_binary(roi, edges)
    
    def _extract_lines_from_binary(self, roi, binary):
        """从二值图像中提取线条位置"""
        h, w = binary.shape
        
        # 垂直投影
        v_proj = np.sum(binary, axis=0)
        # 水平投影
        h_proj = np.sum(binary, axis=1)
        
        # 归一化投影
        v_proj_norm = v_proj / (np.max(v_proj) + 1e-6)
        h_proj_norm = h_proj / (np.max(h_proj) + 1e-6)
        
        # 找峰值（线条位置）
        vertical_lines = self._find_peaks(v_proj_norm, w)
        horizontal_lines = self._find_peaks(h_proj_norm, h)
        
        if len(vertical_lines) == 0 or len(horizontal_lines) == 0:
            return False
        
        # 取第一条线条位置
        first_vertical = vertical_lines[0]
        first_horizontal = horizontal_lines[0]
        
        # 转换为毫米
        self.vertical_px = first_vertical
        self.horizontal_px = first_horizontal
        
        self.vertical_mm = round(first_vertical * 25.4 / self.dpi, 2)
        self.horizontal_mm = round(first_horizontal * 25.4 / self.dpi, 2)
        
        # 计算置信度
        self.vertical_confidence = min(100, int(v_proj_norm[first_vertical] * 100))
        self.horizontal_confidence = min(100, int(h_proj_norm[first_horizontal] * 100))
        
        # 存储检测到的线条
        self.detected_lines = {
            'vertical': vertical_lines[:5],
            'horizontal': horizontal_lines[:5]
        }
        
        return True
    
    def _find_peaks(self, projection, dimension):
        """找投影中的峰值位置"""
        peaks = []
        threshold = 0.15  # 降低阈值以检测更多线条
        
        # 局部最大值检测
        for i in range(2, dimension - 2):
            if projection[i] > threshold:
                if (projection[i] > projection[i-1] and 
                    projection[i] > projection[i-2] and
                    projection[i] > projection[i+1] and 
                    projection[i] > projection[i+2]):
                    peaks.append(i)
        
        return peaks
    
    def _finalize(self):
        """完成检测"""
        self.status = "SUCCESS"
        return True
    
    def generate_report(self):
        """生成详细测量报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 70)
        report.append("A4 纸张智能测量报告")
        report.append("=" * 70)
        report.append(f"\n测量时间：{timestamp}")
        report.append(f"图像文件：{self.filename}")
        report.append(f"图像尺寸：{self.width} × {self.height} 像素")
        report.append(f"DPI: {self.dpi}")
        report.append(f"检测方法：{self.detection_method}")
        
        if self.status == "SUCCESS":
            report.append("\n" + "-" * 70)
            report.append("自动计算结果")
            report.append("-" * 70)
            
            report.append(f"\n【水平距离 - 箭头 1】")
            report.append(f"  测量对象：纸张上边缘 → 第一条水平线")
            report.append(f"  像素距离：{self.horizontal_px} px")
            report.append(f"  计算距离：{self.horizontal_mm} mm")
            report.append(f"  置信度：{self.horizontal_confidence}%")
            
            report.append(f"\n【垂直距离 - 箭头 2】")
            report.append(f"  测量对象：纸张左边缘 → 第一条垂直线")
            report.append(f"  像素距离：{self.vertical_px} px")
            report.append(f"  计算距离：{self.vertical_mm} mm")
            report.append(f"  置信度：{self.vertical_confidence}%")
            
            report.append("\n" + "-" * 70)
            report.append("计算公式")
            report.append("-" * 70)
            report.append(f"  毫米 = 像素 × 25.4 ÷ DPI")
            report.append(f"  ")
            report.append(f"  水平：{self.horizontal_px} × 25.4 ÷ {self.dpi} = {self.horizontal_mm} mm")
            report.append(f"  垂直：{self.vertical_px} × 25.4 ÷ {self.dpi} = {self.vertical_mm} mm")
            
            if self.detected_lines:
                report.append("\n" + "-" * 70)
                report.append("检测到的线条位置")
                report.append("-" * 70)
                report.append(f"  垂直线 X 坐标：{self.detected_lines.get('vertical', [])}")
                report.append(f"  水平线 Y 坐标：{self.detected_lines.get('horizontal', [])}")
            
            report.append("\n" + "-" * 70)
            report.append("坐标系定义")
            report.append("-" * 70)
            report.append("  原点 (0, 0): 纸张左上角")
            report.append("  X 轴：水平向右为正")
            report.append("  Y 轴：垂直向下为正")
            
            report.append("\n" + "-" * 70)
            report.append("坐标示意图")
            report.append("-" * 70)
            report.append(f"""
    纸张左边缘           竖线 (X={self.vertical_mm}mm)
        ↓                  ↓
    ┌──┼────────────────┐ ← 上边缘 (Y=0)
    │  │                │
    │  │                │
    │  │                │
    │  ├────────────────┤ ← 横线 (Y={self.horizontal_mm}mm)
    │  │←→             │
    │  │{self.vertical_mm}mm            │
    │  │                │
    └──┴────────────────┘
        ↑
    原点 (0,0)
            """)
            
        else:
            report.append(f"\n测量失败：{self.error_message}")
        
        report.append("\n" + "=" * 70)
        report.append(f"状态：{self.status}")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def analyze_file(self, filepath):
        """主分析函数"""
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze()
        return self.generate_report()


def analyze_smart(filepath, output_path=None):
    """便捷分析函数"""
    tool = A4SmartMeasurement()
    report = tool.analyze_file(filepath)
    
    print(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存至：{output_path}")
    
    return tool


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python a4_smart_measure.py <image_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyze_smart(input_file, output_file)
