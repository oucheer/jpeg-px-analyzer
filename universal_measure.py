# -*- coding: utf-8 -*-
"""
JPEG黑线检测工具
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class UniversalMeasureTool:
    """JPEG黑线检测工具"""
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = 600
        self.filename = ""
        
        # 结果
        self.horizontal_mm = 0.0
        self.vertical_mm = 0.0
        self.horizontal_px = 0
        self.vertical_px = 0
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
        
        # 调试信息
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
        
        # 尝试获取 DPI
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
        
        return 600  # 默认 DPI
    
    def find_lines(self):
        """查找线条位置"""
        h, w = self.gray.shape
        
        # 分析左上角区域
        for search_size in [300, 400, 500]:
            roi_w = min(search_size, w // 3)
            roi_h = min(search_size, h // 3)
            roi = self.gray[0:roi_h, 0:roi_w]
            
            # 边缘检测
            edges = cv2.Canny(roi, 30, 100)
            
            # 投影分析
            v_proj = np.sum(edges, axis=0)
            h_proj = np.sum(edges, axis=1)
            
            # 找峰值
            threshold = 0.15
            max_v = np.max(v_proj)
            max_h = np.max(h_proj)
            
            if max_v > 0:
                v_peaks = []
                for i in range(2, len(v_proj)-2):
                    if v_proj[i] > max_v * threshold:
                        if (v_proj[i] >= v_proj[i-1] and v_proj[i] >= v_proj[i-2] and
                            v_proj[i] >= v_proj[i+1] and v_proj[i] >= v_proj[i+2]):
                            v_peaks.append(i)
                
                if v_peaks:
                    x_line = v_peaks[0]
                    self.debug_info['v_peaks'] = v_peaks
            
            if max_h > 0:
                h_peaks = []
                for i in range(2, len(h_proj)-2):
                    if h_proj[i] > max_h * threshold:
                        if (h_proj[i] >= h_proj[i-1] and h_proj[i] >= h_proj[i-2] and
                            h_proj[i] >= h_proj[i+1] and h_proj[i] >= h_proj[i+2]):
                            h_peaks.append(i)
                
                if h_peaks:
                    y_line = h_peaks[0]
                    self.debug_info['h_peaks'] = h_peaks
            
            if 'x_line' in dir() and 'y_line' in dir():
                self.horizontal_px = y_line
                self.vertical_px = x_line
                
                # 转换为毫米
                self.horizontal_mm = round(y_line * 25.4 / self.dpi, 2)
                self.vertical_mm = round(x_line * 25.4 / self.dpi, 2)
                
                self.debug_info['method'] = 'peak_detection'
                return True
        
        return False
    
    def analyze(self):
        """分析图像"""
        if self.gray is None:
            return False
        
        # 尝试找线条
        if self.find_lines():
            self.status = "SUCCESS"
            return True
        
        # 备选：暗区检测
        h, w = self.gray.shape
        roi_w = min(400, w // 4)
        roi_h = min(400, h // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        row_means = np.mean(roi, axis=1)
        col_means = np.mean(roi, axis=0)
        
        threshold = np.mean(row_means) * 0.90
        
        dark_rows = np.where(row_means < threshold)[0]
        dark_cols = np.where(col_means < threshold)[0]
        
        if len(dark_rows) > 0 and len(dark_cols) > 0:
            self.horizontal_px = int(dark_rows[0])
            self.vertical_px = int(dark_cols[0])
            
            self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi, 2)
            self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi, 2)
            
            self.status = "SUCCESS"
            self.debug_info['method'] = 'dark_region'
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
