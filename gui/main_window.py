# -*- coding: utf-8 -*-
"""
A4 纸张测量工具 - GUI 版本
支持手动输入实际距离参数
"""

import sys
import os
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QFileDialog, QMessageBox, QTabWidget, QLineEdit,
                             QFormLayout, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont

from core.analyzer import JPEGAnalyzer
from a4_measure_final import A4MeasureFinal


class DropLabel(QLabel):
    """支持拖放的标签组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f5f5f5;
                color: #666;
                font-size: 14px;
                padding: 40px;
            }
            QLabel:hover {
                border-color: #666;
                background-color: #e8e8e8;
            }
        """)
        self.setText("拖放 JPEG 图像文件到这里\n\n或点击下方按钮选择文件")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #4CAF50;
                    border-radius: 10px;
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    font-size: 14px;
                    padding: 40px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f5f5f5;
                color: #666;
                font-size: 14px;
                padding: 40px;
            }
            QLabel:hover {
                border-color: #666;
                background-color: #e8e8e8;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        files = event.mimeData().urls()
        if files:
            file_path = files[0].toLocalFile()
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                event.acceptProposedAction()
                self.parent().parent().parent().process_file(file_path)
            else:
                QMessageBox.warning(self, "警告", "仅支持 JPEG 格式文件！")


class AutoMeasureWidget(QWidget):
    """自动测量组件 - 支持自定义 DPI"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = A4MeasureFinal()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 说明标签
        info_label = QLabel("✨ 自动检测模式：工具将自动识别图像中的线条并计算距离")
        info_label.setStyleSheet("color: #2196F3; font-size: 12px; font-weight: bold; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 拖放区域
        self.drop_label = DropLabel(self)
        layout.addWidget(self.drop_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.select_button = QPushButton("选择图像文件")
        self.select_button.clicked.connect(self.select_file)
        button_layout.addWidget(self.select_button)
        
        self.save_button = QPushButton("保存结果")
        self.save_button.clicked.connect(self.save_result)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 结果显示
        result_label = QLabel("测量结果:")
        result_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(180)
        self.result_text.setPlaceholderText("自动检测结果将显示在这里...")
        self.result_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.result_text)
        
        # 状态栏
        self.status_label = QLabel("就绪 - 请拖放图像或点击按钮选择文件")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        self.current_result = ""
        self.current_file = ""
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 JPEG 图像", "", 
            "JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.process_file(file_path)
    
    def process_file(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "错误", "文件不存在！")
            return
        
        self.current_file = file_path
        
        self.status_label.setText("正在自动检测...")
        self.status_label.setStyleSheet("color: #2196F3;")
        self.result_text.clear()
        
        try:
            # 自动检测计算 - 自动读取图像 DPI
            self.analyzer = A4MeasureFinal()  # 自动读取 EXIF DPI
            self.current_result = self.analyzer.process(file_path)
            self.result_text.setText(self.current_result)
            self.save_button.setEnabled(True)
            
            if self.analyzer.status == "SUCCESS":
                self.status_label.setText("自动检测完成")
                self.status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.status_label.setText(f"检测失败 - {self.analyzer.error_message}")
                self.status_label.setStyleSheet("color: #f44336;")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理图像时发生错误：{str(e)}")
            self.status_label.setText("处理失败")
            self.status_label.setStyleSheet("color: #f44336;")
    
    def save_result(self):
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", 
            os.path.splitext(self.current_file)[0] + "_result.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_result)
                QMessageBox.information(self, "成功", "结果已保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("A4 纸张精确测量工具 v5.0")
        self.setMinimumSize(700, 680)
        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QPushButton {
                background-color: #2196F3; color: white; border: none;
                border-radius: 5px; padding: 10px 20px; font-size: 14px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QTextEdit {
                border: 1px solid #ddd; border-radius: 5px; padding: 10px;
                font-family: Consolas, monospace; font-size: 11px;
                background-color: #fafafa;
            }
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; }
            QTabBar::tab {
                background-color: #f0f0f0; padding: 8px 16px; margin-right: 2px;
            }
            QTabBar::tab:selected { background-color: white; border-bottom: 2px solid #2196F3; }
            QLabel { color: #333; }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QLabel("A4 纸张精确测量工具")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel(
            "✨ 自动检测模式\n"
            "   工具将自动识别图像中的线条并计算距离\n"
            "   水平距离 = 纸张上边缘到横线的距离\n"
            "   垂直距离 = 纸张左边缘到竖线的距离"
        )
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #e3f2fd;")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # 主测量组件
        self.measure_widget = AutoMeasureWidget()
        main_layout.addWidget(self.measure_widget)
    
    def process_file(self, file_path):
        self.measure_widget.process_file(file_path)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("A4 纸张测量工具")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
