"""
设置保存模块

负责管理设置的加载、保存和更新，确保设置能够正确持久化。
"""

import json
import os, sys, subprocess
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Tuple, Union

logger = logging.getLogger("settings")

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
        if not os.path.exists(self.settings_file):
            self._save_settings(self.default_settings)
        with open(self.settings_file, 'r', encoding='utf-8') as f:
            self.user_settings = json.load(f)
        self.lock = threading.RLock()
        self._auto_save_timer = None
        self._modified = False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """
        获取默认设置
        
        Returns:
            默认设置字典
        """
        return {
            # 常规设置
            "general": {
                "theme": "auto",  # auto, light, dark
                "auto_check_pip_updates": True,
                "log_size_limit": 10.0,  # 单位MB
                "log_size_unit": "MB",  # 单位选择：KB, MB, GB
                "enable_multi_thread_download": True,
                "download_threads": 4
            },
            
            # 镜像设置
            "mirrors": {
                "python_mirror": {
                    "name": "官方源",
                    "url": "https://www.python.org/ftp/python/",
                    "enabled": True
                },
                "pip_mirror": {
                    "name": "官方源",
                    "url": "https://pypi.org/simple/",
                    "enabled": True
                },
                "auto_select_best_mirror": True
            },
            
            # 代理设置
            "proxy": {
                "enabled": False,
                "type": "http",
                "host": "",
                "port": "",
                "username": "",
                "password": "",
                "use_auth": False
            },
            
            # Python版本管理设置
            "python_versions": {
                "installations": [],
                "default_version": ""
            },
            
            # UI设置
            "ui": {
                "window_width": 800,
                "window_height": 600,
                "remember_size": True,
                "start_minimized": False
            }
        }
        
    def scan_system_python_installations(self) -> List[Dict[str, Union[str, bool]]]:
        """
        扫描系统中安装的Python版本
        
        Returns:
            包含Python安装信息的字典列表，每个字典包含 'path', 'version', 'is_system' 和 'default' 键
        """
        installations = []
        
        # 1. 检查当前sys.executable
        if sys.executable:
            version = self._get_python_version(sys.executable)
            if version:
                installations.append({
                    "path": sys.executable,
                    "version": version,
                    "is_system": True,  # 标记为系统Python
                    "default": True
                })
        
        # 2. 扫描Windows注册表查找其他Python安装
        try:
            import winreg
            
            # 检查32位和64位注册表路径
            for arch in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for key_path in [
                    r"SOFTWARE\\Python\\PythonCore",
                    r"SOFTWARE\\Wow6432Node\\Python\\PythonCore"
                ]:
                    try:
                        with winreg.OpenKey(arch, key_path) as key:
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                version = winreg.EnumKey(key, i)
                                try:
                                    with winreg.OpenKey(key, f"{version}\\InstallPath") as install_key:
                                        path = winreg.QueryValue(install_key, "")
                                        python_exe = os.path.join(path, "python.exe")
                                        if os.path.exists(python_exe):
                                            # 检查此路径是否与sys.executable相同
                                            is_current_sys_executable = (os.path.normcase(python_exe) == os.path.normcase(sys.executable))
                                            # 如果已经作为sys.executable添加过了，则跳过，避免重复
                                            if not any(p['path'] == python_exe and p.get('is_system') for p in installations):
                                                installations.append({
                                                    "path": python_exe,
                                                    "version": version,
                                                    "is_system": is_current_sys_executable, # 标记是否为系统Python
                                                    "default": False
                                                })
                                except WindowsError:
                                    continue
                    except WindowsError:
                        continue
        except ImportError:
            pass
        
        return installations
        
    def _get_python_version(self, python_path: str) -> Optional[str]:
        """
        获取指定Python路径的版本号
        
        Args:
            python_path: Python可执行文件路径
            
        Returns:
            版本号字符串，如"3.9.0"，如果获取失败返回None
        """
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                if version_str.startswith("Python "):
                    return version_str[7:]
        except Exception:
            pass
        return None
        
    def update_python_installations(self) -> bool:
        """
        更新settings.json中的Python安装信息
        
        Returns:
            是否成功更新
        """
        installations = self.scan_system_python_installations()
        # 确保 installations 是一个列表，即使为空也应该写入
        return self.set_setting("python_versions.installations", installations if installations else [])

    def auto_save_system_python(self) -> None:
        """
        自动扫描并保存系统Python版本信息到设置中。
        """
        logger.info("开始自动扫描并保存系统Python版本信息...")
        installations = self.scan_system_python_installations()
        if self.set_setting("python_versions.installations", installations if installations else []):
            logger.info("系统Python版本信息已成功保存到 python_versions.installations")
        else:
            logger.error("保存系统Python版本信息失败")
    
    def load_settings(self):
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
                    
                    # 如果没有设置默认Python版本，则自动设置系统Python为默认版本
                    if not self.settings["python_versions"]["default_version"] and sys.executable:
                        self.settings["python_versions"]["default_version"] = sys.executable
                        logger.info(f"自动设置系统Python {sys.executable} 为默认版本")
                        self.save_settings()

                    return user_settings
                else:
                    # 如果设置文件不存在，使用默认设置
                    self.settings = self.default_settings.copy()
                    logger.info("设置文件不存在，使用默认设置")
                    
                    # 保存默认设置到文件
                    self.save_settings()
                    return self.settings
            except Exception as e:
                logger.error(f"加载设置失败: {e}")
                self.settings = self.default_settings.copy()
                return False
    
    def _merge_user_settings(self, user_settings_model: Dict[str, Any], merge_base: Dict[str, Any], key_path: str = "") -> Dict[str, Any]:
        """
        递归合并用户设置模型到基础字典中，处理嵌套字典结构
        
        该方法递归地将用户设置模型(user_settings_model)合并到基础字典(merge_base)中，
        支持通过key_path的点分格式路径进行深度查找和替换。
        
        Args:
            user_settings_model: 要合并的用户设置字典，包含新的设置值
            merge_base: 目标字典，通常是默认设置或父级设置字典
            key_path: 当前递归路径，用于深度查找和替换，格式为"parent.child"
            
        Returns:
            Dict[str, Any]: 合并后的设置字典
        
        Raises:
            RecursionError: 当递归深度过大时记录警告
            Exception: 合并过程中可能抛出各种异常
        """
        # 防止递归过深导致栈溢出
        if len(key_path.split('.')) > 10e9:
            logger.warning(f"递归深度过大，可能存在循环引用，路径: {key_path}")
            return merge_base
            
        try:
            # 如果有key_path，则进行深度查找和替换
            if key_path:
                keys = key_path.split('.')
                current = merge_base
                
                # 遍历key_path直到倒数第二个key
                for key in keys[:-1]:
                    if key not in current or not isinstance(current[key], dict):
                        # 如果路径不存在，创建中间字典
                        current[key] = {}
                    current = current[key]
                
                # 替换最后一个key的值
                last_key = keys[-1]
                current[last_key] = user_settings_model
                return merge_base
                
            # 如果没有key_path，执行常规合并
            merged = merge_base.copy()
            
            # 遍历用户设置模型中的所有键值对
            for key, value in user_settings_model.items():
                # 处理嵌套字典的情况
                if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                    # 递归合并嵌套字典
                    merged[key] = self._merge_user_settings(value, merged[key])
                else:
                    # 使用用户设置的值覆盖基础设置
                    merged[key] = value
                    
            return merged
        except Exception as e:
            logger.error(f"合并设置失败(路径: {key_path}): {str(e)}")
            return merge_base
            
    def _merge_settings(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并设置
        
        Args:
            default: 默认设置
            user: 用户设置
            
        Returns:
            合并后的设置
        """
        return self._merge_user_settings(user, default, "")
    
    def save_settings(self,settings_yours:Dict[str,Any]=None) -> bool:
        """
        保存设置到文件
        
        Returns:
            是否成功保存
        """
        if settings_yours is not None:
            self.settings=settings_yours
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
    
    def get_setting(self, key_path: str) -> Any:
        """
        获取设置值
        
        Args:
            key_path: 设置键路径，如 "general.theme"
            default: 如果设置不存在，返回此默认值
            
        Returns:
            设置值
        """
        with self.lock:
            try:
                parts = key_path.split('.')
                current = self.user_settings
                
                for part in parts:
                    current = current[part]
                
                return current
            except (KeyError, TypeError):
                print(f"设置 {key_path} 不存在")
                return False
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        设置值
        
        Args:
            key_path: 设置键路径，如 "general.theme"
            value: 要设置的值
            
        Returns:
            是否成功设置
        """
        with self.lock:
            try:
                parts = key_path.split('.')
                current = self.user_settings
                
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
                
                return current
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
                if not self.set_setting(key_path, value):
                    success = False
        
        # 立即保存更改
        if success and self._modified:
            success = self.save_settings()
        
        return success