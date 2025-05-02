"""
PyQuick设置管理模块

负责管理应用程序的各种配置设置，包括常规设置、镜像管理、代理配置和多版本Python管理等。
"""

# 导出主要类和函数
from settings.settings_manager import SettingsManager, ThemeManager
from settings.settings_manager import init_manager, get_manager
from settings.settings_manager import init_theme_manager, get_theme_manager
from settings.ui import SettingsWindow

__all__ = [
    'SettingsManager',
    'ThemeManager',
    'SettingsWindow',
    'init_manager',
    'get_manager',
    'init_theme_manager',
    'get_theme_manager'
] 