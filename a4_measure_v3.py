# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 优化版 v3
使用暗区检测（亮度分析）方法，精确计算线条中心
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasureV3:
    """A4 纸张测量工具 v3 - 暗区检测法"""
    
    DEFAULT_DPI = 600  # 默认 DPI 调整为 600
    
    def __init__(self, dpi=None):
        self.image = None
        self.gray = None
        self.dpi = dpi if dpi is not None else self.DEFAULT_DPI
        self.custom_dpi = dpi is not None  # 是否自定义 DPI
        self.filename = ""
        
        # 结果
        self.horizontal_mm = 0.0
        self.vertical_mm = 0.0
        self.horizontal_px = 0
        self.vertical_px = 0
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
    
    def set_dpi(self, dpi):
        """设置自定义 DPI 值"""
        if dpi < 72 or dpi > 2400:
            raise ValueError("DPI 必须在 72-2400 之间")
        self.dpi = dpi
        self.custom_dpi = True
    
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
        
        # 如果未设置自定义 DPI，则从 EXIF 读取
        if not self.custom_dpi:
            self.dpi = self._get_dpi(filepath)
        return True
    
    def _get_dpi(self, filepath):
        """获取图像 EXIF DPI"""
        try:
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                for t, v in exif.items():
                    tag = TAGS.get(t, t)
                    if tag in ['XResolution', 'YResolution']:
                        if isinstance(v, tuple):
                            return int(v[0]) if v[1] == 1 else int(v[0] / v[1])
                        return int(v)
            return self.DEFAULT_DPI
        except:
            return self.DEFAULT_DPI
    
    def analyze(self):
        """分析图像 - 使用暗区检测法"""
        if self.gray is None:
            return False
        
        h, w = self.gray.shape
        
        # 分析左上角区域
        roi_w = min(400, w // 4)
        roi_h = min(500, h // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 亮度分析 - 找暗区
        row_means = np.mean(roi, axis=1)
        col_means = np.mean(roi, axis=0)
        
        # 阈值：平均亮度的 90%
        threshold = np.mean(row_means) * 0.90
        
        # 找暗区
        dark_rows = np.where(row_means < threshold)[0]
        dark_cols = np.where(col_means < threshold)[0]
        
        if len(dark_rows) > 0 and len(dark_cols) > 0:
            # 取第一条暗线的起始位置（不是中心）
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
        r.append(f"DPI: {self.dpi}")
        
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
    
    def process(self, filepath, dpi=None):
        """处理文件
        
        Args:
            filepath: 图像文件路径
            dpi: 可选的 DPI 值，如果指定则覆盖 EXIF 中的 DPI
        """
        # 如果提供了 dpi 参数，设置自定义 DPI
        if dpi is not None:
            self.set_dpi(dpi)
        
        if not self.load_image(filepath):
            return self.generate_report()
        
        self.analyze()
        return self.generate_report()
    
    @staticmethod
    def calculate_mm(pixels, dpi):
        """静态方法：根据像素和 DPI 计算毫米
        
        Args:
            pixels: 像素值
            dpi: DPI 值
            
        Returns:
            float: 毫米值
        """
        return pixels * 25.4 / dpi


def main():
    import sys
    
    if len(sys.argv) < 2:
        # 测试
        test_file = "tests/calibration_test_10mm.jpg"
        if os.path.exists(test_file):
            tool = A4MeasureV3()
            print(tool.process(test_file))
        else:
            print("Usage: python a4_measure_v3.py <image_file>")
    else:
        tool = A4MeasureV3()
        print(tool.process(sys.argv[1]))


if __name__ == "__main__":
    main()
