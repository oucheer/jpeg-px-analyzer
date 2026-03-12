# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 最终优化版
专门找 L 形坐标线的交点作为原点
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasureFinal:
    """A4 纸张测量工具 - 最终版"""
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = 600  # 默认值 600 DPI
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
        
        # 默认值
        return 600  # 默认 600 DPI
    
    def find_l_shaped_intersection(self):
        """找 L 形坐标线的交点"""
        h, w = self.gray.shape
        
        # 策略：在更大范围内找 L 形线条
        # L 形线条特点：一条水平长线 + 一条垂直长线
        
        # 分析多个区域
        for search_size in [300, 400, 500]:
            roi_w = min(search_size, w // 3)
            roi_h = min(search_size, h // 3)
            roi = self.gray[0:roi_h, 0:roi_w]
            
            # 边缘检测
            edges = cv2.Canny(roi, 30, 100)
            
            # 投影分析
            v_proj = np.sum(edges, axis=0)
            h_proj = np.sum(edges, axis=1)
            
            # 找显著峰值（长线）
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
                    # 找最左边的峰值
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
                    # 找最上边的峰值
                    y_line = h_peaks[0]
                    self.debug_info['h_peaks'] = h_peaks
            
            # 如果找到了交点
            if 'x_line' in dir() and 'y_line' in dir():
                self.horizontal_px = y_line
                self.vertical_px = x_line
                
                # 转换为毫米
                self.horizontal_mm = round(y_line * 25.4 / self.dpi, 2)
                self.vertical_mm = round(x_line * 25.4 / self.dpi, 2)
                
                self.debug_info['method'] = 'peak_detection'
                self.debug_info['search_size'] = search_size
                self.debug_info['raw_x'] = x_line
                self.debug_info['raw_y'] = y_line
                
                return True
        
        return False
    
    def analyze(self):
        """分析图像"""
        if self.gray is None:
            return False
        
        # 尝试找 L 形交点
        if self.find_l_shaped_intersection():
            self.status = "SUCCESS"
            return True
        
        # 备选：使用暗区检测
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
        r.append("A4 纸张测量报告")
        r.append("=" * 60)
        r.append(f"\n文件: {self.filename}")
        r.append(f"尺寸: {self.gray.shape[1]} × {self.gray.shape[0]} 像素")
        r.append(f"DPI: {self.dpi}")
        r.append(f"检测方法: {self.debug_info.get('method', 'N/A')}")
        
        if self.status == "SUCCESS":
            r.append("\n" + "=" * 60)
            r.append("测量结果")
            r.append("=" * 60)
            
            r.append("""
┌─────────────────────────────────────────────────────────────┐
│                        距离测量示意图                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ↑ 上边缘 (Y=0)                                         │
│     │                                                        │
│  d1 │    ┌────────────────────────────────────────┐        │
│     │    │                                        │        │
│     │    │                                        │        │
│     │    ├────────────────────────────────────────┤        │
│     │    │ ← 水平线 (Y={})                         │
│     │    │                                        │        │
│     │    └────────────────────────────────────────┘        │
│     │                                                        │
│     │← d2 →│                                                │
│     │       │                                                │
│ 左边缘 → ───┼────────────────────────────────────────      │
│  (X=0)  │    │ ← 垂直线 (X={})                             │
│         └────┴────────────────────────────────────────      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""".format(self.horizontal_px, self.vertical_px))
            
            r.append("\n【水平距离 d1】")
            r.append("  起点: 上边缘 (图像顶部 Y=0)")
            r.append("  终点: 检测到的第一条水平线 (Y={} px)".format(self.horizontal_px))
            r.append("  距离: {} mm".format(self.horizontal_mm))
            
            r.append("\n【垂直距离 d2】")
            r.append("  起点: 左边缘 (图像左侧 X=0)")
            r.append("  终点: 检测到的第一条垂直线 (X={} px)".format(self.vertical_px))
            r.append("  距离: {} mm".format(self.vertical_mm))
            
            r.append("\n" + "-" * 60)
            r.append("计算")
            r.append("-" * 60)
            r.append("  公式: mm = 像素 × 25.4 ÷ DPI")
            r.append("  ")
            r.append("  水平: {} × 25.4 ÷ {} = {} mm".format(
                self.horizontal_px, self.dpi, self.horizontal_mm))
            r.append("  垂直: {} × 25.4 ÷ {} = {} mm".format(
                self.vertical_px, self.dpi, self.vertical_mm))
            
            r.append("\n" + "-" * 60)
            r.append("注意事项")
            r.append("-" * 60)
            r.append("  - 测量的是从图像边缘到第一条可见线条的距离")
            r.append("  - 如果图像有白色边距，测量的是边距后的第一条线")
            r.append("  - DPI = {} (自动检测或默认值)".format(self.dpi))
            
            if 'v_peaks' in self.debug_info:
                r.append("\n检测到的垂直线位置 (像素): {}".format(
                    self.debug_info['v_peaks'][:10]))
            if 'h_peaks' in self.debug_info:
                r.append("检测到的水平线位置 (像素): {}".format(
                    self.debug_info['h_peaks'][:10]))
        else:
            r.append(f"\n错误: {self.error_message}")
        
        r.append("\n" + "=" * 60)
        
        return "\n".join(r)
    
    def process(self, filepath):
        """处理文件"""
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze()
        return self.generate_report()


def main():
    import sys
    
    if len(sys.argv) < 2:
        test_file = "d:/work/AI/AI Use/jpeg analyzer/2026-03-11_177.jpg"
    else:
        test_file = sys.argv[1]
    
    tool = A4MeasureFinal()
    print(tool.process(test_file))


if __name__ == "__main__":
    main()
