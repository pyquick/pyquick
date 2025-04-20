"""
PyQuick UI 模块
包含应用程序的用户界面元素和功能
"""

# 导出对话框模块
from ui.dialogs import show_about_dialog, show_settings_dialog, show_debug_dialog

# 导出所有功能
__all__ = [
    'show_about_dialog',
    'show_settings_dialog',
    'show_debug_dialog'
] 