# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 详细分析报告
测量从纸张边缘到坐标线的距离
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4PaperAnalyzer:
    """A4 纸张测量分析器"""
    
    DEFAULT_DPI = 300
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
        self.filename = ""
        self.width = 0
        self.height = 0
        
        # 测量结果
        self.line_x_px = 0  # 垂直线 X 坐标（像素）
        self.line_y_px = 0  # 水平线 Y 坐标（像素）
        self.line_x_mm = 0.0  # 垂直线 X 坐标（毫米）
        self.line_y_mm = 0.0  # 水平线 Y 坐标（毫米）
        
        # 置信度
        self.x_confidence = 0
        self.y_confidence = 0
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
        
        # 详细数据
        self.detailed_data = {}
    
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
    
    def detect_coordinate_lines(self):
        """检测坐标线（黑色 L 形线）"""
        if self.gray is None:
            return False
        
        # ROI: 左上角区域 (20% × 20%)
        roi_w = int(self.width * 0.2)
        roi_h = int(self.height * 0.2)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 预处理
        gaussian = cv2.GaussianBlur(roi, (5, 5), 1.5)
        _, binary = cv2.threshold(gaussian, 50, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学闭运算
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 垂直投影（检测垂直线）
        h, w = binary.shape
        h_proj = np.sum(binary, axis=0) / 255
        
        # 水平投影（检测水平线）
        v_proj = np.sum(binary, axis=1) / 255
        
        # 检测垂直线
        threshold = h * 0.3
        in_line = False
        line_start = 0
        
        for x in range(w):
            if h_proj[x] > threshold:
                if not in_line:
                    line_start = x
                    in_line = True
            else:
                if in_line:
                    line_end = x
                    self.line_x_px = (line_start + line_end) // 2
                    break
        
        # 检测水平线
        threshold = w * 0.3
        in_line = False
        
        for y in range(h):
            if v_proj[y] > threshold:
                if not in_line:
                    line_start = y
                    in_line = True
            else:
                if in_line:
                    line_end = y
                    self.line_y_px = (line_start + line_end) // 2
                    break
        
        # 转换为毫米
        self.line_x_mm = round(self.line_x_px * 25.4 / self.dpi, 2)
        self.line_y_mm = round(self.line_y_px * 25.4 / self.dpi, 2)
        
        # 计算置信度
        self._calculate_confidence(roi, binary, h_proj, v_proj)
        
        if self.line_x_px > 0 and self.line_y_px > 0:
            self.status = "SUCCESS"
            return True
        else:
            self.status = "FAIL"
            self.error_message = "No coordinate lines detected"
            return False
    
    def _calculate_confidence(self, roi, binary, h_proj, v_proj):
        """计算置信度"""
        h, w = binary.shape
        
        # 垂直线置信度
        if self.line_x_px < w:
            line_density = h_proj[self.line_x_px] / h
            self.x_confidence = min(100, int(line_density * 100))
        
        # 水平线置信度
        if self.line_y_px < h:
            line_density = v_proj[self.line_y_px] / w
            self.y_confidence = min(100, int(line_density * 100))
        
        # 存储详细数据
        self.detailed_data = {
            'roi_size': (w, h),
            'binary_count': np.sum(binary > 0),
            'h_proj_max': np.max(h_proj),
            'v_proj_max': np.max(v_proj)
        }
    
    def generate_report(self):
        """生成详细测量报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 70)
        report.append("A4 纸张坐标测量报告")
        report.append("=" * 70)
        report.append(f"\n测量时间：{timestamp}")
        report.append(f"图像文件：{self.filename}")
        report.append(f"图像尺寸：{self.width} × {self.height} 像素")
        report.append(f"DPI: {self.dpi}")
        report.append("\n" + "-" * 70)
        report.append("测量结果（以红色方框直角顶点为基准）")
        report.append("-" * 70)
        
        if self.status == "SUCCESS":
            report.append("\n【箭头 1】垂直距离测量:")
            report.append(f"  测量对象：纸张上边缘 → 水平黑线")
            report.append(f"  像素距离：{self.line_y_px} px")
            report.append(f"  物理距离：{self.line_y_mm} mm")
            report.append(f"  置信度：{self.x_confidence}%")
            
            report.append("\n【箭头 2】水平距离测量:")
            report.append(f"  测量对象：纸张左边缘 → 垂直黑线")
            report.append(f"  像素距离：{self.line_x_px} px")
            report.append(f"  物理距离：{self.line_x_mm} mm")
            report.append(f"  置信度：{self.y_confidence}%")
            
            report.append("\n" + "-" * 70)
            report.append("坐标系定义")
            report.append("-" * 70)
            report.append("  原点 (0, 0): 红色方框内直角顶点（L 形黑线交点）")
            report.append("  X 轴：水平向右为正")
            report.append("  Y 轴：垂直向下为正")
            
            report.append("\n坐标示意图:")
            report.append("""
    纸张左边缘          垂直黑线 (X={line_x_mm:.1f}mm)
        ↓                ↓
    ┌──┼────────────────┐ ← 纸张上边缘
    │  │                │   (Y=0)
    │  │                │
    │  │                │
    │  ├────────────────┤ ← 水平黑线 (Y={line_y_mm:.1f}mm)
    │  │←→              │
    │  │X={line_x_mm:.1f}mm        │
    │  │                │
    │  │                │
    └──┴────────────────┘
        ↑
        测量基准点
            """)
            
            report.append("\n" + "-" * 70)
            report.append("计算过程")
            report.append("-" * 70)
            report.append(f"  1. 读取图像尺寸：{self.width} × {self.height} 像素")
            report.append(f"  2. 解析 DPI 信息：{self.dpi}")
            report.append(f"  3. 提取 ROI 区域：{int(self.width*0.2)} × {int(self.height*0.2)} 像素")
            report.append(f"  4. 二值化阈值：50 (RGB≤50 为黑色)")
            report.append(f"  5. 检测垂直线位置：X = {self.line_x_px} 像素")
            report.append(f"  6. 检测水平线位置：Y = {self.line_y_px} 像素")
            report.append(f"  7. 像素转毫米：距离 = 像素 × 25.4 / DPI")
            report.append(f"     - X 轴：{self.line_x_px} × 25.4 / {self.dpi} = {self.line_x_mm} mm")
            report.append(f"     - Y 轴：{self.line_y_px} × 25.4 / {self.dpi} = {self.line_y_mm} mm")
            
        else:
            report.append(f"\n测量失败：{self.error_message}")
        
        report.append("\n" + "=" * 70)
        report.append(f"状态：{self.status}")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def analyze(self, filepath):
        """主分析函数"""
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.detect_coordinate_lines()
        return self.generate_report()


def analyze_a4_paper(filepath, output_path=None):
    """便捷分析函数"""
    analyzer = A4PaperAnalyzer()
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
        print("Usage: python a4_analyzer.py <image_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyze_a4_paper(input_file, output_file)
