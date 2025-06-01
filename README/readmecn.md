# PyQuick 项目

## 项目简介
PyQuick 是一个基于 Python 的工具集项目，旨在提供快速开发和部署的实用功能。项目包含构建脚本、工具模块和依赖管理配置。

## 项目结构
### 核心文件说明
- [python_tool.py](file:///Users/li/Documents/GitHub/pyquick/python_tool.py)：核心功能实现文件，提供Python版本下载、pip管理（升级、安装、卸载包）、主题切换等功能
- [build.bat](file:///Users/li/Documents/GitHub/pyquick/build.bat)：Windows 平台构建脚本，用于将Python脚本打包为独立的Windows可执行文件
- [requirements.txt](file:///Users/li/Documents/GitHub/pyquick/requirements.txt)：项目依赖清单，包含运行项目所需的所有Python库

### 其他重要文件
- LICENSE.txt：GNU General Public License 的完整文本
- README.md：项目说明文档，包含项目简介、安装指南和使用说明

## 功能特性
1. 支持跨平台构建
2. 提供常用工具函数
3. 完整的依赖管理配置

## Python_Tool 功能详解

### 主要功能模块

#### 1. Python 版本下载
- 支持从 python.org 下载指定版本的 Python 安装程序
- 提供版本选择下拉框，支持下载从 3.5.0 到 3.13.2 的多个 Python 版本
- 支持自定义下载路径选择
- 显示下载进度条和下载状态信息
- 支持断点续传功能，提高下载可靠性

#### 2. pip 管理
- **pip 升级**：检查当前 pip 版本并自动升级到最新版
- **包安装**：支持搜索并安装指定的 Python 包，提供版本选择功能
- **包卸载**：支持卸载已安装的 Python 包，显示卸载过程和结果
- **包管理**：
  - 查看已安装包列表及其版本信息
  - 支持批量安装/卸载操作
  - 显示安装/卸载操作的状态和结果
  - 提供包依赖关系分析功能

#### 3. 主题切换
- 支持在深色模式和浅色模式之间切换
- 提供多种配色方案可供选择
- 自动保存用户主题偏好设置
- 根据系统版本自动调整主题支持
- 支持实时预览不同主题效果

#### 4. 系统信息监控
- 显示当前系统环境信息（操作系统、Python版本、pip版本等）
- 监控系统资源使用情况（CPU、内存）
- 提供环境变量管理功能

#### 5. 日志记录与调试
- 记录所有操作日志，便于排查问题
- 提供详细的错误信息提示
- 支持导出日志文件以供分析

### 技术实现
- 使用 `tkinter` 实现图形用户界面
- 使用 `subprocess` 执行系统命令（如 pip 操作）
- 使用 `requests` 和 `wget` 实现文件下载功能
- 使用 `threading` 实现多线程操作，避免界面冻结
- 使用 `sv_ttk` 提供现代化的 Sun Valley 主题风格
- 使用 `psutil` 库获取系统信息
- 使用 `logging` 模块实现日志记录功能

### 使用流程
1. 运行 `python_tool.py` 启动应用程序
2. 在 "Python Download" 标签页中选择 Python 版本和下载路径，点击 "Download" 开始下载
3. 在 "pip Management" 标签页中可以升级 pip 或安装/卸载 Python 包
4. 在 "System Info" 标签页查看系统环境信息和资源使用情况
5. 在主窗口菜单中可以切换主题、查看关于信息和导出日志

## 安装指南
```bash
# 安装依赖
pip install -r requirements.txt
```

## 使用说明
1. 运行 `python_tool.py` 启动主程序
2. 使用 `build.bat` 进行项目打包（Windows）
3. 查看 "Help" 菜单获取使用帮助和技术支持信息

## 技术栈
- Python 3.x
- Tkinter：用于构建图形用户界面
- Nuitka：Python 脚本编译为可执行文件的工具
- Requests：HTTP 请求库，用于下载文件
- Wget：网络数据集下载工具
- sv_ttk：Sun Valley 主题包，提供现代化的界面风格
- BeautifulSoup4 和 lxml：HTML 解析库