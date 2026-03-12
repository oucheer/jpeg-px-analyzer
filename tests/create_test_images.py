# -*- coding: utf-8 -*-
"""
测试图像生成器
生成用于测试的JPEG图像
"""

import numpy as np
import cv2
import os


def create_test_image(filename, width=2480, height=3508, dpi=300):
    """
    创建测试图像 - 带有黑色线条的文档
    
    Args:
        filename: 保存路径
        width: 图像宽度 (A4 @ 300DPI ≈ 2480)
        height: 图像高度 (A4 @ 300DPI ≈ 3508)
        dpi: DPI值
    """
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    x_line_pos = int(1.23 * dpi / 25.4 * width / width)
    y_line_pos = int(0.87 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * width / width))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"Created: {filename} ({width}x{height}, {dpi} DPI)")


def create_noisy_image(filename, width=2480, height=3508, dpi=300):
    """创建带噪声的测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    noise = np.random.randint(-30, 30, (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    x_line_pos = int(1.5 * dpi / 25.4 * width / width)
    y_line_pos = int(1.0 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * width / width))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    print(f"Created noisy: {filename}")


def create_color_image(filename, width=1920, height=1080, dpi=300):
    """创建彩色测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8)
    
    img[:, :width//2] = [240, 230, 220]
    img[:, width//2:] = [200, 210, 220]
    
    x_line_pos = int(0.5 * dpi / 25.4 * height)
    y_line_pos = int(0.3 * dpi / 25.4 * width)
    
    line_thickness = max(3, int(0.3 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    print(f"Created color: {filename}")


def create_low_dpi_image(filename, width=1275, height=1650, dpi=150):
    """创建低DPI测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 245
    
    x_line_pos = int(1.0 * dpi / 25.4 * height / height)
    y_line_pos = int(0.8 * dpi / 25.4 * width / width)
    
    line_thickness = max(2, int(0.4 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print(f"Created low DPI: {filename} ({width}x{height}, {dpi} DPI)")


def create_high_dpi_image(filename, width=4960, height=7016, dpi=600):
    """创建高DPI测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 242
    
    x_line_pos = int(2.0 * dpi / 25.4 * height / height)
    y_line_pos = int(1.5 * dpi / 25.4 * width / width)
    
    line_thickness = max(4, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (0, 0, 0), line_thickness)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (0, 0, 0), line_thickness)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    print(f"Created high DPI: {filename} ({width}x{height}, {dpi} DPI)")


def create_blurry_image(filename, width=2480, height=3508, dpi=300):
    """创建模糊测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    x_line_pos = int(1.2 * dpi / 25.4 * height / height)
    y_line_pos = int(0.9 * dpi / 25.4 * width / width)
    
    line_thickness = max(3, int(0.5 * dpi / 25.4 * height / height))
    
    cv2.line(img, (0, x_line_pos), (width, x_line_pos), (30, 30, 30), line_thickness + 2)
    cv2.line(img, (y_line_pos, 0), (y_line_pos, height), (30, 30, 30), line_thickness + 2)
    
    kernel = np.ones((5, 5), np.float32) / 25
    img = cv2.filter2D(img, -1, kernel)
    
    cv2.imwrite(filename, img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    print(f"Created blurry: {filename}")


if __name__ == "__main__":
    tests_dir = "tests"
    os.makedirs(tests_dir, exist_ok=True)
    
    create_test_image(f"{tests_dir}/test_01_standard.jpg")
    create_noisy_image(f"{tests_dir}/test_02_noisy.jpg")
    create_color_image(f"{tests_dir}/test_03_color.jpg")
    create_low_dpi_image(f"{tests_dir}/test_04_low_dpi.jpg")
    create_high_dpi_image(f"{tests_dir}/test_05_high_dpi.jpg")
    create_blurry_image(f"{tests_dir}/test_06_blurry.jpg")
    
    print("\nAll test images created!")
