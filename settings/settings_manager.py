#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设置管理器模块
负责加载、保存和管理程序配置
作为settings模块的主入口
"""

import os
import sys
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# 设置管理器单例
_settings_manager_instance = None
# 主题管理器单例
_theme_manager_instance = None

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
        self.default_settings = self._get_default_settings()
        self.lock = threading.RLock()
        self._auto_save_timer = None
        self._modified = False

        # 加载设置
        self.load_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """
        获取默认设置
        
        Returns:
            默认设置字典
        """
        return {
            # 主题设置
            "theme": {
                "current_theme": "系统默认",
                "custom_themes": []
            },
            
            # 更新设置
            "updates": {
                "check_pip_updates": True,
                "check_package_status": True,
                "auto_check_updates": True,
                "update_channel": "stable"
            },
            
            # 日志设置
            "logging": {
                "max_size_value": 10.0,
                "max_size_unit": "MB",
                "log_level": "INFO"
            },
            
            # 下载设置
            "downloads": {
                "use_multi_thread": True,
                "thread_count": 4,
                "default_save_path": "",
                "timeout": 30
            },
            
            # Python设置
            "python": {
                "installations": [],
                "default_version": "",
                "auto_detect": True
            },
            
            # 代理设置
            "proxy": {
                "enable": False,
                "type": "http",
                "http": "",
                "https": "",
                "socks": "",
                "exclude": "localhost,127.0.0.1"
            },
            
            # 镜像设置
            "mirrors": {
                "python": {
                    "name": "官方源",
                    "url": "https://www.python.org/ftp/python/",
                    "enabled": True
                },
                "pip": {
                    "name": "官方源",
                    "url": "https://pypi.org/simple/",
                    "enabled": True
                },
                "auto_select_best": True
            },
            
            # UI设置
            "ui": {
                "window_width": 800,
                "window_height": 600,
                "remember_size": True,
                "start_minimized": False
            }
        }

    def load_settings(self) -> bool:
        """
        从文件加载设置
        
        Returns:
            是否成功加载
        """
        with self.lock:
            try:
                if os.path.exists(self.settings_file):
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        user_settings = json.load(f)
                    
                    # 合并默认设置和用户设置
                    self.settings = self._merge_settings(self.default_settings.copy(), user_settings)
                    logger.info(f"已从 {self.settings_file} 加载设置")
                    return True
                else:
                    # 如果设置文件不存在，使用默认设置
                    self.settings = self.default_settings.copy()
                    logger.info("设置文件不存在，使用默认设置")
                    
                    # 保存默认设置到文件
                    self.save_settings()
                    return True
            except Exception as e:
                logger.error(f"加载设置失败: {e}")
                self.settings = self.default_settings.copy()
                return False

    def _merge_settings(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并设置
        
        Args:
            default: 默认设置
            user: 用户设置
            
        Returns:
            合并后的设置
        """
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                # 递归合并子字典
                self._merge_settings(default[key], value)
            else:
                # 直接更新值
                default[key] = value
        
        return default

    def save_settings(self) -> bool:
        """
        保存设置到文件
        
        Returns:
            是否成功保存
        """
        with self.lock:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
                
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                
                self._modified = False
                logger.info(f"已保存设置到 {self.settings_file}")
                return True
            except Exception as e:
                logger.error(f"保存设置失败: {e}")
                return False

    def get(self, key_path: str, default=None) -> Any:
        """
        获取设置值
        
        Args:
            key_path: 设置键路径，如 "theme.current_theme"
            default: 如果设置不存在，返回此默认值
            
        Returns:
            设置值
        """
        with self.lock:
            try:
                parts = key_path.split('.')
                current = self.settings
                
                for part in parts:
                    current = current[part]
                
                return current
            except (KeyError, TypeError):
                return default

    def set(self, key_path: str, value: Any) -> bool:
        """
        设置值
        
        Args:
            key_path: 设置键路径，如 "theme.current_theme"
            value: 要设置的值
            
        Returns:
            是否成功设置
        """
        with self.lock:
            try:
                parts = key_path.split('.')
                current = self.settings
                
                # 遍历路径的所有部分，除了最后一个
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 设置最后一个部分
                current[parts[-1]] = value
                self._modified = True
                
                # 启动自动保存定时器
                self._schedule_auto_save()
                
                return True
            except Exception as e:
                logger.error(f"设置 {key_path} 为 {value} 失败: {e}")
        return False

    def _schedule_auto_save(self, delay: int = 5):
        """
        计划自动保存
        
        Args:
            delay: 延迟保存的秒数
        """
        if self._auto_save_timer:
            # 如果已有定时器，取消它
            self._auto_save_timer.cancel()
        
        # 创建新的定时器
        self._auto_save_timer = threading.Timer(delay, self._auto_save)
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()

    def _auto_save(self):
        """自动保存设置"""
        if self._modified:
            self.save_settings()

    def reset_to_default(self, section: Optional[str] = None) -> bool:
        """
        重置设置为默认值
        
        Args:
            section: 要重置的设置部分，如果为None则重置所有设置
            
        Returns:
            是否成功重置
        """
        with self.lock:
            try:
                if section is None:
                    self.settings = self.default_settings.copy()
                elif section in self.default_settings:
                    self.settings[section] = self.default_settings[section].copy()
                else:
                    logger.warning(f"未知的设置部分: {section}")
                    return False
                
                self._modified = True
                self._schedule_auto_save()
                
                logger.info(f"已重置设置 {section if section else '所有'}")
                return True
            except Exception as e:
                logger.error(f"重置设置失败: {e}")
                return False

    def update_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """
        批量更新设置
        
        Args:
            settings_dict: 设置字典，键为设置路径，值为设置值
            
        Returns:
            是否成功更新
        """
        success = True
        with self.lock:
            for key_path, value in settings_dict.items():
                if not self.set(key_path, value):
                    success = False
        
        # 立即保存更改
        if success and self._modified:
            success = self.save_settings()
        
        return success

class ThemeManager:
    """主题管理器类"""
    
    def __init__(self, settings_manager: SettingsManager, themes_dir: str = None):
        """
        初始化主题管理器
        
        Args:
            settings_manager: 设置管理器实例
            themes_dir: 主题文件夹路径
        """
        self.settings_manager = settings_manager
        
        # 设置主题目录
        if themes_dir:
            self.themes_dir = themes_dir
        else:
            self.themes_dir = os.path.join(settings_manager.config_path, "themes")
        
        # 确保主题目录存在
        os.makedirs(self.themes_dir, exist_ok=True)
        
        # 默认主题
        self.default_themes = {
            "系统默认": {
                "name": "系统默认",
                "type": "auto",
                "description": "根据系统设置自动选择亮色或暗色主题",
                "colors": {}
            },
            "亮色主题": {
                "name": "亮色主题",
                "type": "light",
                "description": "默认亮色主题",
                "colors": {}
            },
            "暗色主题": {
                "name": "暗色主题",
                "type": "dark",
                "description": "默认暗色主题",
                "colors": {}
            }
        }
        
        # 所有主题，包括自定义主题
        self.themes = self.default_themes.copy()
        
        # 加载自定义主题
        self.load_custom_themes()
    
    def load_custom_themes(self) -> bool:
        """
        加载自定义主题
        
        Returns:
            是否成功加载
        """
        try:
            # 获取保存的自定义主题
            custom_themes = self.settings_manager.get("theme.custom_themes", [])
            
            # 加载主题文件夹中的主题
            for filename in os.listdir(self.themes_dir):
                if filename.endswith(".json"):
                    try:
                        theme_path = os.path.join(self.themes_dir, filename)
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                        
                        # 验证主题数据
                        if self._validate_theme(theme_data):
                            # 如果主题不在保存的列表中，添加到列表
                            theme_name = theme_data.get("name")
                            if theme_name and not any(t.get("name") == theme_name for t in custom_themes):
                                custom_themes.append(theme_data)
                    except Exception as e:
                        logger.error(f"加载主题文件 {filename} 失败: {e}")
            
            # 更新设置管理器中的自定义主题列表
            self.settings_manager.set("theme.custom_themes", custom_themes)
            
            # 将自定义主题添加到主题字典
            for theme in custom_themes:
                theme_name = theme.get("name")
                if theme_name:
                    self.themes[theme_name] = theme
            
            logger.info(f"已加载 {len(custom_themes)} 个自定义主题")
            return True
        except Exception as e:
            logger.error(f"加载自定义主题失败: {e}")
            return False
    
    def _validate_theme(self, theme_data: Dict[str, Any]) -> bool:
        """
        验证主题数据
        
        Args:
            theme_data: 主题数据
            
        Returns:
            是否有效
        """
        # 检查必需字段
        required_fields = ["name", "type", "description", "colors"]
        for field in required_fields:
            if field not in theme_data:
                logger.warning(f"主题缺少必需字段: {field}")
                return False
        
        # 检查主题类型
        if theme_data["type"] not in ["light", "dark", "auto"]:
            logger.warning(f"无效的主题类型: {theme_data['type']}")
            return False
        
        # 检查颜色
        if not isinstance(theme_data["colors"], dict):
            logger.warning("主题颜色必须是字典类型")
            return False
        
        return True
    
    def get_available_themes(self) -> List[str]:
        """
        获取可用主题列表
        
        Returns:
            主题名称列表
        """
        return list(self.themes.keys())
    
    def get_current_theme(self) -> Dict[str, Any]:
        """
        获取当前主题
        
        Returns:
            当前主题数据
        """
        theme_name = self.settings_manager.get("theme.current_theme", "系统默认")
        return self.themes.get(theme_name, self.default_themes["系统默认"])
    
    def set_current_theme(self, theme_name: str) -> bool:
        """
        设置当前主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            是否成功设置
        """
        if theme_name in self.themes:
            self.settings_manager.set("theme.current_theme", theme_name)
            logger.info(f"已设置当前主题: {theme_name}")
            return True
        else:
            logger.warning(f"未知的主题: {theme_name}")
            return False
    
    def apply_theme(self, window) -> bool:
        """
        应用主题到窗口
        
        Args:
            window: tkinter窗口
            
        Returns:
            是否成功应用
        """
        try:
            # 获取当前主题
            theme = self.get_current_theme()
            theme_type = theme.get("type", "auto")
            
            # 如果是使用sv_ttk包，尝试应用
            try:
                import sv_ttk
                # 如果是自动主题，尝试使用darkdetect检测系统主题
                if theme_type == "auto":
                    try:
                        import darkdetect
                        theme_type = "dark" if darkdetect.isDark() else "light"
                    except ImportError:
                        theme_type = "light"  # 默认使用亮色主题
                
                # 应用sv_ttk主题
                sv_ttk.set_theme(theme_type)
                logger.info(f"已应用sv_ttk主题: {theme_type}")
                return True
            except ImportError:
                logger.warning("未安装sv_ttk，无法应用主题")
            
            # 如果有自定义颜色，应用它们
            colors = theme.get("colors", {})
            for widget, color in colors.items():
                try:
                    pass  # 自定义逻辑...
                except Exception as e:
                    logger.error(f"应用颜色失败: {widget} => {color}, {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
            return False
    
    def create_theme(self, name: str, theme_type: str, description: str, colors: Dict[str, str]) -> bool:
        """
        创建新主题
        
        Args:
            name: 主题名称
            theme_type: 主题类型，可以是 "light", "dark" 或 "auto"
            description: 主题描述
            colors: 主题颜色字典
            
        Returns:
            是否成功创建
        """
        try:
            # 检查主题名称是否已存在
            if name in self.themes:
                logger.warning(f"主题已存在: {name}")
                return False
            
            # 检查主题类型
            if theme_type not in ["light", "dark", "auto"]:
                logger.warning(f"无效的主题类型: {theme_type}")
                return False
            
            # 创建主题数据
            theme_data = {
                "name": name,
                "type": theme_type,
                "description": description,
                "colors": colors
            }
            
            # 验证主题数据
            if not self._validate_theme(theme_data):
                return False
            
            # 将主题添加到自定义主题列表
            custom_themes = self.settings_manager.get("theme.custom_themes", [])
            custom_themes.append(theme_data)
            self.settings_manager.set("theme.custom_themes", custom_themes)
            
            # 将主题添加到主题字典
            self.themes[name] = theme_data
            
            # 保存主题到文件
            theme_path = os.path.join(self.themes_dir, f"{name}.json")
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"已创建主题: {name}")
            return True
        except Exception as e:
            logger.error(f"创建主题失败: {e}")
            return False
    
    def delete_theme(self, name: str) -> bool:
        """
        删除主题
        
        Args:
            name: 主题名称
            
        Returns:
            是否成功删除
        """
        try:
            # 检查是否是默认主题
            if name in self.default_themes:
                logger.warning(f"无法删除默认主题: {name}")
                return False
                
            # 检查主题是否存在
            if name not in self.themes:
                logger.warning(f"主题不存在: {name}")
                return False
            
            # 从自定义主题列表中删除
            custom_themes = self.settings_manager.get("theme.custom_themes", [])
            custom_themes = [t for t in custom_themes if t.get("name") != name]
            self.settings_manager.set("theme.custom_themes", custom_themes)
            
            # 从主题字典中删除
            del self.themes[name]
            
            # 删除主题文件
            theme_path = os.path.join(self.themes_dir, f"{name}.json")
            if os.path.exists(theme_path):
                os.remove(theme_path)
            
            # 如果当前主题是被删除的主题，重置为默认主题
            current_theme = self.settings_manager.get("theme.current_theme")
            if current_theme == name:
                self.settings_manager.set("theme.current_theme", "系统默认")
            
            logger.info(f"已删除主题: {name}")
            return True
        except Exception as e:
            logger.error(f"删除主题失败: {e}")
            return False
    
    def update_theme(self, name: str, theme_type: str = None, description: str = None, colors: Dict[str, str] = None) -> bool:
        """
        更新主题
        
        Args:
            name: 主题名称
            theme_type: 主题类型，可以是 "light", "dark" 或 "auto"
            description: 主题描述
            colors: 主题颜色字典
            
        Returns:
            是否成功更新
        """
        try:
            # 检查主题是否存在
            if name not in self.themes:
                logger.warning(f"主题不存在: {name}")
                return False
            
            # 获取主题数据
            theme_data = self.themes[name].copy()
            
            # 更新主题属性
            if theme_type is not None:
                if theme_type not in ["light", "dark", "auto"]:
                    logger.warning(f"无效的主题类型: {theme_type}")
                    return False
                theme_data["type"] = theme_type
            
            if description is not None:
                theme_data["description"] = description
            
            if colors is not None:
                theme_data["colors"] = colors
            
            # 验证主题数据
            if not self._validate_theme(theme_data):
                return False
            
            # 检查是否是默认主题
            if name in self.default_themes:
                # 如果是默认主题，只更新内存中的主题
                self.themes[name] = theme_data
            else:
                # 更新自定义主题列表
                custom_themes = self.settings_manager.get("theme.custom_themes", [])
                for i, theme in enumerate(custom_themes):
                    if theme.get("name") == name:
                        custom_themes[i] = theme_data
                        break
                self.settings_manager.set("theme.custom_themes", custom_themes)
                
                # 更新主题字典
                self.themes[name] = theme_data
                
                # 保存主题到文件
                theme_path = os.path.join(self.themes_dir, f"{name}.json")
                with open(theme_path, 'w', encoding='utf-8') as f:
                    json.dump(theme_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"已更新主题: {name}")
            return True
        except Exception as e:
            logger.error(f"更新主题失败: {e}")
            return False
    
    def get_theme(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取主题
        
        Args:
            name: 主题名称
            
        Returns:
            主题数据
        """
        return self.themes.get(name)

# 初始化函数
def init_manager(config_path: str) -> SettingsManager:
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

def get_manager() -> SettingsManager:
    """
    获取设置管理器实例
    
    Returns:
        设置管理器实例
    """
    global _settings_manager_instance
    if _settings_manager_instance is None:
        raise RuntimeError("设置管理器尚未初始化")
    return _settings_manager_instance

def init_theme_manager(themes_dir: str = None) -> ThemeManager:
    """
    初始化主题管理器
    
    Args:
        themes_dir: 主题文件夹路径
        
    Returns:
        主题管理器实例
    """
    global _theme_manager_instance, _settings_manager_instance
    if _theme_manager_instance is None:
        if _settings_manager_instance is None:
            raise RuntimeError("请先初始化设置管理器")
        _theme_manager_instance = ThemeManager(_settings_manager_instance, themes_dir)
    return _theme_manager_instance

def get_theme_manager() -> ThemeManager:
    """
    获取主题管理器实例
    
    Returns:
        主题管理器实例
    """
    global _theme_manager_instance
    if _theme_manager_instance is None:
        raise RuntimeError("主题管理器尚未初始化")
    return _theme_manager_instance

# 显示设置窗口
def show_settings_window(parent_window):
    """
    显示设置窗口
    
    Args:
        parent_window: 父窗口
    """
    from .ui import open_settings_window
    
    # 获取实例
    settings_manager = get_manager()
    theme_manager = get_theme_manager()
    
    # 打开设置窗口
    return open_settings_window(parent_window, settings_manager, theme_manager) 