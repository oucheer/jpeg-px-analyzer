# -*- coding: utf-8 -*-
"""
DPI 距离计算单元测试
验证不同 DPI 设置下的计算准确性
"""

import unittest
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a4_measure_v3 import A4MeasureV3


class TestDPICalculation(unittest.TestCase):
    """DPI 距离计算测试"""
    
    def test_calculate_mm_basic(self):
        """测试基本毫米计算"""
        # 100 像素 @ 300 DPI
        result = A4MeasureV3.calculate_mm(100, 300)
        expected = 100 * 25.4 / 300
        self.assertAlmostEqual(result, expected, places=2)
        print(f"✓ 100px @ 300DPI = {result:.2f}mm")
    
    def test_calculate_mm_different_dpi(self):
        """测试不同 DPI 下的计算"""
        test_cases = [
            (100, 150, 100 * 25.4 / 150),  # @150 DPI
            (100, 300, 100 * 25.4 / 300),  # @300 DPI
            (100, 600, 100 * 25.4 / 600),  # @600 DPI
            (100, 1200, 100 * 25.4 / 1200),  # @1200 DPI
        ]
        
        for pixels, dpi, expected in test_cases:
            result = A4MeasureV3.calculate_mm(pixels, dpi)
            error_pct = abs(result - expected) / expected * 100
            self.assertLess(error_pct, 1, f"DPI {dpi} 误差超过 1%")
            print(f"✓ {pixels}px @ {dpi}DPI = {result:.2f}mm (误差: {error_pct:.3f}%)")
    
    def test_accuracy_1_percent(self):
        """验证精度误差不超过 ±1%"""
        test_cases = [
            (50, 300), (100, 300), (200, 300), (500, 300),
            (50, 600), (100, 600), (200, 600), (500, 600),
            (50, 150), (100, 150), (200, 150), (500, 150),
        ]
        
        for pixels, dpi in test_cases:
            result = A4MeasureV3.calculate_mm(pixels, dpi)
            expected = pixels * 25.4 / dpi
            error_pct = abs(result - expected) / expected * 100
            self.assertLess(error_pct, 1, f"像素={pixels}, DPI={dpi} 误差={error_pct:.3f}% 超过 1%")
    
    def test_default_dpi(self):
        """测试默认 DPI 为 600"""
        tool = A4MeasureV3()
        self.assertEqual(tool.dpi, 600)
        print(f"✓ 默认 DPI = {tool.dpi}")
    
    def test_custom_dpi(self):
        """测试自定义 DPI"""
        tool = A4MeasureV3(dpi=300)
        self.assertEqual(tool.dpi, 300)
        self.assertTrue(tool.custom_dpi)
        
        tool.set_dpi(1200)
        self.assertEqual(tool.dpi, 1200)
        print(f"✓ 自定义 DPI = {tool.dpi}")
    
    def test_dpi_validation(self):
        """测试 DPI 验证"""
        tool = A4MeasureV3()
        
        # 有效 DPI
        for dpi in [72, 150, 300, 600, 1200, 2400]:
            tool.set_dpi(dpi)
            self.assertEqual(tool.dpi, dpi)
        
        # 无效 DPI
        with self.assertRaises(ValueError):
            tool.set_dpi(50)
        with self.assertRaises(ValueError):
            tool.set_dpi(3000)
        print("✓ DPI 验证通过")
    
    def test_calculate_mm_precision(self):
        """测试高精度计算"""
        # 精确到小数点后 3 位
        test_cases = [
            (118, 300, 9.99),  # 常见网格线
            (236, 300, 19.98),  # 20mm
            (59, 300, 4.99),   # 5mm
            (6, 300, 0.51),    # 0.5mm
            (5, 300, 0.42),    # 0.4mm
        ]
        
        for pixels, dpi, expected in test_cases:
            result = A4MeasureV3.calculate_mm(pixels, dpi)
            error_pct = abs(result - expected) / expected * 100
            self.assertLess(error_pct, 1, f"像素={pixels}, DPI={dpi} 误差={error_pct:.3f}%")
            print(f"✓ {pixels}px @ {dpi}DPI = {result:.3f}mm (预期: {expected}mm, 误差: {error_pct:.3f}%)")


class TestDPIScaling(unittest.TestCase):
    """DPI 缩放测试"""
    
    def test_same_physical_size_different_dpi(self):
        """相同物理尺寸不同 DPI 下的像素值"""
        physical_mm = 10.0  # 10mm
        
        # 计算在不同 DPI 下的像素值
        pixels_150 = physical_mm * 150 / 25.4
        pixels_300 = physical_mm * 300 / 25.4
        pixels_600 = physical_mm * 600 / 25.4
        pixels_1200 = physical_mm * 1200 / 25.4
        
        # 验证像素到毫米的转换一致性
        mm_150 = A4MeasureV3.calculate_mm(pixels_150, 150)
        mm_300 = A4MeasureV3.calculate_mm(pixels_300, 300)
        mm_600 = A4MeasureV3.calculate_mm(pixels_600, 600)
        mm_1200 = A4MeasureV3.calculate_mm(pixels_1200, 1200)
        
        # 所有结果应该接近 10mm
        for mm in [mm_150, mm_300, mm_600, mm_1200]:
            error_pct = abs(mm - physical_mm) / physical_mm * 100
            self.assertLess(error_pct, 1, f"误差 {error_pct:.3f}% 超过 1%")
            print(f"✓ {physical_mm}mm = {mm:.2f}mm (误差: {error_pct:.3f}%)")
    
    def test_high_resolution_accuracy(self):
        """高分辨率精度测试 - 600 DPI"""
        # 模拟 0.5mm @ 600 DPI
        pixels = 0.5 * 600 / 25.4  # ≈ 11.81 像素
        result = A4MeasureV3.calculate_mm(pixels, 600)
        expected = 0.5
        error_pct = abs(result - expected) / expected * 100
        self.assertLess(error_pct, 1)
        print(f"✓ 0.5mm @ 600DPI = {result:.3f}mm (误差: {error_pct:.3f}%)")
        
        # 模拟 0.4mm @ 600 DPI
        pixels = 0.4 * 600 / 25.4  # ≈ 9.45 像素
        result = A4MeasureV3.calculate_mm(pixels, 600)
        expected = 0.4
        error_pct = abs(result - expected) / expected * 100
        self.assertLess(error_pct, 1)
        print(f"✓ 0.4mm @ 600DPI = {result:.3f}mm (误差: {error_pct:.3f}%)")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("DPI 距离计算单元测试")
    print("=" * 70)
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDPICalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestDPIScaling))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ 所有测试通过！精度误差均 < 1%")
    else:
        print(f"❌ {len(result.failures + result.errors)} 个测试失败")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
