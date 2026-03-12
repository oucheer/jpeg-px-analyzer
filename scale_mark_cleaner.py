# -*- coding: utf-8 -*-
"""
图像干扰元素消除工具 - 最终版
专门消除坐标纸刻度标记区域的短线干扰
"""

import cv2
import numpy as np
import os


class ScaleMarkCleaner:
    """坐标纸刻度标记清洁器"""
    
    def __init__(self, image_path):
        """初始化"""
        self.image_path = image_path
        self.original = None
        self.processed = None
        
    def load_image(self):
        """加载图像"""
        if not os.path.exists(self.image_path):
            return False
        
        self.original = cv2.imread(self.image_path)
        self.processed = self.original.copy()
        return True
    
    def clean_scale_mark_region(self, center_x, center_y, radius):
        """清洁刻度标记区域
        
        Args:
            center_x: 区域中心 X 坐标
            center_y: 区域中心 Y 坐标
            radius: 区域半径
        """
        # 创建圆形掩码
        mask = np.zeros(self.processed.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)
        
        # 提取 ROI
        x1 = max(0, center_x - radius)
        y1 = max(0, center_y - radius)
        x2 = min(self.processed.shape[1], center_x + radius)
        y2 = min(self.processed.shape[0], center_y + radius)
        
        roi = self.processed[y1:y2, x1:x2].copy()
        roi_mask = mask[y1:y2, x1:x2]
        
        if roi.size == 0:
            return 0
        
        # 转换为灰度
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray_roi, 180, 255, cv2.THRESH_BINARY_INV)
        
        # 应用掩码
        binary = cv2.bitwise_and(binary, binary, mask=roi_mask)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        removed_count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # 只处理小面积的短线/噪点
            if 3 < area < 150:
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算长宽比
                aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
                
                # 如果是短线（长宽比>2 或面积很小）
                if aspect_ratio > 2.5 or area < 80:
                    # 创建修复掩码
                    repair_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                    cv2.drawContours(repair_mask, [contour], -1, 255, -1)
                    
                    # 膨胀确保覆盖
                    repair_mask = cv2.dilate(repair_mask, kernel, iterations=2)
                    
                    # 修复
                    roi_repaired = cv2.inpaint(roi, repair_mask, 5, cv2.INPAINT_TELEA)
                    
                    # 更新
                    roi[:] = roi_repaired
                    removed_count += 1
        
        # 更新主图像
        self.processed[y1:y2, x1:x2] = roi
        
        return removed_count
    
    def process_default_regions(self):
        """处理默认的刻度标记区域（左上角）"""
        if not self.load_image():
            return False
        
        h, w = self.processed.shape[:2]
        
        # 根据典型坐标纸布局，定义两个刻度标记区域
        # 区域 1: 顶部刻度（水平方向）
        region1_x = int(w * 0.02)  # 2% 宽度位置
        region1_y = int(h * 0.02)  # 2% 高度位置
        region1_radius = int(h * 0.03)  # 3% 高度作为半径
        
        # 区域 2: 左侧刻度（垂直方向）
        region2_x = int(w * 0.02)
        region2_y = int(h * 0.03)
        region2_radius = int(h * 0.03)
        
        print(f"处理区域 1 (顶部刻度): 中心=({region1_x}, {region1_y}), 半径={region1_radius}")
        removed1 = self.clean_scale_mark_region(region1_x, region1_y, region1_radius)
        print(f"  消除短线数：{removed1}")
        
        print(f"处理区域 2 (左侧刻度): 中心=({region2_x}, {region2_y}), 半径={region2_radius}")
        removed2 = self.clean_scale_mark_region(region2_x, region2_y, region2_radius)
        print(f"  消除短线数：{removed2}")
        
        print(f"\n总共消除 {removed1 + removed2} 条短线")
        
        return True
    
    def process_custom_regions(self, regions):
        """处理自定义区域
        
        Args:
            regions: 列表，每个元素为 (center_x, center_y, radius)
        """
        if not self.load_image():
            return False
        
        total_removed = 0
        
        for i, (cx, cy, r) in enumerate(regions):
            print(f"处理区域 {i+1}: 中心=({cx}, {cy}), 半径={r}")
            removed = self.clean_scale_mark_region(cx, cy, r)
            total_removed += removed
            print(f"  消除短线数：{removed}")
        
        print(f"\n总共消除 {total_removed} 条短线")
        return True
    
    def save_result(self, output_path):
        """保存结果"""
        if self.processed is None:
            return False
        
        cv2.imwrite(output_path, self.processed)
        return True


def clean_scale_marks(input_path, output_path=None, regions=None):
    """便捷函数：清洁刻度标记区域
    
    Args:
        input_path: 输入图像路径
        output_path: 输出路径（可选）
        regions: 自定义区域列表（可选）
    
    Returns:
        bool: 是否成功
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cleaned{ext}"
    
    cleaner = ScaleMarkCleaner(input_path)
    
    if regions:
        success = cleaner.process_custom_regions(regions)
    else:
        success = cleaner.process_default_regions()
    
    if success:
        cleaner.save_result(output_path)
        print(f"\n结果已保存至：{output_path}")
        return True
    else:
        print("处理失败")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # 默认测试
        test_file = "d:/work/AI/AI Use/jpeg analyzer/2026-03-11_177.jpg"
        if os.path.exists(test_file):
            clean_scale_marks(test_file)
        else:
            print("Usage: python scale_mark_cleaner.py <image_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 如果有额外参数，作为自定义区域
        if len(sys.argv) > 3:
            regions = []
            for i in range(3, len(sys.argv), 3):
                cx = int(sys.argv[i])
                cy = int(sys.argv[i+1])
                r = int(sys.argv[i+2])
                regions.append((cx, cy, r))
            clean_scale_marks(input_file, output_file, regions)
        else:
            clean_scale_marks(input_file, output_file)
