"""
PyQuick - 工具模块

包含应用所需的通用工具函数
"""
import os
import json
import traceback
import logging
import threading
import time
import tkinter as tk

# 获取日志记录器
try:
    from log import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("PyQuick")

def ensure_dir_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            return True
        except Exception as e:
            logger.error(f"创建目录失败 {directory}: {e}")
            return False
    return True

def safe_config(widget, **kwargs):
    """安全配置UI组件，避免异常"""
    try:
        for key, value in kwargs.items():
            if key == "add_cascade":
                # 特殊处理菜单项添加
                if value:
                    widget.add_cascade(**{k:v for k,v in kwargs.items() if k != "add_cascade"})
                return
            elif key == "text" and hasattr(widget, "config"):
                # 设置文本内容
                widget.config(text=value)
            elif key == "values" and hasattr(widget, "config"):
                # 设置下拉框值
                widget.config(values=value)
            elif key == "current" and hasattr(widget, "current"):
                # 设置下拉框当前选项
                widget.current(value)
            elif key == "state" and hasattr(widget, "config"):
                # 设置状态
                widget.config(state=value)
            elif hasattr(widget, "config"):
                # 其他配置项
                widget.config(**{key: value})
    except Exception as e:
        logger.error(f"配置UI组件失败: {e}")

def safe_grid(widget, **kwargs):
    """安全地使用grid显示组件"""
    try:
        widget.grid(**kwargs)
    except Exception as e:
        logger.error(f"显示UI组件失败: {e}")

def safe_grid_forget(widget):
    """安全地隐藏组件"""
    try:
        widget.grid_forget()
    except Exception as e:
        logger.error(f"隐藏UI组件失败: {e}")

def safe_ui_update(widget, **kwargs):
    """安全地更新UI组件属性"""
    try:
        for key, value in kwargs.items():
            if key == "mode" and hasattr(widget, "config"):
                widget.config(mode=value)
            elif key == "value" and hasattr(widget, "config"):
                widget["value"] = value
            elif key == "start" and hasattr(widget, "start"):
                widget.start(value)
            elif key == "stop" and value and hasattr(widget, "stop"):
                widget.stop()
            elif hasattr(widget, key):
                setattr(widget, key, value)
            elif hasattr(widget, "config"):
                widget.config(**{key: value})
    except Exception as e:
        logger.error(f"更新UI组件失败: {e}")

def safe_destroy(widget):
    """安全地销毁组件"""
    try:
        widget.destroy()
    except Exception as e:
        logger.error(f"销毁UI组件失败: {e}")

def format_file_size(size_in_bytes):
    """格式化文件大小"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes/1024:.2f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_in_bytes/(1024*1024*1024):.2f} GB"

def get_file_extension(filename):
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()

def is_executable(filename):
    """检查文件是否为可执行文件"""
    ext = get_file_extension(filename)
    executable_extensions = [".exe", ".bat", ".cmd", ".ps1", ".py", ".sh"]
    return ext in executable_extensions

def write_config(config_path, config, filename="config.json"):
    """写入JSON配置文件"""
    try:
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        
        config_file = os.path.join(config_path, filename)
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"写入配置失败 {filename}: {e}")
        return False

def read_config(config_path, filename="config.json", default=None):
    """读取JSON配置文件"""
    if default is None:
        default = {}
    
    try:
        config_file = os.path.join(config_path, filename)
        
        if not os.path.exists(config_file):
            # 创建默认配置
            write_config(config_path, default, filename)
            return default
        
        # 读取配置
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取配置失败 {filename}: {e}")
        return default

def run_with_progress(func, args=(), kwargs=None, progress_callback=None, finish_callback=None):
    """使用进度回调运行函数
    
    Args:
        func: 要运行的函数
        args: 函数参数
        kwargs: 函数关键字参数
        progress_callback: 进度回调函数，接收进度值(0-100)和状态消息
        finish_callback: 完成回调函数，接收结果和是否发生异常
    """
    if kwargs is None:
        kwargs = {}
    
    def run_thread():
        result = None
        error = None
        try:
            result = func(*args, **kwargs)
            if finish_callback:
                finish_callback(result, False)
        except Exception as e:
            error = e
            logger.error(f"运行任务失败: {e}")
            if finish_callback:
                finish_callback(None, True)
    
    thread = threading.Thread(target=run_thread, daemon=True)
    thread.start()
    return thread 