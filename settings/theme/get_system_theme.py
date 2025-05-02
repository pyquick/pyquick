#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统主题检测模块
负责检测系统当前的主题设置
"""

import darkdetect
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_system_theme() -> Dict[str, Any]:
    """
    获取系统当前主题设置
    
    Returns:
        主题配置字典
    """
    try:
        # 检测系统主题
        is_dark = darkdetect.isDark()
        
        # 返回对应的主题配置
        if is_dark:
            return {
                "name": "dark",
                "display_name": "系统深色",
                "colors": {
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                    "background": "#1e1e1e",
                    "text": "#ffffff"
                }
            }
        else:
            return {
                "name": "light",
                "display_name": "系统浅色",
                "colors": {
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                    "background": "#ffffff",
                    "text": "#000000"
                }
            }
    except Exception as e:
        logger.error(f"获取系统主题失败: {e}")
        # 出错时返回默认浅色主题
        return {
            "name": "light",
            "display_name": "默认浅色",
            "colors": {
                "primary": "#007acc",
                "secondary": "#6c757d",
                "background": "#ffffff",
                "text": "#000000"
            }
        }