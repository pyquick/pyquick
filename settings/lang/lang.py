"""
多语言支持模块
"""
import os
import json
from typing import Dict, Optional

class LanguageManager:
    """
    语言管理器类，负责加载和管理多语言资源
    """
    
    def __init__(self, lang_dir: str = None):
        """
        初始化语言管理器
        
        Args:
            lang_dir: 语言资源文件目录路径
        """
        self.lang_dir = lang_dir or os.path.join(os.path.dirname(__file__), 'resources')
        self.languages: Dict[str, Dict[str, str]] = {}
        self.current_lang = 'en'  # 默认英语
        
    def load_language(self, lang_code: str) -> bool:
        """
        加载指定语言资源
        
        Args:
            lang_code: 语言代码，如'en', 'zh'等
            
        Returns:
            bool: 是否加载成功
        """
        lang_file = os.path.join(self.lang_dir, f"{lang_code}.json")
        
        if not os.path.exists(lang_file):
            return False
            
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.languages[lang_code] = json.load(f)
            return True
        except Exception as e:
            print(f"加载语言文件失败: {e}")
            return False
    
    def get_text(self, key: str, lang_code: Optional[str] = None) -> str:
        """
        获取指定键的翻译文本
        
        Args:
            key: 翻译键
            lang_code: 语言代码，如未指定则使用当前语言
            
        Returns:
            str: 翻译文本，如找不到则返回键本身
        """
        lang = lang_code or self.current_lang
        
        if lang not in self.languages:
            if not self.load_language(lang):
                return key
                
        return self.languages[lang].get(key, key)
    
    def set_language(self, lang_code: str) -> bool:
        """
        设置当前语言
        
        Args:
            lang_code: 语言代码
            
        Returns:
            bool: 是否设置成功
        """
        if lang_code in self.languages or self.load_language(lang_code):
            self.current_lang = lang_code
            return True
        return False

# 单例模式
language_manager = LanguageManager()