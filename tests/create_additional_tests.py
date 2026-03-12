# -*- coding: utf-8 -*-
"""
Additional test image generator
"""

import numpy as np
import cv2
import os


def create_light_bg_image(filename, width=2480, height=3508, dpi=300):
    """创建浅色背景测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 250
    
    x_line_pos = int(1.5 * dpi / 25.4 * height / height)
    y_line_pos = int(1.2 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print(f"Created light background: {filename}")


def create_dark_bg_image(filename, width=1920, height=1080, dpi=300):
    """创建深色背景测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 30
    
    x_line_pos = int(0.8 * dpi / 25.4 * height / height)
    y_line_pos = int(0.6 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness + 2)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness + 2)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print(f"Created dark background: {filename}")


def create_multi_line_image(filename, width=2480, height=3508, dpi=300):
    """创建多条线测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 245
    
    line_thickness = max(3, int(0.4 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, 50), (width, 50), (0, 0, 0), line_thickness)
    cv2.line(img, (0, 100), (width, 100), (0, 0, 0), line_thickness)
    
    cv2.line(img, (80, 0), (80, height), (0, 0, 0), line_thickness)
    cv2.line(img, (150, 0), (150, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print(f"Created multi-line: {filename}")


def create_high_compression_image(filename, width=1920, height=1080, dpi=300):
    """创建高压缩比测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    x_line_pos = int(0.7 * dpi / 25.4 * height / height)
    y_line_pos = int(0.5 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    print(f"Created high compression: {filename}")


def create_wrinkled_image(filename, width=2480, height=3508, dpi=300):
    """创建褶皱效果测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    x_line_pos = int(1.3 * dpi / 25.4 * height / height)
    y_line_pos = int(1.0 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    for i in range(0, height, 50):
        offset = int(5 * np.sin(i / 50))
        cv2.line(img, (0, i + offset), (width, i + offset), (245, 245, 245), 1)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    print(f"Created wrinkled: {filename}")


if __name__ == "__main__":
    tests_dir = "tests"
    os.makedirs(tests_dir, exist_ok=True)
    
    create_light_bg_image(f"{tests_dir}/test_07_light_bg.jpg")
    create_dark_bg_image(f"{tests_dir}/test_08_dark_bg.jpg")
    create_multi_line_image(f"{tests_dir}/test_09_multi_line.jpg")
    create_high_compression_image(f"{tests_dir}/test_10_high_compression.jpg")
    
    print("\nAll additional test images created!")
