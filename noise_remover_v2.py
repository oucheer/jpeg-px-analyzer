# -*- coding: utf-8 -*-
"""
图像干扰元素消除工具 - 增强版
支持自动检测刻度标记区域并消除短线干扰
"""

import cv2
import numpy as np
import os


class SmartNoiseRemover:
    """智能干扰元素消除器"""
    
    def __init__(self, image_path):
        """初始化
        
        Args:
            image_path: 图像文件路径
        """
        self.image_path = image_path
        self.original = None
        self.processed = None
        self.target_regions = []  # 目标处理区域
        
    def load_image(self):
        """加载图像"""
        if not os.path.exists(self.image_path):
            return False
        
        self.original = cv2.imread(self.image_path)
        self.processed = self.original.copy()
        return True
    
    def detect_scale_marks_auto(self):
        """自动检测刻度标记区域（左上角）"""
        if self.original is None:
            return False
        
        h, w = self.original.shape[:2]
        
        # 定义左上角 ROI 区域（根据典型坐标纸布局）
        roi_w = int(w * 0.05)  # 前 5% 宽度
        roi_h = int(h * 0.05)  # 前 5% 高度
        
        # 提取左上角区域
        roi = self.original[0:roi_h, 0:roi_w]
        
        # 转换为灰度
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 形态学膨胀，连接短线
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 分析轮廓，找到刻度标记区域
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, cw, ch = cv2.boundingRect(contour)
            
            # 过滤：小面积、细长形状（刻度标记特征）
            if 100 < area < 5000 and (cw < ch * 0.3 or ch < cw * 0.3):
                # 转换到全局坐标
                global_x = x
                global_y = y
                
                # 定义处理区域（扩大一些）
                region_size = max(cw, ch) * 3
                region_center = (global_x + cw//2, global_y + ch//2)
                region_radius = region_size
                
                self.target_regions.append((region_center, region_radius))
        
        return len(self.target_regions) > 0
    
    def specify_regions_manually(self, regions):
        """手动指定处理区域
        
        Args:
            regions: 列表，每个元素为 (center_x, center_y, radius)
        """
        for region in regions:
            center = (region[0], region[1])
            radius = region[2]
            self.target_regions.append((center, radius))
    
    def remove_short_lines_in_region(self, center, radius):
        """消除区域内的短线
        
        Args:
            center: 区域中心 (x, y)
            radius: 区域半径
        """
        # 创建圆形掩码
        mask = np.zeros(self.processed.shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)
        
        # 提取 ROI
        x1 = max(0, center[0] - radius)
        y1 = max(0, center[1] - radius)
        x2 = min(self.processed.shape[1], center[0] + radius)
        y2 = min(self.processed.shape[0], center[1] + radius)
        
        roi = self.processed[y1:y2, x1:x2]
        roi_mask = mask[y1:y2, x1:x2]
        
        if roi.size == 0:
            return
        
        # 转换为灰度
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 二值化，检测暗色线条
        _, binary = cv2.threshold(gray_roi, 150, 255, cv2.THRESH_BINARY_INV)
        
        # 应用掩码
        binary = cv2.bitwise_and(binary, binary, mask=roi_mask)
        
        # 形态学操作，分离短线
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        removed_count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # 过滤：非常小的区域（短线、噪点）
            if 5 < area < 200:  # 面积阈值
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算长宽比
                aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                
                # 如果是细长线（长宽比>3）且面积小
                if aspect_ratio > 3 or area < 50:
                    # 创建修复掩码
                    repair_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                    cv2.drawContours(repair_mask, [contour], -1, 255, -1)
                    
                    # 膨胀一点确保完全覆盖
                    repair_mask = cv2.dilate(repair_mask, kernel, iterations=1)
                    
                    # 修复
                    roi_repaired = cv2.inpaint(roi, repair_mask, 3, cv2.INPAINT_TELEA)
                    
                    # 更新 ROI
                    roi[:] = roi_repaired
                    removed_count += 1
        
        # 更新主图像
        self.processed[y1:y2, x1:x2] = roi
        
        return removed_count
    
    def process(self, auto_detect=True, manual_regions=None):
        """执行处理流程
        
        Args:
            auto_detect: 是否自动检测
            manual_regions: 手动指定的区域列表
        """
        if not self.load_image():
            return False
        
        if auto_detect:
            if not self.detect_scale_marks_auto():
                print("未自动检测到刻度标记区域")
        
        if manual_regions:
            self.specify_regions_manually(manual_regions)
        
        if len(self.target_regions) == 0:
            print("未指定任何处理区域")
            return False
        
        print(f"检测到 {len(self.target_regions)} 个处理区域")
        
        total_removed = 0
        
        # 处理每个区域
        for i, (center, radius) in enumerate(self.target_regions):
            print(f"\n处理区域 {i+1}: 中心={center}, 半径={radius}")
            removed = self.remove_short_lines_in_region(center, radius)
            total_removed += removed
            print(f"  消除短线数量：{removed}")
        
        print(f"\n总共消除 {total_removed} 条短线")
        return True
    
    def save_result(self, output_path):
        """保存结果"""
        if self.processed is None:
            return False
        
        cv2.imwrite(output_path, self.processed)
        return True
    
    def get_statistics(self):
        """获取统计信息"""
        return {
            'regions_count': len(self.target_regions),
            'regions': self.target_regions
        }


def remove_noise(input_path, output_path=None, auto_detect=True, manual_regions=None):
    """便捷函数：消除图像干扰元素
    
    Args:
        input_path: 输入图像路径
        output_path: 输出图像路径（可选）
        auto_detect: 是否自动检测
        manual_regions: 手动指定区域
    
    Returns:
        dict: 处理统计信息
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cleaned{ext}"
    
    remover = SmartNoiseRemover(input_path)
    
    if remover.process(auto_detect, manual_regions):
        remover.save_result(output_path)
        stats = remover.get_statistics()
        print(f"\n处理完成！")
        print(f"  输出文件：{output_path}")
        print(f"  处理区域数：{stats['regions_count']}")
        return stats
    else:
        print("处理失败")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # 默认测试
        test_file = "d:/work/AI/AI Use/jpeg analyzer/2026-03-11_177.jpg"
        if os.path.exists(test_file):
            remove_noise(test_file)
        else:
            print("Usage: python noise_remover_v2.py <image_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        remove_noise(input_file, output_file)
