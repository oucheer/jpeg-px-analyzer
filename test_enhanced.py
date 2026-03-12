# -*- coding: utf-8 -*-
"""
测试增强版算法
"""

from a4_analyzer_enhanced import analyze_a4_paper

# 创建测试图像（模拟用户上传的浅色网格）
import cv2
import numpy as np
import os

def create_light_grid_test():
    """创建浅色网格测试图像"""
    width = 2480  # A4 @ 300DPI
    height = 3508
    
    # 白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 绘制浅灰色网格 (RGB=200,200,200)
    grid_spacing = 118  # 10mm
    for x in range(0, width, grid_spacing):
        cv2.line(img, (x, 0), (x, height), (200, 200, 200), 1)
    
    for y in range(0, height, grid_spacing):
        cv2.line(img, (0, y), (width, y), (200, 200, 200), 1)
    
    # 保存
    os.makedirs("tests", exist_ok=True)
    cv2.imwrite("tests/light_grid_test.jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print("Created light grid test image")

if __name__ == "__main__":
    # 创建测试图像
    create_light_grid_test()
    
    # 测试增强版算法
    print("=" * 70)
    print("测试增强版算法 - 浅色网格检测")
    print("=" * 70)
    analyze_a4_paper("tests/light_grid_test.jpg")
