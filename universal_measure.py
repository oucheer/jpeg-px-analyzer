# -*- coding: utf-8 -*-
"""
JPEG黑线检测工具 - 优化版 (C语言核心)
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime

try:
    from core.line_detector import detect_lines as c_detect_lines, pixels_to_mm as c_pixels_to_mm
    C_EXTENSION_AVAILABLE = True
except ImportError:
    C_EXTENSION_AVAILABLE = False


class UniversalMeasureTool:
    """JPEG黑线检测工具"""
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = 600
        self.filename = ""
        
        self.horizontal_mm = 0.0
        self.vertical_mm = 0.0
        self.horizontal_px = 0
        self.vertical_px = 0
        
        self.status = "FAIL"
        self.error_message = ""
        
        self.debug_info = {}
    
    def load_image(self, filepath):
        """加载图像"""
        if not os.path.exists(filepath):
            self.status = "FAIL"
            self.error_message = "文件不存在"
            return False
        
        self.filename = os.path.basename(filepath)
        
        try:
            self.image = cv2.imread(filepath)
            if self.image is None:
                self.status = "FAIL"
                self.error_message = "不支持的格式"
                return False
            
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            
        except:
            self.status = "FAIL"
            self.error_message = "文件损坏"
            return False
        
        self.dpi = self._get_dpi(filepath)
        
        return True
    
    def _get_dpi(self, filepath):
        """获取 DPI"""
        try:
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                for t, v in exif.items():
                    tag = TAGS.get(t, t)
                    if tag in ['XResolution', 'YResolution']:
                        if isinstance(v, tuple):
                            dpi = int(v[0]) if v[1] == 1 else int(v[0] / v[1])
                            if 72 <= dpi <= 1200:
                                return dpi
                        elif isinstance(v, (int, float)):
                            dpi = int(v)
                            if 72 <= dpi <= 1200:
                                return dpi
        except:
            pass
        
        return 600
    
    def find_lines(self):
        """查找线条位置 - 使用C语言实现"""
        if C_EXTENSION_AVAILABLE:
            return self._find_lines_c()
        else:
            return self._find_lines_python()
    
    def _find_lines_c(self):
        """使用C扩展查找线条"""
        try:
            edge_margin = 15
            vertical_px, horizontal_px = c_detect_lines(self.gray, edge_margin)
            
            if vertical_px is not None and horizontal_px is not None:
                self.vertical_px = vertical_px
                self.horizontal_px = horizontal_px
                
                self.horizontal_mm = round(horizontal_px * 25.4 / self.dpi, 2)
                self.vertical_mm = round(vertical_px * 25.4 / self.dpi, 2)
                
                if vertical_px < edge_margin * 2:
                    return self._find_lines_python()
                
                self.debug_info['method'] = 'c_extension'
                return True
        except Exception as e:
            self.debug_info['c_error'] = str(e)
        
        return self._find_lines_python()
    
    def _find_lines_python(self):
        """Python实现的后备算法"""
        h, w = self.gray.shape
        
        blurred = cv2.GaussianBlur(self.gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        v_proj = np.sum(edges, axis=0)
        h_proj = np.sum(edges, axis=1)
        
        edge_margin = 15
        min_valid_peak = 50
        
        def find_first_peak(proj, min_pos):
            max_val = np.max(proj)
            if max_val == 0:
                return None
            
            threshold = max_val * 0.10
            for i in range(min_pos, len(proj) - 2):
                if proj[i] > threshold:
                    if (proj[i] >= proj[i-1] and proj[i] >= proj[i-2] and
                        proj[i] >= proj[i+1] and proj[i] >= proj[i+2]):
                        return i
            return None
        
        x_line = find_first_peak(v_proj, min_valid_peak)
        y_line = find_first_peak(h_proj, min_valid_peak)
        
        if x_line is None or y_line is None:
            row_means = np.mean(blurred, axis=1)
            col_means = np.mean(blurred, axis=0)
            
            bg_row = np.mean(row_means[-50:])
            bg_col = np.mean(col_means[-50:])
            
            dark_rows = np.where(row_means < bg_row * 0.85)[0]
            dark_cols = np.where(col_means < bg_col * 0.85)[0]
            
            if x_line is None:
                valid_cols = dark_cols[dark_cols > edge_margin]
                if len(valid_cols) > 0:
                    x_line = int(valid_cols[0])
            
            if y_line is None:
                valid_rows = dark_rows[dark_rows > edge_margin]
                if len(valid_rows) > 0:
                    y_line = int(valid_rows[0])
        
        if x_line is not None and y_line is not None:
            self.vertical_px = x_line
            self.horizontal_px = y_line
            
            self.horizontal_mm = round(y_line * 25.4 / self.dpi, 2)
            self.vertical_mm = round(x_line * 25.4 / self.dpi, 2)
            
            self.debug_info['method'] = 'python_fallback'
            return True
        
        return False
    
    def analyze(self):
        """分析图像"""
        if self.gray is None:
            return False
        
        if self.find_lines():
            self.status = "SUCCESS"
            return True
        
        self.error_message = "未检测到线条"
        return False
    
    def generate_report(self):
        """生成报告"""
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        r = []
        r.append("=" * 60)
        r.append("线条检测报告")
        r.append("=" * 60)
        r.append(f"\n文件: {self.filename}")
        r.append(f"图像尺寸: {self.gray.shape[1]} × {self.gray.shape[0]} 像素")
        r.append(f"DPI: {self.dpi}")
        r.append(f"检测方法: {self.debug_info.get('method', 'N/A')}")
        r.append(f"C扩展: {'已加载' if C_EXTENSION_AVAILABLE else '未加载'}")
        
        if self.status == "SUCCESS":
            r.append("\n" + "-" * 60)
            r.append("测量结果")
            r.append("-" * 60)
            
            r.append("""
┌─────────────────────────────────────────────────────────────────┐
│                      距离测量示意图                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     ↑ 上边缘 (Y=0)                                             │
│     │                                                            │
│  d1 │    ┌────────────────────────────────────────┐          │
│     │    │                                        │          │
│     │    │                                        │          │
│     │    ├────────────────────────────────────────┤          │
│     │    │ ← 水平线 (Y={})                           │
│     │    │                                        │          │
│     │    └────────────────────────────────────────┘          │
│     │                                                            │
│     │← d2 →│                                                    │
│     │       │                                                    │
│ 左边缘 → ───┼────────────────────────────────────────          │
│  (X=0)  │    │ ← 垂直线 (X={})                             │
│         └────┴────────────────────────────────────────          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
""".format(self.horizontal_px, self.vertical_px))
            
            r.append(f"\n【水平距离 d1】")
            r.append(f"  起点: 上边缘 (Y=0)")
            r.append(f"  终点: 水平线 (Y={self.horizontal_px} px)")
            r.append(f"  距离: {self.horizontal_mm} mm")
            
            r.append(f"\n【垂直距离 d2】")
            r.append(f"  起点: 左边缘 (X=0)")
            r.append(f"  终点: 垂直线 (X={self.vertical_px} px)")
            r.append(f"  距离: {self.vertical_mm} mm")
            
            r.append("\n" + "-" * 60)
            r.append("计算")
            r.append("-" * 60)
            r.append(f"  公式: mm = 像素 × 25.4 ÷ DPI")
            r.append(f"  水平: {self.horizontal_px} × 25.4 ÷ {self.dpi} = {self.horizontal_mm} mm")
            r.append(f"  垂直: {self.vertical_px} × 25.4 ÷ {self.dpi} = {self.vertical_mm} mm")
            
            r.append("\n" + "-" * 60)
            r.append("注意事项")
            r.append("-" * 60)
            r.append(f"  - 测量的是从图像边缘到第一条可见线条的距离")
            r.append(f"  - DPI = {self.dpi}")
        else:
            r.append(f"\n错误: {self.error_message}")
        
        r.append("\n" + "=" * 60)
        
        return "\n".join(r)
    
    def process(self, filepath):
        """处理文件
        
        Args:
            filepath: 图像路径
        """
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze()
        return self.generate_report()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python universal_measure.py <image_file>")
        return
    
    test_file = sys.argv[1]
    
    tool = UniversalMeasureTool()
    print(tool.process(test_file))


if __name__ == "__main__":
    main()
