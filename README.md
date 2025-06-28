# PyQuick

Python快速开发工具包 (Development Channel)

## 项目概述

PyQuick是一个Python快速开发工具包，提供了一系列实用功能模块，包括：
- Python环境管理
- PIP包管理
- 多线程下载
- 代理配置
- 错误收集与处理
- 系统调试信息收集

## 主要功能模块

### 核心模块
- `pyquick.py`: 主程序入口
- `launcher.py`: 启动器

### 下载管理
- `downloader/`: 多线程下载管理器
  - `DownloadManager.py`: 下载任务管理
  - `DownloadTask.py`: 下载任务实现
  - `MultiThreadDownloader.py`: 多线程下载器

### PIP管理
- `pipx/`: PIP包管理
  - `install_unsi.py`: 包安装/卸载
  - `pip_manager.py`: PIP管理器
  - `upgrade_pip.py`: PIP升级

### 系统工具
- `debug_info/`: 系统调试信息
- `get_system_build/`: 系统构建信息
- `settings/`: 配置管理

### 其他工具
- `crashes/`: 错误收集处理
- `log/`: 日志管理
- `proxy.py`: 代理配置

## 最近更新

### 2025-05-05
- 修复了macOS和Windows合并的bug

### 2025-05-03
- 初步支持Windows

### 2025-05-02
- 添加Python和PIP管理功能
- 改进下载管理器
- 优化项目结构

### 2025-04-27
- 添加自动安装依赖功能
- 实现代理配置加载
- 更新下载功能支持代理

## 安装与使用

1. 克隆仓库
```bash
git clone https://github.com/pyquick/pyquick.git
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行主程序
```bash
python pyquick.py
```

## 贡献指南

欢迎提交Pull Request或报告Issues。