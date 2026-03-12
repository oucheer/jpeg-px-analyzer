# -*- coding: utf-8 -*-
# Build script for PyInstaller

import subprocess
import os
import sys
import shutil
import time

os.chdir(r"d:\work\AI\AI Use\jpeg analyzer")

# 先尝试清理 dist 目录
dist_path = "dist/JPEGBlackLineDetector"
if os.path.exists(dist_path):
    print(f"Removing old build: {dist_path}")
    try:
        # 等待一下确保文件不被占用
        time.sleep(1)
        # 尝试重命名而不是直接删除
        old_path = f"dist/JPEGBlackLineDetector_old_{int(time.time())}"
        os.rename(dist_path, old_path)
        print(f"Renamed old build to: {old_path}")
    except Exception as e:
        print(f"Warning: Could not remove {dist_path}: {e}")
        print("Please close any running Python processes and try again.")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "JPEGBlackLineDetector",
    "--onedir",
    "--windowed",
    "--add-data", "core;core",
    "--hidden-import", "PyQt5.QtCore",
    "--hidden-import", "PyQt5.QtGui",
    "--hidden-import", "PyQt5.QtWidgets",
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.ExifTags",
    "--noconfirm",
    "main.py"
]

print("Building EXE...")
print(" ".join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
print("Done!")
