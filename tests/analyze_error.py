# -*- coding: utf-8 -*-
"""
误差分析与测试
"""

import os
import cv2
import numpy as np


def analyze_image_structure():
    """分析图像结构，找出问题"""
    
    # 读取原始测试图像
    img = cv2.imread("tests/precise_test_0.5_0.4mm.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    h, w = gray.shape
    
    # 提取左上角区域
    roi = gray[0:100, 0:100]
    
    print("=" * 60)
    print("图像分析")
    print("=" * 60)
    print(f"图像尺寸: {w} x {h}")
    print(f"ROI 区域: 100 x 100")
    
    # 分析像素值
    print(f"\n左上角像素值统计:")
    print(f"  最小值: {np.min(roi)}")
    print(f"  最大值: {np.max(roi)}")
    print(f"  平均值: {np.mean(roi):.2f}")
    print(f"  标准差: {np.std(roi):.2f}")
    
    # 边缘检测
    edges = cv2.Canny(roi, 30, 100)
    
    # 投影分析
    v_proj = np.sum(edges, axis=0)
    h_proj = np.sum(edges, axis=1)
    
    print(f"\n边缘检测结果:")
    print(f"  边缘点数量: {np.sum(edges > 0)}")
    
    # 找峰值
    print(f"\n垂直投影 (前20像素):")
    for i in range(min(20, len(v_proj))):
        if v_proj[i] > 0:
            print(f"  X={i}: {v_proj[i]}")
    
    print(f"\n水平投影 (前20像素):")
    for i in range(min(20, len(h_proj))):
        if h_proj[i] > 0:
            print(f"  Y={i}: {h_proj[i]}")
    
    # 问题分析
    print("\n" + "=" * 60)
    print("误差分析")
    print("=" * 60)
    print("问题1: 线条太细(0.5mm=5像素, 0.4mm=4像素)")
    print("问题2: 网格线干扰")
    print("问题3: 边缘效应")
    print("\n解决方案: 需要更智能的算法来区分主线条和网格线")


def create_better_test():
    """创建更好的测试图像"""
    
    dpi = 300
    width = 2480
    height = 3508
    
    # 白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 绘制粗黑线（在正确位置）
    h_px = int(0.5 * dpi / 25.4)  # 0.5mm = 5px
    v_px = int(0.4 * dpi / 25.4)  # 0.4mm = 4px
    
    # 使用粗线条以便检测
    thickness = 3
    
    # 绘制线条
    cv2.line(img, (0, h_px), (width, h_px), (0, 0, 0), thickness)
    cv2.line(img, (v_px, 0), (v_px, height), (0, 0, 0), thickness)
    
    # 添加网格作为参考（但不是太明显）
    grid_spacing = int(10 * dpi / 25.4)  # 10mm
    for x in range(0, width, grid_spacing):
        cv2.line(img, (x, 0), (x, height), (220, 220, 220), 1)
    for y in range(0, height, grid_spacing):
        cv2.line(img, (0, y), (width, y), (220, 220, 220), 1)
    
    cv2.imwrite("tests/better_test.jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"\nCreated better test: {h_px}px x {v_px}px")


if __name__ == "__main__":
    analyze_image_structure()
    create_better_test()
