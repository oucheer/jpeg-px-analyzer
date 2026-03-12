# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 优化版 v4
自动检测网格间距来验证 DPI
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasureV4:
    """A4 纸张测量工具 v4 - 智能 DPI 检测版"""
    
    DEFAULT_DPI = 300  # 改回 300 作为默认值
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.dpi = self.DEFAULT_DPI
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
        
        # 尝试从 EXIF 读取 DPI，如果没有则使用默认值
        self.dpi = self._get_dpi(filepath)
        
        self.debug_info['exif_dpi'] = self.dpi
        
        return True
    
    def _get_dpi(self, filepath):
        """获取 DPI - 优先从图像特征推断"""
        # 首先尝试从 EXIF 读取
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
        
        # 如果没有 EXIF，尝试通过网格间距推断
        inferred_dpi = self._infer_dpi_from_grid()
        if inferred_dpi > 0:
            return inferred_dpi
        
        return self.DEFAULT_DPI
    
    def _infer_dpi_from_grid(self):
        """从网格间距推断 DPI"""
        h, w = self.gray.shape
        
        # 分析较大区域来检测网格
        roi_w = min(1000, w // 4)
        roi_h = min(1000, h // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 边缘检测
        edges = cv2.Canny(roi, 30, 100)
        
        # 投影
        v_proj = np.sum(edges, axis=0)
        h_proj = np.sum(edges, axis=1)
        
        # 找峰值间隔
        peaks_v = self._find_peaks(v_proj)
        peaks_h = self._find_peaks(h_proj)
        
        if len(peaks_v) >= 2:
            intervals_v = np.diff(peaks_v)
            median_interval_v = np.median(intervals_v)
            
            # 假设是 10mm 网格，计算 DPI
            # 10mm = 像素 / DPI * 25.4
            # DPI = 像素 * 25.4 / 10
            inferred_dpi = int(median_interval_v * 25.4 / 10)
            
            if 72 <= inferred_dpi <= 1200:
                self.debug_info['inferred_dpi'] = inferred_dpi
                self.debug_info['grid_interval'] = median_interval_v
                return inferred_dpi
        
        return 0
    
    def _find_peaks(self, projection):
        """找投影峰值"""
        peaks = []
        threshold = np.max(projection) * 0.2 if np.max(projection) > 0 else 0
        
        for i in range(2, len(projection) - 2):
            if projection[i] > threshold:
                if (projection[i] >= projection[i-1] and 
                    projection[i] >= projection[i-2] and
                    projection[i] >= projection[i+1] and 
                    projection[i] >= projection[i+2]):
                    peaks.append(i)
        
        return peaks
    
    def analyze(self):
        """分析图像"""
        if self.gray is None:
            return False
        
        h, w = self.gray.shape
        
        # 分析左上角区域 - 扩大搜索范围
        roi_w = min(500, w // 4)
        roi_h = min(500, h // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 亮度分析
        row_means = np.mean(roi, axis=1)
        col_means = np.mean(roi, axis=0)
        
        # 阈值：平均亮度的 90%
        threshold = np.mean(row_means) * 0.92
        
        # 找暗区
        dark_rows = np.where(row_means < threshold)[0]
        dark_cols = np.where(col_means < threshold)[0]
        
        self.debug_info['threshold'] = threshold
        self.debug_info['dark_rows_count'] = len(dark_rows)
        self.debug_info['dark_cols_count'] = len(dark_cols)
        
        if len(dark_rows) > 0 and len(dark_cols) > 0:
            # 取第一条暗线的起始位置
            self.horizontal_px = int(dark_rows[0])
            self.vertical_px = int(dark_cols[0])
            
            # 转换为毫米
            self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi, 2)
            self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi, 2)
            
            self.status = "SUCCESS"
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
        r.append(f"DPI: {self.dpi} (自动检测)")
        
        if 'inferred_dpi' in self.debug_info:
            r.append(f"  - 从网格推断: {self.debug_info.get('inferred_dpi', 'N/A')}")
        
        if self.status == "SUCCESS":
            r.append("\n" + "-" * 60)
            r.append("测量结果")
            r.append("-" * 60)
            r.append(f"\n【水平距离】上边缘 → 水平线")
            r.append(f"  像素: {self.horizontal_px} px")
            r.append(f"  距离: {self.horizontal_mm} mm")
            r.append(f"\n【垂直距离】左边缘 → 垂直线")
            r.append(f"  像素: {self.vertical_px} px")
            r.append(f"  距离: {self.vertical_mm} mm")
            r.append("\n" + "-" * 60)
            r.append("计算")
            r.append("-" * 60)
            r.append(f"  公式: mm = px × 25.4 ÷ DPI")
            r.append(f"  水平: {self.horizontal_px} × 25.4 ÷ {self.dpi} = {self.horizontal_mm} mm")
            r.append(f"  垂直: {self.vertical_px} × 25.4 ÷ {self.dpi} = {self.vertical_mm} mm")
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
        # 默认测试
        test_file = "d:/work/AI/AI Use/jpeg analyzer/2026-03-11_177.jpg"
        if os.path.exists(test_file):
            tool = A4MeasureV4()
            print(tool.process(test_file))
        else:
            print("Usage: python a4_measure_v4.py <image_file>")
    else:
        tool = A4MeasureV4()
        print(tool.process(sys.argv[1]))


if __name__ == "__main__":
    main()
