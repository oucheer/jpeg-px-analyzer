# -*- coding: utf-8 -*-
"""
距离测量可视化工具
生成清晰的位置标注图
"""

import cv2
import numpy as np
import os


def create_visualization(input_path, output_path=None):
    """创建可视化标注图"""
    
    # 读取图像
    img = cv2.imread(input_path)
    if img is None:
        print(f"无法读取图像: {input_path}")
        return False
    
    h, w = img.shape[:2]
    
    # 缩小图像以便显示（保持比例）
    scale = min(800 / w, 800 / h, 1.0)
    new_w = int(w * scale)
    new_h = int(h * scale)
    display = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 定义要标注的位置
    # 这些位置是基于之前的分析结果
    positions = {
        'left_edge': (10, new_h // 2),
        'top_edge': (new_w // 2, 10),
        'horizontal_line': (new_w // 2, int(110 * scale)),  # Y=110
        'vertical_line': (int(195 * scale), new_h // 2),  # X=195
    }
    
    # 颜色定义
    WHITE = (255, 255, 255)
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    
    # 绘制标注
    
    # 1. 边缘线
    cv2.line(display, (0, 10), (new_w, 10), WHITE, 2)  # 上边缘
    cv2.line(display, (10, 0), (10, new_h), WHITE, 2)  # 左边缘
    
    # 2. 检测到的线条
    cv2.line(display, 
             (0, positions['horizontal_line'][1]), 
             (new_w, positions['horizontal_line'][1]), 
             RED, 3)
    cv2.line(display, 
             (positions['vertical_line'][0], 0), 
             (positions['vertical_line'][0], new_h), 
             RED, 3)
    
    # 3. 绘制测量箭头
    # 水平距离（从上边缘到水平线）
    arrow_start = (new_w // 2, 30)
    arrow_end = (new_w // 2, positions['horizontal_line'][1] - 10)
    cv2.arrowedLine(display, arrow_start, arrow_end, GREEN, 2)
    
    # 垂直距离（从左边缘到垂直线）
    arrow_start = (30, new_h // 2)
    arrow_end = (positions['vertical_line'][0] - 10, new_h // 2)
    cv2.arrowedLine(display, arrow_start, arrow_end, BLUE, 2)
    
    # 4. 添加文字标注
    
    # 标题
    cv2.putText(display, "距离测量示意图", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
    
    # 边缘标注
    cv2.putText(display, "上边缘 (Y=0)", 
                (new_w // 2 - 50, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
    cv2.putText(display, "左边缘", 
                (15, new_h // 2), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
    
    # 线条标注
    cv2.putText(display, f"水平线 Y=110px", 
                (new_w // 2 + 10, positions['horizontal_line'][1]), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, RED, 1)
    cv2.putText(display, f"垂直线 X=195px", 
                (positions['vertical_line'][0], positions['vertical_line'][1] + 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, RED, 1)
    
    # 距离标注
    cv2.putText(display, "d1 = 4.66mm (600DPI)", 
                (new_w // 2 + 10, new_h // 4), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 2)
    cv2.putText(display, "d2 = 8.26mm (600DPI)", 
                (new_w // 4, new_h // 2 + 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLUE, 2)
    
    # 图例
    legend_y = new_h - 80
    cv2.rectangle(display, (10, legend_y - 20), (250, legend_y + 60), (0, 0, 0), -1)
    cv2.putText(display, "图例:", (20, legend_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    cv2.line(display, (20, legend_y + 20), (40, legend_y + 20), RED, 2)
    cv2.putText(display, "检测到的线条", (50, legend_y + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
    cv2.arrowedLine(display, (20, legend_y + 45), (60, legend_y + 45), GREEN, 2)
    cv2.putText(display, "水平距离 d1", (70, legend_y + 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
    cv2.arrowedLine(display, (20, legend_y + 65), (60, legend_y + 65), BLUE, 2)
    cv2.putText(display, "垂直距离 d2", (70, legend_y + 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
    
    # 保存
    if output_path is None:
        output_path = input_path.replace('.jpg', '_visualization.jpg')
    
    cv2.imwrite(output_path, display)
    print(f"可视化图已保存: {output_path}")
    
    return True


def create_ascii_diagram():
    """创建 ASCII 图示"""
    
    diagram = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           距离测量示意图                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║     ↑ 上边缘 (Y=0)                                                           ║
║     │                                                                       ║
║     │    ┌────────────────────────────────────────┐                       ║
║     │    │                                        │                       ║
║     │    │                                        │                       ║
║  d1 │    │          纸张区域                      │                       ║
║     │    │                                        │                       ║
║     │    ├────────────────────────────────────────┤ ← 水平线 (Y=110px)  ║
║     │    │                                        │                       ║
║     │    └────────────────────────────────────────┘                       ║
║     │                                                                       ║
║     │← d2 →│                                                                   ║
║     │       │                                                                   ║
║  左边缘 → ───┼───────────────────────────────────────────────────────────    ║
║  (X=0)  │    │                                                                   ║
║         │    │ ← 垂直线 (X=195px)                                             ║
║         │    │                                                                   ║
║         └────┴───────────────────────────────────────────────────────────    ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  测量说明:                                                                   ║
║                                                                              ║
║  1. d1 (水平距离):                                                           ║
║     - 起点: 上边缘 (Y=0)                                                    ║
║     - 终点: 水平线 (检测到的第一条黑线, Y=110px)                              ║
║     - 计算: 110 × 25.4 ÷ 600 = 4.66 mm                                      ║
║                                                                              ║
║  2. d2 (垂直距离):                                                           ║
║     - 起点: 左边缘 (X=0)                                                    ║
║     - 终点: 垂直线 (检测到的第一条黑线, X=195px)                              ║
║     - 计算: 195 × 25.4 ÷ 600 = 8.26 mm                                      ║
║                                                                              ║
║  注意事项:                                                                   ║
║  - 图像可能有白色边距，检测到的是第一条可见线条                                 ║
║  - DPI = 600 (默认)                                                         ║
║  - 计算公式: mm = 像素 × 25.4 ÷ DPI                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    print(diagram)
    
    # 保存到文件
    with open('measurement_diagram.txt', 'w', encoding='utf-8') as f:
        f.write(diagram)
    
    print("\nASCII 图示已保存到: measurement_diagram.txt")


def main():
    # 创建 ASCII 图示
    create_ascii_diagram()
    
    # 创建可视化图像
    test_file = "d:/work/AI/AI Use/jpeg analyzer/2026-03-11_177.jpg"
    if os.path.exists(test_file):
        print("\n创建可视化标注图...")
        create_visualization(test_file)


if __name__ == "__main__":
    main()
