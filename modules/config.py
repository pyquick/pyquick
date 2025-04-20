#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置模块
负责管理应用设置、读写配置文件
"""
import os
import json
import shutil
from pathlib import Path

# 配置目录和文件
CONFIG_DIR = "config"
DEFAULT_CONFIG_FILE = "settings.json"
LANGUAGE_FILE = "language.txt"
THEME_FILE = "theme.txt"
THREAD_FILE = "allowthread.txt"
LOG_SIZE_FILE = "log_size.txt"

# 全局变量
_config_cache = {}
_changed = False

def init_config():
    """初始化配置目录和默认配置文件"""
    # 创建配置目录（如果不存在）
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    # 创建默认配置文件（如果不存在）
    config_path = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_FILE)
    if not os.path.exists(config_path):
        default_config = {
            "language": "zh_CN",
            "theme": "clam",
            "allow_threading": True,
            "log_level": "INFO",
            "max_log_size": 5,  # MB
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "python_mirror": "",
            "pip_mirror": ""
        }
        save_config(default_config)
    
    # 创建旧版兼容配置文件
    _create_legacy_config_files()
    
    # 加载配置
    return load_config()

def _create_legacy_config_files():
    """创建与旧版兼容的单文件配置"""
    config = load_config()
    
    # 语言文件
    _write_single_value_file(LANGUAGE_FILE, config.get("language", "zh_CN"))
    
    # 主题文件
    _write_single_value_file(THEME_FILE, config.get("theme", "clam"))
    
    # 线程设置文件
    thread_value = "1" if config.get("allow_threading", True) else "0"
    _write_single_value_file(THREAD_FILE, thread_value)
    
    # 日志大小文件
    _write_single_value_file(LOG_SIZE_FILE, str(config.get("max_log_size", 5)))

def _write_single_value_file(filename, value):
    """写入单值配置文件"""
    file_path = os.path.join(CONFIG_DIR, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(value))
    except Exception as e:
        print(f"无法写入配置文件 {filename}: {e}")

def load_config():
    """加载配置文件"""
    global _config_cache
    config_path = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_FILE)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
        else:
            _config_cache = {}
    except Exception as e:
        print(f"无法加载配置文件: {e}")
        _config_cache = {}
    
    return _config_cache

def save_config(config=None):
    """保存配置文件"""
    global _config_cache, _changed
    
    if config is None:
        config = _config_cache
    else:
        _config_cache = config
    
    config_path = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_FILE)
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        _changed = False
        
        # 更新旧版配置文件
        _create_legacy_config_files()
        
        return True
    except Exception as e:
        print(f"无法保存配置文件: {e}")
        return False

def get_setting(key, default=None):
    """获取配置项"""
    global _config_cache
    
    if not _config_cache:
        load_config()
    
    return _config_cache.get(key, default)

def set_setting(key, value):
    """设置配置项"""
    global _config_cache, _changed
    
    if not _config_cache:
        load_config()
    
    _config_cache[key] = value
    _changed = True
    return True

def save_if_changed():
    """如果配置已更改，则保存"""
    global _changed
    if _changed:
        return save_config()
    return True

# 从旧版配置文件读取
def get_language():
    """获取当前语言设置"""
    try:
        lang_file = os.path.join(CONFIG_DIR, LANGUAGE_FILE)
        if os.path.exists(lang_file):
            with open(lang_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return get_setting("language", "zh_CN")
    except Exception:
        return "zh_CN"

def get_theme():
    """获取当前主题设置"""
    try:
        theme_file = os.path.join(CONFIG_DIR, THEME_FILE)
        if os.path.exists(theme_file):
            with open(theme_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return get_setting("theme", "clam")
    except Exception:
        return "clam"

def get_thread_setting():
    """获取线程设置"""
    try:
        thread_file = os.path.join(CONFIG_DIR, THREAD_FILE)
        if os.path.exists(thread_file):
            with open(thread_file, "r", encoding="utf-8") as f:
                return f.read().strip() == "1"
        return get_setting("allow_threading", True)
    except Exception:
        return True

def get_log_size():
    """获取日志大小设置（MB）"""
    try:
        log_size_file = os.path.join(CONFIG_DIR, LOG_SIZE_FILE)
        if os.path.exists(log_size_file):
            with open(log_size_file, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        return get_setting("max_log_size", 5)
    except Exception:
        return 5 