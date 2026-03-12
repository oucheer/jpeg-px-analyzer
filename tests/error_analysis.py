# -*- coding: utf-8 -*-
"""
误差分析与解决方案

问题诊断：
1. 测试图像线条太细 (0.5mm = 5像素)
2. 线条靠近边缘，检测不准确
3. 边缘效应影响

解决方案：
1. 创建更准确的测试图像
2. 改进线条中心检测算法
3. 添加校准功能
"""

import cv2
import numpy as np
import os


def create_calibration_test():
    """创建校准测试图像 - 线条在合理位置"""
    
    dpi = 300
    width = 2480
    height = 3508
    
    # 创建白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 线条位置（更合理的位置，避免边缘效应）
    # 使用 10mm 位置（约 118 像素），这是常见的网格纸位置
    line_x = int(10 * dpi / 25.4)  # 10mm
    line_y = int(10 * dpi / 25.4)  # 10mm
    
    thickness = 3  # 粗线条
    
    # 绘制垂直线
    cv2.line(img, (line_x, 0), (line_x, height), (0, 0, 0), thickness)
    
    # 绘制水平线
    cv2.line(img, (0, line_y), (width, line_y), (0, 0, 0), thickness)
    
    # 添加浅灰色网格供参考
    grid = int(10 * dpi / 25.4)
    for x in range(0, width, grid):
        cv2.line(img, (x, 0), (x, height), (230, 230, 230), 1)
    for y in range(0, height, grid):
        cv2.line(img, (0, y), (width, y), (230, 230, 230), 1)
    
    os.makedirs("tests", exist_ok=True)
    cv2.imwrite("tests/calibration_test_10mm.jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    
    print(f"创建校准测试图像:")
    print(f"  垂直线 X = {line_x} px ({line_x * 25.4 / dpi:.2f} mm)")
    print(f"  水平线 Y = {line_y} px ({line_y * 25.4 / dpi:.2f} mm)")


def analyze_with_center_detection():
    """使用线条中心检测算法"""
    
    img = cv2.imread("tests/calibration_test_10mm.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    h, w = gray.shape
    
    # 分析左上角区域
    roi_w = 200
    roi_h = 200
    roi = gray[0:roi_h, 0:roi_w]
    
    print("\n" + "=" * 60)
    print("线条中心检测分析")
    print("=" * 60)
    
    # 方法1: 亮度分析
    row_means = np.mean(roi, axis=1)
    col_means = np.mean(roi, axis=0)
    
    # 找暗区（线条）
    threshold = np.mean(row_means) * 0.85
    
    # 找所有暗区
    dark_rows = np.where(row_means < threshold)[0]
    dark_cols = np.where(col_means < threshold)[0]
    
    print(f"\n暗区检测:")
    print(f"  水平暗区: {dark_rows[:10]}")
    print(f"  垂直暗区: {dark_cols[:10]}")
    
    if len(dark_rows) > 0:
        # 计算线条中心
        h_center = (dark_rows[0] + dark_rows[-1]) // 2
        print(f"  水平线条中心: {h_center} px ({h_center * 25.4 / 300:.2f} mm)")
    
    if len(dark_cols) > 0:
        v_center = (dark_cols[0] + dark_cols[-1]) // 2
        print(f"  垂直线条中心: {v_center} px ({v_center * 25.4 / 300:.2f} mm)")
    
    # 方法2: 边缘检测
    edges = cv2.Canny(roi, 30, 100)
    
    v_proj = np.sum(edges, axis=0)
    h_proj = np.sum(edges, axis=1)
    
    # 找峰值
    max_v = np.max(v_proj)
    max_h = np.max(h_proj)
    
    print(f"\n边缘投影:")
    print(f"  垂直峰值位置: {np.argmax(v_proj)} px ({np.argmax(v_proj) * 25.4 / 300:.2f} mm)")
    print(f"  水平峰值位置: {np.argmax(h_proj)} px ({np.argmax(h_proj) * 25.4 / 300:.2f} mm)")


def main():
    print("=" * 60)
    print("误差分析与解决方案")
    print("=" * 60)
    
    # 创建测试图像
    create_calibration_test()
    
    # 分析
    analyze_with_center_detection()


if __name__ == "__main__":
    main()
