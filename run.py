#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQuick - Python安装与管理工具
启动脚本

用于启动PyQuick应用程序
"""

import os
import sys
import subprocess

def main():
    """主函数，启动PyQuick应用程序"""
    print("正在启动PyQuick...")
    
    # 检查当前目录是否存在pyquick.py
    if not os.path.exists("pyquick.py"):
        print("错误：未找到pyquick.py文件")
        return 1
    
    # 启动应用程序
    try:
        subprocess.run([sys.executable, "pyquick.py"])
        return 0
    except Exception as e:
        print(f"启动PyQuick时出错：{e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 