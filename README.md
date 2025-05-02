# PyQuick

PyQuick是一个简单易用的Python包管理工具,提供图形化界面来管理Python包、虚拟环境和开发环境。

## 主要特性

- 界面简洁直观,易于上手
- 支持多线程下载加速
- 自动检测pip更新
- 支持镜像源管理
- 提供日志和调试功能
- 支持代理设置
- 提供崩溃报告功能
- 自动检测包状态

## 设置系统

PyQuick提供了完整的设置系统,可以配置:

- 自动检查更新
- 日志文件大小限制  
- 下载线程数
- 镜像源设置
- 代理配置

所有设置都会自动保存,下次启动时自动加载。

## 系统要求

- Python 3.7+
- Windows/macOS/Linux

## 开发说明

本项目使用tkinter开发GUI界面,使用sv_ttk提供现代化的界面外观。

### 依赖管理

项目使用requirements.txt管理依赖:

```bash
pip install -r requirements.txt
```

### 目录结构

- about/ - 关于页面
- config/ - 配置文件
- crashes/ - 崩溃报告
- debug_info/ - 调试信息 
- downloader/ - 下载管理
- key/ - 密钥管理
- log/ - 日志管理
- pipx/ - pip管理
- settings/ - 设置管理
- test_net/ - 网络测试

## 贡献指南

欢迎提交Issue和Pull Request。

## 开源协议

本项目采用MIT协议开源。



