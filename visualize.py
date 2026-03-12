# -*- coding: utf-8 -*-
"""
测量结果可视化工具
在图像上标注测量结果和坐标系
"""

import cv2
import numpy as np
from a4_analyzer import A4PaperAnalyzer
import sys


def visualize_measurement(image_path, output_path=None):
    """
    在图像上可视化测量结果
    """
    analyzer = A4PaperAnalyzer()
    
    if not analyzer.load_image(image_path):
        print(f"Error: {analyzer.error_message}")
        return
    
    analyzer.detect_coordinate_lines()
    
    if analyzer.status != "SUCCESS":
        print(f"Error: {analyzer.error_message}")
        return
    
    img = analyzer.image.copy()
    h, w = img.shape[:2]
    
    # 颜色定义
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    BLACK = (0, 0, 0)
    
    # 1. 绘制坐标轴
    # 垂直线（绿色）
    cv2.line(img, 
             (analyzer.line_x_px, 0), 
             (analyzer.line_x_px, h), 
             GREEN, 2)
    
    # 水平线（蓝色）
    cv2.line(img, 
             (0, analyzer.line_y_px), 
             (w, analyzer.line_y_px), 
             BLUE, 2)
    
    # 2. 标注原点（红色方框直角顶点）
    cv2.circle(img, 
               (analyzer.line_x_px, analyzer.line_y_px), 
               8, RED, -1)
    
    # 红色方框标记原点
    box_size = 30
    cv2.rectangle(img,
                  (analyzer.line_x_px - box_size, analyzer.line_y_px - box_size),
                  (analyzer.line_x_px, analyzer.line_y_px),
                  RED, 2)
    
    # 3. 标注箭头 1（垂直距离）
    # 从顶部到水平线的箭头
    arrow1_start = (50, 20)
    arrow1_end = (50, analyzer.line_y_px - 5)
    cv2.arrowedLine(img, arrow1_start, arrow1_end, RED, 3)
    cv2.putText(img, f"Y={analyzer.line_y_mm:.1f}mm", 
                (60, analyzer.line_y_px // 2), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)
    
    # 4. 标注箭头 2（水平距离）
    # 从左侧到垂直线的箭头
    arrow2_start = (20, 50)
    arrow2_end = (analyzer.line_x_px - 5, 50)
    cv2.arrowedLine(img, arrow2_start, arrow2_end, BLUE, 3)
    cv2.putText(img, f"X={analyzer.line_x_mm:.1f}mm",
                (analyzer.line_x_px // 2, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLUE, 2)
    
    # 5. 添加文字说明
    cv2.putText(img, "Origin (0,0)",
                (analyzer.line_x_px - 80, analyzer.line_y_px + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)
    
    cv2.putText(img, "Horizontal Line",
                (analyzer.line_x_px + 20, analyzer.line_y_px - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLUE, 1)
    
    cv2.putText(img, "Vertical Line",
                (analyzer.line_x_px + 20, analyzer.line_y_px + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)
    
    # 6. 添加测量结果信息框
    info_text = [
        f"DPI: {analyzer.dpi}",
        f"X: {analyzer.line_x_mm} mm",
        f"Y: {analyzer.line_y_mm} mm",
        f"Conf: {analyzer.x_confidence}%/{analyzer.y_confidence}%"
    ]
    
    y_offset = 30
    for text in info_text:
        cv2.putText(img, text, (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 2)
        y_offset += 25
    
    # 保存结果
    if output_path is None:
        output_path = image_path.replace('.jpg', '_annotated.jpg')
    
    cv2.imwrite(output_path, img)
    print(f"Visualization saved to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize.py <image_file>")
        sys.exit(1)
    
    image_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    visualize_measurement(image_file, output_file)
