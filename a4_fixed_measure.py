# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 指定距离模式
严格按照用户输入的实际距离参数进行计算
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasurementTool:
    """A4 纸张测量工具 - 指定距离模式"""
    
    DEFAULT_DPI = 300
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.width = 0
        self.height = 0
        
        # 用户指定的实际距离（毫米）
        self.actual_horizontal_mm = 0.0  # 边缘到横线的实际距离
        self.actual_vertical_mm = 0.0    # 左边缘到竖线的实际距离
        
        # 计算结果
        self.horizontal_px = 0   # 水平距离（像素）
        self.vertical_px = 0      # 垂直距离（像素）
        
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
    
    def set_distances(self, horizontal_mm, vertical_mm):
        """
        设置实际距离参数（毫米）
        
        Args:
            horizontal_mm: 边缘到横线的距离（毫米）
            vertical_mm: 左边缘到竖线的距离（毫米）
        """
        self.actual_horizontal_mm = horizontal_mm
        self.actual_vertical_mm = vertical_mm
    
    def calculate(self):
        """
        根据设置的参数进行精确计算
        严格按照用户输入的实际距离，不自动检测
        """
        if self.gray is None:
            self.status = "FAIL"
            self.error_message = "Image not loaded"
            return False
        
        # 严格按照用户输入的距离计算
        # 像素 = 毫米 × DPI / 25.4
        
        self.horizontal_px = round(self.actual_horizontal_mm * self.dpi / 25.4, 1)
        self.vertical_px = round(self.actual_vertical_mm * self.dpi / 25.4, 1)
        
        self.status = "SUCCESS"
        return True
    
    def generate_report(self):
        """生成测量报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 70)
        report.append("A4 纸张测量报告")
        report.append("=" * 70)
        report.append(f"\n测量时间：{timestamp}")
        report.append(f"图像文件：{self.filename}")
        report.append(f"图像尺寸：{self.width} × {self.height} 像素")
        report.append(f"DPI: {self.dpi}")
        
        if self.status == "SUCCESS":
            report.append("\n" + "-" * 70)
            report.append("测量结果（按照您指定的实际距离参数）")
            report.append("-" * 70)
            
            report.append(f"\n【水平距离 - 箭头 1】")
            report.append(f"  测量对象：纸张上边缘 → 水平黑线")
            report.append(f"  实际距离：{self.actual_horizontal_mm} mm")
            report.append(f"  对应像素：{self.horizontal_px} px")
            
            report.append(f"\n【垂直距离 - 箭头 2】")
            report.append(f"  测量对象：纸张左边缘 → 垂直黑线")
            report.append(f"  实际距离：{self.actual_vertical_mm} mm")
            report.append(f"  对应像素：{self.vertical_px} px")
            
            report.append("\n" + "-" * 70)
            report.append("计算公式")
            report.append("-" * 70)
            report.append(f"  像素 = 毫米 × DPI ÷ 25.4")
            report.append(f"  ")
            report.append(f"  水平：{self.actual_horizontal_mm} × {self.dpi} ÷ 25.4 = {self.horizontal_px} px")
            report.append(f"  垂直：{self.actual_vertical_mm} × {self.dpi} ÷ 25.4 = {self.vertical_px} px")
            
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
    纸张左边缘           竖线 (X={self.actual_vertical_mm}mm)
        ↓                  ↓
    ┌──┼────────────────┐ ← 上边缘 (Y=0)
    │  │                │
    │  │                │
    │  │                │
    │  ├────────────────┤ ← 横线 (Y={self.actual_horizontal_mm}mm)
    │  │←→             │
    │  │{self.actual_vertical_mm}mm            │
    │  │                │
    └──┴────────────────┘
        ↑
    原点 (0,0)
            """)
            
        else:
            report.append(f"\n计算失败：{self.error_message}")
        
        report.append("\n" + "=" * 70)
        report.append(f"状态：{self.status}")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def analyze(self, filepath, horizontal_mm=0.5, vertical_mm=0.4):
        """
        主分析函数
        
        Args:
            filepath: 图像文件路径
            horizontal_mm: 边缘到横线的实际距离（毫米）
            vertical_mm: 左边缘到竖线的实际距离（毫米）
        """
        if not self.load_image(filepath):
            return self.generate_report()
        
        # 设置用户指定的实际距离
        self.set_distances(horizontal_mm, vertical_mm)
        
        # 计算
        self.calculate()
        
        return self.generate_report()


def analyze_with_fixed_distances(filepath, horizontal_mm=0.5, vertical_mm=0.4, output_path=None):
    """
    便捷分析函数 - 使用固定的实际距离
    
    Args:
        filepath: 图像文件路径
        horizontal_mm: 边缘到横线的实际距离（毫米）
        vertical_mm: 左边缘到竖线的实际距离（毫米）
        output_path: 输出文件路径（可选）
    """
    tool = A4MeasurementTool()
    report = tool.analyze(filepath, horizontal_mm, vertical_mm)
    
    print(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存至：{output_path}")
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python a4_fixed_measure.py <image_file> [horizontal_mm] [vertical_mm]")
        print("Example: python a4_fixed_measure.py test.jpg 0.5 0.4")
        sys.exit(1)
    
    input_file = sys.argv[1]
    horizontal_mm = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    vertical_mm = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4
    output_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    analyze_with_fixed_distances(input_file, horizontal_mm, vertical_mm, output_file)
