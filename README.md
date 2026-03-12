# JPEG Black Line Detector

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform">
</p>

简体中文 | [English](./README_EN.md)

## 📋 项目简介

JPEG Black Line Detector 是一款专业的图像分析工具，专门用于检测JPEG图像中的黑色线条并计算精确的物理距离。该工具广泛应用于文档扫描、工业检测、纸张测量等领域。

### 核心功能

- ✅ **自动黑线检测** - 智能识别图像中的水平线和垂直线
- ✅ **精确测量** - 将像素距离转换为毫米单位，支持自定义DPI
- ✅ **高性能** - 采用C语言扩展加速处理速度
- ✅ **友好界面** - 提供直观的图形用户界面（GUI）
- ✅ **多种输出** - 支持文本报告和JSON格式输出

---

## 🏗️ 项目架构

```
jpeg-analyzer/
├── core/                      # 核心算法模块
│   ├── analyzer.py           # JPEG分析器主类
│   ├── cdistance.py          # Python绑定接口
│   ├── line_detector.py      # C扩展加载器
│   └── distance/             # C语言实现
│       ├── distance_calculator.c
│       ├── distance_calculator.h
│       ├── line_detector.c
│       └── line_detector.h
├── gui/                      # 图形界面模块
│   └── main_window.py       # PyQt5主窗口
├── image/                   # 测试图像目录
│   └── QUICK_START/         # 快速开始示例
├── measurement_results/     # 测量结果输出目录
├── universal_measure.py    # 通用测量工具（推荐）
├── a4_analyzer_final.py    # A4专用分析器
├── main.py                 # 程序入口
└── README.md               # 项目文档
```

### 技术栈

| 组件 | 技术 |
|------|------|
| 核心算法 | Python 3.7+ / NumPy / OpenCV |
| 性能优化 | C语言 (CPython扩展) |
| 图形界面 | PyQt5 |
| 图像处理 | Pillow (EXIF解析) |

---

## ✨ 功能特性

### 1. 智能黑线检测

- 采用**投影法**快速定位线条位置
- 使用**Hough变换**验证直线度
- 支持**自适应阈值**处理复杂背景

### 2. DPI自动识别

- 自动从JPEG EXIF元数据中提取DPI信息
- 支持自定义DPI设置
- 默认DPI: 300/600

### 3. 精确距离计算

- 像素 → 毫米转换公式：`mm = pixels × 25.4 / DPI`
- 水平距离测量（从顶部边缘）
- 垂直距离测量（从左侧边缘）

### 4. 置信度评估

- 基于线条黑度评估
- 考虑线条连续性
- 综合背景对比度分析

### 5. 多种输出格式

- 文本报告（ASCII图表）
- 结构化文本输出
- 可扩展的API接口

---

## 🚀 快速开始

### 环境要求

- Python 3.7 或更高版本
- Windows 操作系统
- 已编译的C扩展 DLL（已包含在项目中）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/jpeg-analyzer.git
cd jpeg-analyzer
```

#### 2. 安装Python依赖

```bash
pip install opencv-python numpy pillow pyqt5
```

#### 3. 验证安装

```bash
python universal_measure.py --help
```

---

## 📖 使用方法

### 方法一：图形界面（推荐）

启动GUI应用程序：

```bash
python main.py
```

**操作步骤：**

1. 运行程序后，显示主界面
2. **拖放** JPEG图像到指定区域
3. 或点击"选择图像文件"按钮
4. 查看测量结果
5. 可点击"保存结果"导出报告

![GUI界面预览](docs/gui-preview.png)

### 方法二：命令行工具

#### 通用测量工具

```bash
python universal_measure.py <image_path>
```

**示例：**

```bash
python universal_measure.py image/sample.jpg
```

**输出示例：**

```
============================================================
线条检测报告
============================================================

文件: sample.jpg
图像尺寸: 2480 × 3508 像素
DPI: 600
检测方法: c_extension
C扩展: 已加载

------------------------------------------------------------
测量结果
------------------------------------------------------------

【水平距离 d1】
  起点: 上边缘 (Y=0)
  终点: 水平线 (Y=120 px)
  距离: 5.08 mm

【垂直距离 d2】
  起点: 左边缘 (X=0)
  终点: 垂直线 (X=85 px)
  距离: 3.60 mm

------------------------------------------------------------
计算
------------------------------------------------------------
  公式: mm = 像素 × 25.4 ÷ DPI
  水平: 120 × 25.4 ÷ 600 = 5.08 mm
  垂直: 85 × 25.4 ÷ 600 = 3.60 mm

============================================================
```

#### 核心模块API

```python
from core.analyzer import analyze_jpeg_image

# 简单调用
result = analyze_jpeg_image("sample.jpg")

# 保存到文件
result = analyze_jpeg_image("sample.jpg", "output.txt")

print(result)
```

---

## ⚙️ 配置说明

### DPI设置

工具按以下优先级获取DPI：

1. **EXIF元数据** - 从JPEG图像中自动提取
2. **默认值** - 300 DPI（可配置）

修改默认DPI，编辑 `core/analyzer.py`：

```python
class JPEGAnalyzer:
    DEFAULT_DPI = 300  # 修改此值
```

### 检测参数调整

在 `universal_measure.py` 中可调整：

```python
class UniversalMeasureTool:
    def __init__(self):
        self.dpi = 600  # 默认DPI
        # ...
```

### C扩展设置

| 文件 | 说明 |
|------|------|
| `distance_calculator.dll` | 距离计算核心 |
| `line_detector.dll` | 线条检测核心 |

如需重新编译C扩展，参考 `core/build_dll.py`。

---

## 📐 测量原理

### 处理流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  JPEG图像   │ -> │  图像预处理  │ -> │  线条检测   │
│   输入      │    │ (高斯模糊/   │    │  (投影法/   │
│             │    │  二值化)     │    │   Hough)    │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   距离计算   │ <- │ 置信度评估  │ <- │  坐标定位   │
│  (像素->mm) │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 核心算法

1. **ROI区域提取** - 左上角20%区域
2. **高斯模糊** - 5x5核，sigma=1.5
3. **二值化** - 阈值50，反转
4. **投影法** - 行列投影找峰值
5. **直线验证** - Hough变换

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/your-repo/jpeg-analyzer.git

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 代码规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 风格指南
- 使用中文或英文注释，保持一致性
- 提交前运行测试

### 提交流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 MIT 许可证开源。

```
MIT License

Copyright (c) 2026 oucheer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 联系方式

- 项目主页：https://github.com/oucheer/jpeg-analyzer
- 问题反馈：https://github.com/oucheer/jpeg-analyzer/issues

---

## 🙏 致谢

感谢以下开源项目：

- [OpenCV](https://opencv.org/) - 计算机视觉库
- [NumPy](https://numpy.org/) - 科学计算基础库
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Qt框架Python绑定
