# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - 最终版本
自动检测 + 误差分析 + 校准功能
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime


class A4MeasureTool:
    """A4 纸张测量工具 - 最终版"""
    
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
        
        # 校准参数
        self.calibration_x = 1.0  # X轴校准系数
        self.calibration_y = 1.0  # Y轴校准系数
        
        # 状态
        self.status = "FAIL"
        self.error_message = ""
        self.detection_info = {}
    
    def load_image(self, filepath):
        """加载图像"""
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
            self.error_message = str(e)
            return False
        
        self.dpi = self._extract_dpi(filepath)
        return True
    
    def _extract_dpi(self, filepath):
        """解析 DPI"""
        try:
            image = Image.open(filepath)
            exif_data = image._getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['XResolution', 'YResolution']:
                        if isinstance(value, tuple):
                            return int(value[0]) if value[1] == 1 else int(value[0] / value[1])
                        return int(value)
            
            return self.DEFAULT_DPI
        except:
            return self.DEFAULT_DPI
    
    def set_calibration(self, cal_x, cal_y):
        """设置校准系数"""
        self.calibration_x = cal_x
        self.calibration_y = cal_y
    
    def analyze(self):
        """主分析流程"""
        if self.gray is None:
            return False
        
        # 检测线条
        if not self._detect_lines():
            return False
        
        # 应用校准
        self.horizontal_mm = round(self.horizontal_px * 25.4 / self.dpi * self.calibration_y, 2)
        self.vertical_mm = round(self.vertical_px * 25.4 / self.dpi * self.calibration_x, 2)
        
        self.status = "SUCCESS"
        return True
    
    def _detect_lines(self):
        """多策略线条检测"""
        # 策略1: 深度优先搜索粗线条
        result = self._detect_deep_lines()
        if result:
            self.detection_info['method'] = 'Deep Lines'
            return True
        
        # 策略2: 边缘检测
        result = self._detect_edge_lines()
        if result:
            self.detection_info['method'] = 'Edge Detection'
            return True
        
        # 策略3: 形态学
        result = self._detect_morphology_lines()
        if result:
            self.detection_info['method'] = 'Morphology'
            return True
        
        return False
    
    def _detect_deep_lines(self):
        """检测深色线条"""
        # 分析整个左上角区域
        roi_w = min(500, self.width // 4)
        roi_h = min(700, self.height // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 统计每列/行的平均亮度
        row_means = np.mean(roi, axis=1)  # 每行平均值
        col_means = np.mean(roi, axis=0)  # 每列平均值
        
        # 找暗区（线条）
        threshold = np.mean(row_means) * 0.9
        
        # 找第一行暗区
        dark_rows = np.where(row_means < threshold)[0]
        if len(dark_rows) > 0:
            self.horizontal_px = int(dark_rows[0])
        else:
            self.horizontal_px = 0
        
        dark_cols = np.where(col_means < threshold)[0]
        if len(dark_cols) > 0:
            self.vertical_px = int(dark_cols[0])
        else:
            self.vertical_px = 0
        
        if self.horizontal_px > 0 or self.vertical_px > 0:
            self.detection_info['raw_horizontal'] = self.horizontal_px
            self.detection_info['raw_vertical'] = self.vertical_px
            return True
        
        return False
    
    def _detect_edge_lines(self):
        """边缘检测"""
        roi_w = min(500, self.width // 4)
        roi_h = min(700, self.height // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # Canny边缘
        edges = cv2.Canny(roi, 30, 100)
        
        # 投影
        v_proj = np.sum(edges, axis=0)
        h_proj = np.sum(edges, axis=1)
        
        # 找第一个显著峰值
        self.vertical_px = self._find_first_significant(v_proj)
        self.horizontal_px = self._find_first_significant(h_proj)
        
        return self.horizontal_px > 0 or self.vertical_px > 0
    
    def _detect_morphology_lines(self):
        """形态学检测"""
        roi_w = min(500, self.width // 4)
        roi_h = min(700, self.height // 4)
        roi = self.gray[0:roi_h, 0:roi_w]
        
        # 梯度
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        grad = cv2.morphologyEx(roi, cv2.MORPH_GRADIENT, kernel)
        
        _, binary = cv2.threshold(grad, 20, 255, cv2.THRESH_BINARY)
        
        v_proj = np.sum(binary, axis=0)
        h_proj = np.sum(binary, axis=1)
        
        self.vertical_px = self._find_first_significant(v_proj)
        self.horizontal_px = self._find_first_significant(h_proj)
        
        return self.horizontal_px > 0 or self.vertical_px > 0
    
    def _find_first_significant(self, projection):
        """找第一个显著位置"""
        if len(projection) == 0:
            return 0
        
        max_val = np.max(projection)
        if max_val == 0:
            return 0
        
        threshold = max_val * 0.15
        
        for i in range(len(projection)):
            if projection[i] >= threshold:
                return i
        
        return 0
    
    def generate_report(self, expected_h=None, expected_v=None):
        """生成完整报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = []
        lines.append("=" * 70)
        lines.append("A4 纸张智能测量报告")
        lines.append("=" * 70)
        lines.append(f"\n图像文件: {self.filename}")
        lines.append(f"图像尺寸: {self.width} × {self.height} 像素")
        lines.append(f"DPI: {self.dpi}")
        lines.append(f"检测方法: {self.detection_info.get('method', 'Unknown')}")
        
        if self.status == "SUCCESS":
            lines.append("\n" + "-" * 70)
            lines.append("自动检测结果")
            lines.append("-" * 70)
            lines.append(f"\n【水平距离 - 箭头1】")
            lines.append(f"  像素: {self.horizontal_px} px")
            lines.append(f"  距离: {self.horizontal_mm} mm")
            lines.append(f"\n【垂直距离 - 箭头2】")
            lines.append(f"  像素: {self.vertical_px} px")
            lines.append(f"  距离: {self.vertical_mm} mm")
            
            # 误差分析
            if expected_h is not None and expected_v is not None:
                lines.append("\n" + "-" * 70)
                lines.append("误差分析")
                lines.append("-" * 70)
                
                err_h = abs(self.horizontal_mm - expected_h)
                err_v = abs(self.vertical_mm - expected_v)
                err_h_pct = (err_h / expected_h * 100) if expected_h > 0 else 0
                err_v_pct = (err_v / expected_v * 100) if expected_v > 0 else 0
                
                lines.append(f"\n水平距离:")
                lines.append(f"  预期值: {expected_h} mm")
                lines.append(f"  测量值: {self.horizontal_mm} mm")
                lines.append(f"  误差: {err_h:.3f} mm ({err_h_pct:.1f}%)")
                
                lines.append(f"\n垂直距离:")
                lines.append(f"  预期值: {expected_v} mm")
                lines.append(f"  测量值: {self.vertical_mm} mm")
                lines.append(f"  误差: {err_v:.3f} mm ({err_v_pct:.1f}%)")
                
                lines.append("\n校准系数:")
                lines.append(f"  X轴: {self.calibration_x}")
                lines.append(f"  Y轴: {self.calibration_y}")
            
            lines.append("\n" + "-" * 70)
            lines.append("计算公式")
            lines.append("-" * 70)
            lines.append(f"  距离(mm) = 像素 × 25.4 ÷ DPI × 校准系数")
            lines.append(f"  ")
            lines.append(f"  水平: {self.horizontal_px} × 25.4 ÷ {self.dpi} × {self.calibration_y} = {self.horizontal_mm} mm")
            lines.append(f"  垂直: {self.vertical_px} × 25.4 ÷ {self.dpi} × {self.calibration_x} = {self.vertical_mm} mm")
        else:
            lines.append(f"\n状态: {self.error_message}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def analyze_file(self, filepath, expected_h=None, expected_v=None, cal_x=1.0, cal_y=1.0):
        """分析文件"""
        self.set_calibration(cal_x, cal_y)
        
        if not self.load_image(filepath):
            return self.generate_report(expected_h, expected_v)
        
        self.analyze()
        return self.generate_report(expected_h, expected_v)


def main():
    import sys
    
    print("=" * 70)
    print("A4 纸张智能测量工具 - 最终版")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        # 测试所有图像
        test_images = [
            ("tests/precise_test_0.5_0.4mm.jpg", 0.5, 0.4),
        ]
        
        for img_path, exp_h, exp_v in test_images:
            if os.path.exists(img_path):
                print(f"\n\n{'='*70}")
                print(f"测试: {img_path}")
                print(f"预期: 水平={exp_h}mm, 垂直={exp_v}mm")
                print("="*70)
                
                tool = A4MeasureTool()
                report = tool.analyze_file(img_path, exp_h, exp_v)
                print(report)
    else:
        # 分析指定图像
        tool = A4MeasureTool()
        report = tool.analyze_file(sys.argv[1])
        print(report)


if __name__ == "__main__":
    main()
