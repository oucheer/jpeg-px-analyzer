# -*- coding: utf-8 -*-
"""
创建 A4 纸张网格测试图像
模拟真实的 A4 坐标纸，带有刻度标记
"""

import numpy as np
import cv2

def create_a4_grid_paper(filename, dpi=300):
    """
    创建 A4 纸张网格图像
    A4 尺寸：210mm × 297mm
    网格：10mm × 10mm
    """
    # A4 尺寸转换为像素 (300 DPI)
    width_px = int(210 / 25.4 * dpi)  # 约 2480 像素
    height_px = int(297 / 25.4 * dpi)  # 约 3508 像素
    
    # 创建白色背景
    img = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255
    
    # 定义边距 (5mm)
    margin_top = int(5 / 25.4 * dpi)
    margin_left = int(5 / 25.4 * dpi)
    margin_bottom = int(5 / 25.4 * dpi)
    margin_right = int(5 / 25.4 * dpi)
    
    # 可打印区域
    content_width = width_px - margin_left - margin_right
    content_height = height_px - margin_top - margin_bottom
    
    # 网格间距 (10mm)
    grid_spacing = int(10 / 25.4 * dpi)
    
    # 绘制细网格线
    for x in range(margin_left, width_px - margin_right + 1, grid_spacing):
        cv2.line(img, (x, margin_top), (x, height_px - margin_bottom), (200, 200, 200), 1)
    
    for y in range(margin_top, height_px - margin_bottom + 1, grid_spacing):
        cv2.line(img, (margin_left, y), (width_px - margin_right, y), (200, 200, 200), 1)
    
    # 绘制粗黑线坐标轴 (红色方框位置的 L 形黑线)
    # 水平黑线：从左边距开始，距离顶部一定距离
    line_y = int(10 / 25.4 * dpi)  # 距离顶部 10mm
    line_thickness = max(3, int(0.5 / 25.4 * dpi))  # 0.5mm 粗
    
    cv2.line(img, (margin_left, line_y), (width_px - margin_right, line_y), (0, 0, 0), line_thickness)
    
    # 垂直黑线：从顶部开始，距离左边一定距离
    line_x = int(10 / 25.4 * dpi)  # 距离左侧 10mm
    
    cv2.line(img, (line_x, margin_top), (line_x, height_px - margin_bottom), (0, 0, 0), line_thickness)
    
    # 绘制刻度标记
    # 顶部刻度
    for i in range(0, 21, 1):
        x = margin_left + i * grid_spacing
        if i % 1 == 0:
            cv2.line(img, (x, margin_top - 15), (x, margin_top - 5), (0, 0, 0), 1)
    
    # 左侧刻度
    for i in range(0, 30, 1):
        y = margin_top + i * grid_spacing
        if i % 1 == 0:
            cv2.line(img, (margin_left - 15, y), (margin_left - 5, y), (0, 0, 0), 1)
    
    # 保存图像
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"Created A4 grid paper: {filename}")
    print(f"  Size: {width_px}x{height_px} pixels ({210}x{297} mm @ {dpi} DPI)")
    print(f"  Line X position: {line_x} px ({line_x / dpi * 25.4:.1f} mm from left)")
    print(f"  Line Y position: {line_y} px ({line_y / dpi * 25.4:.1f} mm from top)")
    
    return {
        'width_px': width_px,
        'height_px': height_px,
        'margin_top': margin_top,
        'margin_left': margin_left,
        'line_x': line_x,
        'line_y': line_y,
        'line_thickness': line_thickness,
        'grid_spacing': grid_spacing
    }


if __name__ == "__main__":
    import os
    os.makedirs("tests", exist_ok=True)
    
    params = create_a4_grid_paper("tests/a4_grid_paper.jpg", dpi=300)
    
    print("\n" + "=" * 60)
    print("A4 纸张网格测试图像参数")
    print("=" * 60)
    print(f"图像尺寸：{params['width_px']} × {params['height_px']} 像素")
    print(f"DPI: 300")
    print(f"网格间距：{params['grid_spacing']} 像素 (10mm)")
    print(f"边距：{params['margin_top']} 像素 (5mm)")
    print(f"\n黑色坐标线位置:")
    print(f"  垂直线 X 坐标：{params['line_x']} 像素 ({params['line_x'] / 300 * 25.4:.2f} mm 从左边缘)")
    print(f"  水平线 Y 坐标：{params['line_y']} 像素 ({params['line_y'] / 300 * 25.4:.2f} mm 从顶部)")
    print(f"  线条粗细：{params['line_thickness']} 像素")
    print("=" * 60)
