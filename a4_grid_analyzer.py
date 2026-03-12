# -*- coding: utf-8 -*-
"""
A4 纸张网格分析工具 - 专用版本
针对均匀网格图像的测量方案
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4GridAnalyzer:
    """A4 纸张网格分析器 - 针对均匀网格"""
    
    DEFAULT_DPI = 300
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.width = 0
        self.height = 0
        
        # 测量结果
        self.grid_spacing_px = 0  # 网格间距（像素）
        self.grid_spacing_mm = 10.0  # 网格间距（毫米）- 默认 10mm
        
        # 第一条线位置
        self.first_vertical_x = 0  # 第一条垂直线 X 坐标
        self.first_horizontal_y = 0  # 第一条水平线 Y 坐标
        
        # 置信度
        self.confidence = 0
        
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
                self.error_message = "Unsupported format (only JPEG supported)"
                return False
            
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.height, self.width = self.gray.shape
            
        except Exception as e:
            self.status = "FAIL"
            self.error_message = "File corrupted, cannot read"
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
    
    def analyze_grid(self):
        """分析网格结构"""
        if self.gray is None:
            return False
        
        # ROI: 左上角区域
        roi_w = int(self.width * 0.3)
        roi_h = int(self.height * 0.3)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 边缘检测
        edges = cv2.Canny(roi, 50, 150)
        
        # 膨胀
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # 投影分析
        h_proj = np.sum(edges, axis=0)
        v_proj = np.sum(edges, axis=1)
        
        # 找峰值间隔（网格间距）
        vertical_lines = self._find_peaks(h_proj)
        horizontal_lines = self._find_peaks(v_proj)
        
        if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
            self.status = "FAIL"
            self.error_message = "无法检测网格结构"
            return False
        
        # 计算网格间距
        v_spacing = np.median(np.diff(vertical_lines))
        h_spacing = np.median(np.diff(horizontal_lines))
        self.grid_spacing_px = int((v_spacing + h_spacing) / 2)
        
        # 第一条线位置
        self.first_vertical_x = vertical_lines[0]
        self.first_horizontal_y = horizontal_lines[0]
        
        # 计算物理间距
        self.grid_spacing_mm = round(self.grid_spacing_px * 25.4 / self.dpi, 2)
        
        # 置信度
        self.confidence = min(100, int(len(vertical_lines) * 10))
        
        self.status = "SUCCESS"
        return True
    
    def _find_peaks(self, projection):
        """找投影峰值（线条位置）"""
        threshold = np.max(projection) * 0.3
        peaks = []
        in_peak = False
        peak_start = 0
        
        for i, val in enumerate(projection):
            if val > threshold:
                if not in_peak:
                    peak_start = i
                    in_peak = True
            else:
                if in_peak:
                    peak_center = (peak_start + i) // 2
                    peaks.append(peak_center)
                    in_peak = False
        
        return peaks
    
    def generate_report(self):
        """生成测量报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 70)
        report.append("A4 纸张网格分析报告")
        report.append("=" * 70)
        report.append(f"\n测量时间：{timestamp}")
        report.append(f"图像文件：{self.filename}")
        report.append(f"图像尺寸：{self.width} × {self.height} 像素")
        report.append(f"DPI: {self.dpi}")
        
        if self.status == "SUCCESS":
            report.append("\n" + "-" * 70)
            report.append("网格结构分析")
            report.append("-" * 70)
            report.append(f"网格间距：{self.grid_spacing_px} 像素 = {self.grid_spacing_mm} mm")
            report.append(f"第一条垂直线位置：X = {self.first_vertical_x} px")
            report.append(f"第一条水平线位置：Y = {self.first_horizontal_y} px")
            
            report.append("\n" + "-" * 70)
            report.append("测量说明")
            report.append("-" * 70)
            report.append("由于图像为均匀网格（无 L 形坐标线），建议测量方案:")
            report.append("")
            report.append("方案 1: 以第一条网格线交点为原点")
            report.append(f"  - 原点：({self.first_vertical_x}, {self.first_horizontal_y})")
            report.append(f"  - 到左边缘距离：{self.first_vertical_x * 25.4 / self.dpi:.2f} mm")
            report.append(f"  - 到上边缘距离：{self.first_horizontal_y * 25.4 / self.dpi:.2f} mm")
            report.append("")
            report.append("方案 2: 手动指定原点")
            report.append("  - 请在图像编辑软件中标记原点位置")
            report.append("  - 或使用带 L 形坐标线的图像")
            
            report.append("\n" + "-" * 70)
            report.append("网格示意图")
            report.append("-" * 70)
            report.append(f"""
    左边缘          第一条垂直线 (X={self.first_vertical_x}px)
        ↓                ↓
    ┌──┼────────────────┐ ← 上边缘 (Y=0)
    │  │                │
    │  ├────────────────┤ ← 第一条水平线 (Y={self.first_horizontal_y}px)
    │  │←→              │
    │  │{self.first_vertical_x * 25.4 / self.dpi:.2f}mm          │
    │  │                │
    └──┴────────────────┘
        网格间距：{self.grid_spacing_mm} mm ({self.grid_spacing_px} px)
            """)
        else:
            report.append(f"\n分析失败：{self.error_message}")
        
        report.append("\n" + "=" * 70)
        report.append(f"状态：{self.status}")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def analyze(self, filepath):
        """主分析函数"""
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze_grid()
        return self.generate_report()


def analyze_a4_grid(filepath, output_path=None):
    """便捷分析函数"""
    analyzer = A4GridAnalyzer()
    report = analyzer.analyze(filepath)
    
    print(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存至：{output_path}")
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python a4_grid_analyzer.py <image_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyze_a4_grid(input_file)
