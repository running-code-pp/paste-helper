"""Paste Helper 打包脚本 — PyInstaller"""

import os
import sys
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(PROJECT_DIR, "main.py")
ICON = os.path.join(PROJECT_DIR, "resources", "icon.ico")
DIST = os.path.join(PROJECT_DIR, "dist")
NAME = "PasteHelper"


def clean():
    """清理上次构建产物"""
    import shutil
    for d in ["build", "dist", "__pycache__"]:
        p = os.path.join(PROJECT_DIR, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    spec = os.path.join(PROJECT_DIR, f"{NAME}.spec")
    if os.path.exists(spec):
        os.remove(spec)


def build(console: bool = False):
    """执行 PyInstaller 打包"""
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", NAME,
        "--onefile",               # 单文件 exe
        "--windowed",              # 无控制台窗口
        "--clean",
        "--add-data", f"resources{os.pathsep}resources",
        "--add-data", f"styles{os.pathsep}styles",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
    ]

    if console:
        # 调试模式：显示控制台
        args.remove("--windowed")
    else:
        args.append(f"--icon={ICON}")

    args.append(MAIN)

    print(f"[build] {' '.join(args)}")
    subprocess.run(args, cwd=PROJECT_DIR, check=True)
    print(f"\n[build] done -> {os.path.join(DIST, NAME + '.exe')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Paste Helper 打包工具")
    parser.add_argument("--clean", action="store_true", help="清理构建产物后退出")
    parser.add_argument("--console", action="store_true", help="保留控制台窗口（调试用）")
    parser.add_argument("--build", action="store_true", default=True, help="执行打包")
    args = parser.parse_args()

    if args.clean:
        clean()
        print("[clean] done")

    if args.build or not args.clean:
        build(console=args.console)
