# -*- coding: utf-8 -*-
"""
图像干扰元素消除工具
专门用于消除红色圆圈区域内的短线状干扰元素
"""

import cv2
import numpy as np
import os


class NoiseRemover:
    """干扰元素消除器"""
    
    def __init__(self, image_path):
        """初始化
        
        Args:
            image_path: 图像文件路径
        """
        self.image_path = image_path
        self.original = None
        self.processed = None
        self.red_circles = []  # 红色圆圈位置
        
    def load_image(self):
        """加载图像"""
        if not os.path.exists(self.image_path):
            return False
        
        self.original = cv2.imread(self.image_path)
        self.processed = self.original.copy()
        return True
    
    def detect_red_circles(self):
        """检测红色圆圈区域"""
        if self.original is None:
            return False
        
        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)
        
        # 定义红色范围
        lower_red1 = np.array([0, 70, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 70])
        upper_red2 = np.array([180, 255, 255])
        
        # 创建红色掩码
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # 形态学操作，连接断开的区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 提取圆圈区域
        for contour in contours:
            area = cv2.contourArea(contour)
            # 过滤掉太小的区域
            if area > 500:  # 最小面积阈值
                # 获取外接圆
                (x, y), radius = cv2.minEnclosingCircle(contour)
                center = (int(x), int(y))
                radius = int(radius)
                self.red_circles.append((center, radius))
        
        return len(self.red_circles) > 0
    
    def remove_short_lines_in_circle(self, center, radius):
        """消除圆圈内的短线
        
        Args:
            center: 圆心坐标 (x, y)
            radius: 圆半径
        """
        # 创建圆圈掩码
        mask = np.zeros(self.processed.shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)
        
        # 在圆圈区域内检测线条
        # 使用形态学操作检测短线
        gray = cv2.cvtColor(self.processed, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 在圆圈区域内应用掩码
        masked_edges = cv2.bitwise_and(edges, edges, mask=mask)
        
        # 使用霍夫变换检测线条
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, threshold=20, 
                               minLineLength=5, maxLineGap=10)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # 检查线条是否在圆圈内
                mid_point = ((x1 + x2) // 2, (y1 + y2) // 2)
                dist = np.sqrt((mid_point[0] - center[0])**2 + 
                             (mid_point[1] - center[1])**2)
                
                if dist < radius * 0.8:  # 线条在圆圈内部
                    # 计算线条长度
                    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    # 只消除短线（长度小于半径的 1/3）
                    if length < radius / 3:
                        # 使用周围像素填充
                        self._inpaint_line(x1, y1, x2, y2)
    
    def _inpaint_line(self, x1, y1, x2, y2):
        """修复线条区域"""
        # 创建线条掩码
        line_mask = np.zeros(self.processed.shape[:2], dtype=np.uint8)
        
        # 绘制线条（加粗以便覆盖）
        thickness = max(3, int(np.sqrt((x2-x1)**2 + (y2-y1)**2) / 2))
        cv2.line(line_mask, (x1, y1), (x2, y2), 255, thickness)
        
        # 使用修复算法
        self.processed = cv2.inpaint(self.processed, line_mask, 3, 
                                    cv2.INPAINT_TELEA)
    
    def process(self):
        """执行处理流程"""
        if not self.load_image():
            return False
        
        if not self.detect_red_circles():
            print("未检测到红色圆圈")
            return False
        
        print(f"检测到 {len(self.red_circles)} 个红色圆圈")
        
        # 对每个圆圈进行处理
        for center, radius in self.red_circles:
            print(f"处理圆圈：中心={center}, 半径={radius}")
            self.remove_short_lines_in_circle(center, radius)
        
        return True
    
    def save_result(self, output_path):
        """保存结果"""
        if self.processed is None:
            return False
        
        cv2.imwrite(output_path, self.processed)
        return True
    
    def get_statistics(self):
        """获取处理统计信息"""
        return {
            'circles_detected': len(self.red_circles),
            'circle_positions': self.red_circles
        }


def remove_noise_from_image(input_path, output_path=None):
    """便捷函数：从图像中消除干扰元素
    
    Args:
        input_path: 输入图像路径
        output_path: 输出图像路径（可选）
    
    Returns:
        dict: 处理统计信息
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cleaned{ext}"
    
    remover = NoiseRemover(input_path)
    
    if remover.process():
        remover.save_result(output_path)
        stats = remover.get_statistics()
        print(f"\n处理完成！")
        print(f"  输出文件：{output_path}")
        print(f"  检测到圆圈数：{stats['circles_detected']}")
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
            remove_noise_from_image(test_file)
        else:
            print("Usage: python noise_remover.py <image_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        remove_noise_from_image(input_file, output_file)
