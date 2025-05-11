#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设置管理模块
负责加载、保存和管理应用程序配置
"""

import os
import json
import logging
logger = logging.getLogger(__name__)

# 全局实例
_settings_manager_instance = None

class SettingsManager:
    """设置管理器类"""
    
    def __init__(self, config_path: str):
        """
        初始化设置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.settings_file = os.path.join(config_path, "settings.json")
        self.settings = {}
        # 加载默认设置
        self._init_default_settings()
        # 从文件加载用户设置
        self._load_settings()
    
    def _init_default_settings(self):
        """初始化默认设置"""
        self.settings = {
            # 常规设置
            "interface": {
                "language": "简体中文",
                "enable_tray_icon": True,
                "start_minimized": False,
                "save_window_position": True,
                "confirm_exit": True
            },
            
            # 外观设置
            "appearance": {
                "theme": "系统默认",  # 系统默认, 浅色, 深色
                "font_size": 12,
                "custom_accent_color": "",
                "use_custom_accent": False
            },
            
            # 下载设置
            "download": {
                "default_path": "",
                "thread_count": 4,
                "auto_retry": True,
                "retry_count": 3,
                "timeout": 30,
                "verify_ssl": True
            },
            
            # 代理设置
            "proxy": {
                "enabled": False,
                "type": "http",  # http, socks4, socks5
                "host": "",
                "port": "",
                "username": "",
                "password": "",
                "use_auth": False
            },
            
            # Python版本管理
            "python_versions": {
                "installations": [],  # 确保这是一个空列表
                "default_version": "",
                "windows_specific": {  # Windows平台特有设置
                    "registry_paths": [  # Windows注册表路径
                        "SOFTWARE\\Python\\PythonCore",
                        "SOFTWARE\\Wow6432Node\\Python\\PythonCore"
                    ],
                    "common_paths": [  # 常见安装路径
                        "C:\\Python*",
                        "%USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python*",
                        "%USERPROFILE%\\scoop\\apps\\python\\current\\python.exe",
                        "%USERPROFILE%\\miniconda3\\python.exe",
                        "%USERPROFILE%\\anaconda3\\python.exe"
                    ]
                }
            },
            
            # Python安装信息 (兼容旧版设置)
            "python": {
                "installations": []  # 确保这是一个空列表
            },
            
            # 高级设置
            "advanced": {
                "debug_mode": False,
                "log_level": "info",  # debug, info, warning, error
                "clear_cache_on_exit": False,
                "check_updates": True,
                "update_channel": "stable"  # stable, beta, dev
            },
            
            # 更新设置
            "updates": {
                "auto_check": True,
                "last_check": "",
                "available_version": "",
                "check_interval": 7  # 天
            },
            
            # 网络测试设置
            "net_test": {
                "servers": [
                    {"name": "百度", "url": "https://www.baidu.com"},
                    {"name": "阿里云", "url": "https://www.aliyun.com"},
                    {"name": "腾讯云", "url": "https://cloud.tencent.com"},
                    {"name": "PyPI", "url": "https://pypi.org"}
                ],
                "last_test": None,  # 上次测试时间
                "last_result": {}   # 上次测试结果
            },
            
            # 镜像服务器设置
            "mirror": {
                "sources": [
                    {"name": "官方源", "url": "https://pypi.org/simple"},
                    {"name": "清华源", "url": "https://pypi.tuna.tsinghua.edu.cn/simple"},
                    {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple"},
                    {"name": "豆瓣", "url": "https://pypi.douban.com/simple"}
                ],
                "selected": "官方源",  # 当前选择的镜像源
                "last_checked": None  # 上次检查时间
            }
        }
    
    def _load_settings(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    # 合并用户设置到默认设置
                    self._merge_settings(user_settings)
                logger.info("设置加载成功")
            else:
                # 如果文件不存在，确保配置目录存在并保存默认设置
                os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
                self.save_settings()
                logger.info("已创建默认设置文件")
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
    
    def get_default_python_version(self):
        """
        获取默认Python版本
        
        Returns:
            str: 默认Python版本路径
        """
        try:
            return self.settings["python_versions"]["default_version"]
        except KeyError:
            return ""
            
    def _merge_settings(self, user_settings, target = None, path = ""):
        """
        递归合并用户设置到默认设置
        
        Args:
            user_settings: 用户设置
            target: 目标设置字典，默认为self.settings
            path: 当前设置路径，用于日志
        """
        if target is None:
            target = self.settings
            
        for key, value in user_settings.items():
            current_path = f"{path}.{key}" if path else key
            
            # 特殊处理 python_versions 字段，确保它的结构正确
            if key == "python_versions":
                # 如果值是字符串，尝试解析为JSON
                if isinstance(value, str):
                    try:
                        import json
                        value = json.loads(value)
                    except:
                        logger.error(f"无法解析python_versions数据: {value}")
                        value = {"installations": [], "default_version": ""}
                
                # 如果值不是字典类型，设置为正确的结构
                if not isinstance(value, dict):
                    logger.error(f"python_versions数据类型错误: {type(value)}")
                    value = {"installations": [], "default_version": ""}
                    
                # 确保installations字段存在且为列表
                if "installations" not in value:
                    value["installations"] = []
                elif not isinstance(value["installations"], list):
                    # 尝试转换字符串为列表
                    if isinstance(value["installations"], str):
                        try:
                            import json
                            installations = json.loads(value["installations"])
                            if isinstance(installations, list):
                                value["installations"] = installations
                            else:
                                value["installations"] = []
                        except:
                            value["installations"] = []
                    else:
                        value["installations"] = []
                
                # 确保default_version字段存在且正确处理false值
                if "default_version" not in value:
                    value["default_version"] = ""
                elif value["default_version"] == False:
                    value["default_version"] = ""
                
                target[key] = value
                logger.debug(f"合并python_versions数据: {current_path}")
                continue
                
            # 特殊处理installations列表
            if key == "installations" and isinstance(value, (list, str)):
                # 确保值是列表类型
                if isinstance(value, str):
                    try:
                        import json
                        value = json.loads(value)
                    except:
                        logger.error(f"无法解析installations数据: {value}")
                        value = []
                
                # 如果值仍然不是列表，设为空列表
                if not isinstance(value, list):
                    logger.error(f"installations数据类型错误: {type(value)}")
                    value = []
                
                target[key] = value
                logger.debug(f"合并installations数据: {current_path} = {value}")
                continue
            
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # 如果都是字典，递归合并
                self._merge_settings(value, target[key], current_path)
            else:
                # 否则直接覆盖
                target[key] = value
                logger.debug(f"加载用户设置: {current_path} = {value}")
    
    def save_settings(self) -> bool:
        """
        保存设置到文件
        
        Returns:
            是否成功保存
        """
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info("设置保存成功")
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取设置值，支持点分隔的嵌套键名
        
        Args:
            key: 设置键名，如 "interface.language"
            default: 默认值
        
        Returns:
            设置值
        """
        if "." not in key:
            return self.settings.get(key, default)
    
        # 处理嵌套键
        keys = key.split(".")
        value = self.settings
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            # 特殊处理: 确保列表类型不被错误转换为字符串
            if isinstance(value, list) and key.endswith(".installations"):
                # 深拷贝确保不修改原始数据
                import copy
                return copy.deepcopy(value)
                
            return value
        except Exception as e:
            logger.error(f"获取设置值失败: {key}, 错误: {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置值，支持点分隔的嵌套键名
        
        Args:
            key: 设置键名，如 "interface.language"
            value: 设置值
            
        Returns:
            是否成功设置
        """
        try:
            if "." not in key:
                self.settings[key] = value
                logger.debug(f"设置更新: {key} = {value}")
                return True
            
            # 处理嵌套键
            keys = key.split(".")
            target = self.settings
            
            # 导航到最后一级的父字典
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                elif not isinstance(target[k], dict):
                    target[k] = {}
                
                target = target[k]
            
            # 设置最后一级的值
            target[keys[-1]] = value
            logger.debug(f"设置更新: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"设置值失败: {key} = {value}, 错误: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有设置
        
        Returns:
            所有设置的字典
        """
        return self.settings

def init_manager(config_path: str) -> Optional[SettingsManager]:
    """
    初始化设置管理器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        设置管理器实例
    """
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager(config_path)
    return _settings_manager_instance

def get_manager() -> Optional[SettingsManager]:
    """
    获取设置管理器实例
    
    Returns:
        设置管理器实例
    """
    global _settings_manager_instance
    return _settings_manager_instance

# 主题管理器实例
_theme_manager_instance = None

def init_theme_manager(config_path: str) -> Optional[SettingsManager]:
    """
    初始化主题管理器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        主题管理器实例
    """
    global _theme_manager_instance
    if _theme_manager_instance is None:
        theme_path = os.path.join(config_path, "themes")
        os.makedirs(theme_path, exist_ok=True)
        _theme_manager_instance = SettingsManager(theme_path)
    return _theme_manager_instance

def get_theme_manager() -> Optional[SettingsManager]:
    """
    获取主题管理器实例
    
    Returns:
        主题管理器实例
    """
    global _theme_manager_instance
    return _theme_manager_instance
