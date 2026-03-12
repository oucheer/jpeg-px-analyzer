# -*- coding: utf-8 -*-
"""
创建精确的测试图像 - 线条位置在0.5mm和0.4mm处
用于验证算法的准确性
"""

import cv2
import numpy as np
import os


def create_precise_test_image(filename, dpi=300):
    """
    创建精确测试图像
    线条位置：水平0.5mm，垂直0.4mm
    """
    width = 2480  # A4 @ 300DPI
    height = 3508
    
    # 白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 线条位置（像素）
    horizontal_px = int(0.5 * dpi / 25.4)  # 0.5mm
    vertical_px = int(0.4 * dpi / 25.4)    # 0.4mm
    
    print(f"线条位置:")
    print(f"  水平线 Y = {horizontal_px} px (0.5mm)")
    print(f"  垂直线 X = {vertical_px} px (0.4mm)")
    
    # 绘制浅灰色网格 (RGB=200)
    grid_spacing = int(10 * dpi / 25.4)  # 10mm
    for x in range(0, width, grid_spacing):
        cv2.line(img, (x, 0), (x, height), (200, 200, 200), 1)
    for y in range(0, height, grid_spacing):
        cv2.line(img, (0, y), (width, y), (200, 200, 200), 1)
    
    # 绘制粗黑线（在指定位置）
    thickness = 3
    cv2.line(img, (0, horizontal_px), (width, horizontal_px), (0, 0, 0), thickness)
    cv2.line(img, (vertical_px, 0), (vertical_px, height), (0, 0, 0), thickness)
    
    # 保存
    os.makedirs("tests", exist_ok=True)
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"\nCreated: {filename}")
    
    return horizontal_px, vertical_px


def create_multiple_test_cases():
    """创建多个测试用例"""
    test_cases = [
        ("精确位置0.5_0.4mm", 300, 0.5, 0.4),
        ("DPI_150", 150, 0.5, 0.4),
        ("DPI_600", 600, 0.5, 0.4),
        ("深色线条", 300, 0.5, 0.4),
    ]
    
    for name, dpi, h_mm, v_mm in test_cases:
        width = int(210 / 25.4 * dpi)
        height = int(297 / 25.4 * dpi)
        
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # 线条位置
        h_px = int(h_mm * dpi / 25.4)
        v_px = int(v_mm * dpi / 25.4)
        
        # 网格
        grid_spacing = int(10 * dpi / 25.4)
        color = (180, 180, 180) if name != "深色线条" else (50, 50, 50)
        
        for x in range(0, width, grid_spacing):
            cv2.line(img, (x, 0), (x, height), color, 1)
        for y in range(0, height, grid_spacing):
            cv2.line(img, (0, y), (width, y), color, 1)
        
        # 粗线
        thickness = max(2, int(0.3 * dpi / 25.4))
        cv2.line(img, (0, h_px), (width, h_px), (0, 0, 0), thickness)
        cv2.line(img, (v_px, 0), (v_px, height), (0, 0, 0), thickness)
        
        filename = f"tests/test_{name}.jpg"
        cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        print(f"Created: {filename} (DPI={dpi}, H={h_mm}mm, V={v_mm}mm)")


if __name__ == "__main__":
    print("=" * 60)
    print("创建精确测试图像")
    print("=" * 60)
    
    # 主测试图像
    h, v = create_precise_test_image("tests/precise_test_0.5_0.4mm.jpg", dpi=300)
    
    print("\n" + "=" * 60)
    print("创建多个测试用例")
    print("=" * 60)
    create_multiple_test_cases()
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
