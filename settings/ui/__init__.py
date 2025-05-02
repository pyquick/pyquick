"""
设置界面模块，包含所有设置面板和主窗口
"""

from settings.ui.window import SettingsWindow
from settings.ui.base_panel import BaseSettingsPanel
from settings.ui.general import GeneralSettingsPanel
from settings.ui.appearance import AppearanceSettingsPanel
from settings.ui.download import DownloadSettingsPanel
from settings.ui.proxy import ProxySettingsPanel
from settings.ui.python import PythonSettingsPanel
from settings.ui.advanced import AdvancedSettingsPanel

# 导出主要类和函数
__all__ = [
    'SettingsWindow',
    'BaseSettingsPanel',
    'GeneralSettingsPanel',
    'AppearanceSettingsPanel',
    'DownloadSettingsPanel',
    'ProxySettingsPanel',
    'PythonSettingsPanel',
    'AdvancedSettingsPanel'
] 