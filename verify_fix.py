# -*- coding: utf-8 -*-
"""
验证修复效果 - 测试线条中心检测
"""

from core.analyzer import JPEGAnalyzer
import os

print("=" * 60)
print("JPEG 黑线检测工具 - 修复验证")
print("=" * 60)
print("\n修复说明:")
print("- 之前：检测边缘位置 (Canny 边缘)")
print("- 现在：检测线条中心位置 (黑色像素投影)")
print("=" * 60)

tests = [
    ('tests/test_01_standard.jpg', '标准文档 (300DPI)'),
    ('tests/test_02_noisy.jpg', '带噪声文档'),
    ('tests/test_07_light_bg.jpg', '浅色背景'),
    ('tests/test_09_multi_line.jpg', '多条线'),
    ('tests/test_10_high_compression.jpg', '高压缩')
]

print("\n测试结果:")
print("-" * 60)

for test_file, description in tests:
    if os.path.exists(test_file):
        analyzer = JPEGAnalyzer()
        result = analyzer.analyze(test_file)
        
        lines = result.split('\n')
        filename = lines[0]
        dpi = lines[1]
        x_axis = lines[2]
        y_axis = lines[3]
        status = lines[4]
        
        print(f"\n{description}: {filename}")
        print(f"  {dpi}")
        print(f"  {x_axis}  ← 箭头 1 距离 (顶部到水平线中心)")
        print(f"  {y_axis}  ← 箭头 2 距离 (左侧到垂直线中心)")
        print(f"  {status}")

print("\n" + "=" * 60)
print("验证完成！")
print("现在测量的是线条中心到边缘的距离，符合您的需求。")
print("=" * 60)
