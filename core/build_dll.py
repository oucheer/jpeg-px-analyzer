# -*- coding: utf-8 -*-
"""
Build DLL from C source code
"""

import subprocess
import os
import sys
import shutil

def build_dll():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, "distance")

    c_file = os.path.join(src_dir, "line_detector.c")
    h_file = os.path.join(src_dir, "line_detector.h")
    output_dll = os.path.join(src_dir, "line_detector.dll")

    if not os.path.exists(c_file):
        print(f"Error: Source file not found: {c_file}")
        return False

    gcc_path = find_gcc()
    if not gcc_path:
        print("Error: GCC not found. Please install MinGW-w64.")
        return False

    cmd = [
        gcc_path,
        "-shared",
        "-O3",
        "-fPIC",
        "-o", output_dll,
        c_file,
        "-lm"
    ]

    print("Building DLL...")
    print("Command:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0 and os.path.exists(output_dll):
        print(f"Success! DLL created: {output_dll}")
        return True
    else:
        print("Build failed!")
        return False

def find_gcc():
    possible_paths = [
        "gcc",
        "mingw32-gcc",
        "x86_64-w64-mingw32-gcc",
    ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return path
        except:
            continue

    common_paths = [
        r"C:\mingw64\bin\gcc.exe",
        r"C:\msys64\mingw64\bin\gcc.exe",
        r"C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None

if __name__ == "__main__":
    os.chdir(r"d:\work\AI\AI Use\jpeg analyzer\core")
    success = build_dll()
    sys.exit(0 if success else 1)
