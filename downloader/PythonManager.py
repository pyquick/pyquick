#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python版本管理器模块
负责查找系统中的Python安装并提供管理功能
"""

import os
import sys
import subprocess
import platform
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PythonManager:
    """Python安装管理类，负责查找和管理系统中的Python安装"""
    
    def __init__(self, settings_manager=None):
        """初始化Python管理器
        
        Args:
            settings_manager: 设置管理器实例
        """
        # Python安装列表
        self.python_installations = []
        # 默认Python安装
        self.default_installation = None
        # 设置管理器
        self.settings_manager = settings_manager
        # 初始化时加载Python安装
        self._load_python_installations()
        
    def _load_python_installations(self):
        """加载系统中已有的Python安装"""
        try:
            # 从配置文件加载已保存的安装信息
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'installations' in data and isinstance(data['installations'], list):
                        self.python_installations = data['installations']
                        # 查找默认安装
                        for install in self.python_installations:
                            if install.get('is_default', False):
                                self.default_installation = install
                                break
            
            # 添加系统Python到安装列表
            sys_python = {
                'name': '系统Python',
                'version': sys.version.split()[0],
                'path': sys.executable,
                'is_default': False
            }
            if not any(install['path'] == sys.executable for install in self.python_installations):
                self.python_installations.append(sys_python)
            
            # 如果没有加载到任何安装，或者没有默认安装，则尝试自动检测
            if not self.python_installations or not self.default_installation:
                self._auto_detect_python()
                
        except Exception as e:
            logger.error(f"加载Python安装信息失败: {str(e)}")
            # 出错时尝试自动检测
            self._auto_detect_python()
    
    def _save_python_installations(self):
        """保存Python安装信息到配置文件"""
        try:
            config_path = self._get_config_path()
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'installations': self.python_installations}, f, ensure_ascii=False, indent=2)
                
            logger.info(f"已保存{len(self.python_installations)}个Python安装信息")
            return True
        except Exception as e:
            logger.error(f"保存Python安装信息失败: {str(e)}")
            return False
    
    def _get_config_path(self):
        """获取配置文件路径"""
        # 获取用户主目录
        home_dir = os.path.expanduser("~")
        # 配置文件路径
        config_dir = os.path.join(home_dir, ".pyquick", "config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "python_installations.json")
    
    def _auto_detect_python(self):
        """自动检测系统中的Python安装"""
        try:
            # 根据不同操作系统使用不同的检测方法
            system = platform.system()
            if system == "Windows":
                self._detect_python_windows()
            elif system == "Darwin":  # macOS
                self._detect_python_macos()
            else:  # Linux和其他系统
                self._detect_python_linux()
                
            # 如果没有找到默认安装，将当前运行的Python设为默认
            if not self.default_installation and self.python_installations:
                self.python_installations[0]['is_default'] = True
                self.default_installation = self.python_installations[0]
                
            # 保存检测结果
            self._save_python_installations()
            
        except Exception as e:
            logger.error(f"自动检测Python安装失败: {str(e)}")
    
    def _detect_python_windows(self):
        """检测Windows系统上的Python安装"""
        try:
            # 使用where命令查找PATH中的Python
            try:
                where_result = subprocess.run(
                    ["where", "python"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if where_result.returncode == 0:
                    for path in where_result.stdout.splitlines():
                        path = path.strip()
                        if path and os.path.exists(path):
                            # 验证Python版本是否有效
                            version_result = subprocess.run(
                                [path, "--version"], 
                                capture_output=True, 
                                text=True, 
                                check=False
                            )
                            if version_result.returncode == 0:
                                self._add_python_installation(path)
            except Exception as e:
                logger.warning(f"使用where命令查找Python失败: {str(e)}")
                
            # 常见的Python安装位置
            python_paths = [
                r"C:\Python*",
                r"C:\Program Files\Python*",
                r"C:\Program Files (x86)\Python*",
                r"%LOCALAPPDATA%\Programs\Python\Python*",
                r"%APPDATA%\Local\Programs\Python\Python*",
                r"%USERPROFILE%\AppData\Local\Programs\Python\Python*",
                r"%USERPROFILE%\scoop\apps\python\current\python.exe",
                r"%USERPROFILE%\scoop\apps\python3\current\python.exe",
                r"%USERPROFILE%\miniconda3\python.exe",
                r"%USERPROFILE%\anaconda3\python.exe"
            ]
            
            # 将环境变量展开
            expanded_paths = []
            for path in python_paths:
                path = path.replace("%LOCALAPPDATA%", os.environ.get("LOCALAPPDATA", ""))
                path = path.replace("%APPDATA%", os.environ.get("APPDATA", ""))
                path = path.replace("%USERPROFILE%", os.environ.get("USERPROFILE", ""))
                if path:
                    expanded_paths.append(path)
            
            # 遍历每个可能的路径查找Python
            for path_pattern in expanded_paths:
                import glob
                for python_dir in glob.glob(path_pattern):
                    python_exe = os.path.join(python_dir, "python.exe")
                    if os.path.exists(python_exe):
                        self._add_python_installation(python_exe)
            
            # 查找当前PATH中的Python
            for path in os.environ.get("PATH", "").split(os.pathsep):
                python_exe = os.path.join(path, "python.exe")
                if os.path.exists(python_exe):
                    self._add_python_installation(python_exe)
                    
                # 也尝试python3.exe
                python3_exe = os.path.join(path, "python3.exe")
                if os.path.exists(python3_exe):
                    self._add_python_installation(python3_exe)
            
            # 查询注册表中的Python安装
            try:
                import winreg
                # 获取注册表路径配置
                registry_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python\PythonCore"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Python\PythonCore"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Python\PythonCore")
                ]
                
                # 如果提供了settings_manager，使用配置的注册表路径
                if self.settings_manager:
                    custom_paths = self.settings_manager.get("python_versions.windows_specific.registry_paths", [])
                    for path in custom_paths:
                        if path.startswith("HKEY_LOCAL_MACHINE\\"):
                            registry_paths.append((winreg.HKEY_LOCAL_MACHINE, path[18:]))
                        elif path.startswith("HKEY_CURRENT_USER\\"):
                            registry_paths.append((winreg.HKEY_CURRENT_USER, path[17:]))
                
                # 检查注册表路径
                for reg_key in registry_paths:
                    try:
                        with winreg.OpenKey(reg_key[0], reg_key[1]) as key:
                            for i in range(0, winreg.QueryInfoKey(key)[0]):
                                version_key_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, version_key_name + "\\InstallPath") as install_key:
                                    python_exe = os.path.join(winreg.QueryValue(install_key, ""), "python.exe")
                                    if os.path.exists(python_exe):
                                        self._add_python_installation(python_exe)
                    except WindowsError:
                        continue
            except ImportError:
                logger.warning("无法导入winreg模块，跳过注册表查询")
        
        except Exception as e:
            logger.error(f"检测Windows Python安装失败: {str(e)}")
    
    def _detect_python_macos(self):
        """检测macOS系统上的Python安装"""
        try:
            # 添加当前Python
            self._add_python_installation(sys.executable, is_default=True)
            
            # 查找常见的Python安装位置
            locations = [
                "/usr/bin/python3",
                "/usr/local/bin/python3",
                "/opt/homebrew/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python"
            ]
            
            for python_path in locations:
                if os.path.exists(python_path) and os.path.isfile(python_path):
                    # 验证Python版本是否有效
                    version_result = subprocess.run(
                        [python_path, "--version"], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    if version_result.returncode == 0:
                        self._add_python_installation(python_path)
            
            # 尝试使用which命令查找
            try:
                which_python3 = subprocess.run(
                    ["which", "python3"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if which_python3.returncode == 0 and which_python3.stdout.strip():
                    path = which_python3.stdout.strip()
                    # 验证Python版本是否有效
                    version_result = subprocess.run(
                        [path, "--version"], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    if version_result.returncode == 0:
                        self._add_python_installation(path)
            except:
                pass
            
            # 查找homebrew安装的Python版本
            try:
                brew_list = subprocess.run(
                    ["brew", "list", "--versions", "python"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if brew_list.returncode == 0 and "python" in brew_list.stdout:
                    for brew_path in ["/opt/homebrew/bin/python3", "/usr/local/bin/python3"]:
                        if os.path.exists(brew_path):
                            self._add_python_installation(brew_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"检测macOS Python安装失败: {str(e)}")
    
    def _detect_python_linux(self):
        """检测Linux系统上的Python安装"""
        try:
            # 添加当前Python
            self._add_python_installation(sys.executable, is_default=True)
            
            # 常见的Python可执行文件位置
            locations = [
                "/usr/bin/python3",
                "/usr/local/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python"
            ]
            
            for python_path in locations:
                if os.path.exists(python_path) and os.path.isfile(python_path):
                    self._add_python_installation(python_path)
            
            # 尝试使用which命令查找
            try:
                for cmd in ["python3", "python"]:
                    which_python = subprocess.run(
                        ["which", cmd], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    if which_python.returncode == 0 and which_python.stdout.strip():
                        self._add_python_installation(which_python.stdout.strip())
            except:
                pass
                
        except Exception as e:
            logger.error(f"检测Linux Python安装失败: {str(e)}")
    
    def _add_python_installation(self, python_path, is_default=False):
        """
        添加一个Python安装到列表中
        
        Args:
            python_path: Python可执行文件路径
            is_default: 是否设为默认安装
        """
        try:
            # 检查路径是否已存在
            for install in self.python_installations:
                if install["path"] == python_path:
                    # 如果要设为默认，更新标记
                    if is_default and not install.get('is_default', False):
                        # 先清除其他默认标记
                        for other in self.python_installations:
                            if other != install and other.get('is_default', False):
                                other['is_default'] = False
                        # 设置新的默认
                        install['is_default'] = True
                        self.default_installation = install
                    return False  # 已存在，不添加
            
            # 获取版本信息
            version_info = self._get_python_version(python_path)
            if not version_info:
                return False
            
            # 新的安装记录
            new_install = {
                "path": python_path,
                "version": version_info.get("version", "未知"),
                "is_default": is_default
            }
            
            # 如果要设为默认，先清除其他默认标记
            if is_default:
                for install in self.python_installations:
                    if install.get('is_default', False):
                        install['is_default'] = False
                self.default_installation = new_install
            
            # 添加到列表
            self.python_installations.append(new_install)
            logger.info(f"添加Python安装: {python_path}, 版本: {version_info.get('version', '未知')}")
            return True
            
        except Exception as e:
            logger.error(f"添加Python安装失败: {str(e)}")
            return False
    
    def _get_python_version(self, python_path):
        """
        获取指定Python路径的版本信息
        
        Args:
            python_path: Python可执行文件路径
            
        Returns:
            包含版本信息的字典，如果失败则返回None
        """
        try:
            # 运行Python获取版本信息
            version_cmd = [
                python_path, 
                "-c", 
                "import sys; import platform; print(f'{platform.python_version()}|{sys.executable}')"
            ]
            result = subprocess.run(
                version_cmd, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=3  # 3秒超时
            )
            
            if result.returncode == 0 and "|" in result.stdout:
                parts = result.stdout.strip().split("|")
                if len(parts) >= 2:
                    return {
                        "version": parts[0],
                        "path": parts[1]
                    }
            
            # 如果上面的方法失败，尝试另一种简单的方式
            version_simple = subprocess.run(
                [python_path, "--version"], 
                capture_output=True, 
                text=True,
                check=False,
                timeout=3
            )
            
            if version_simple.returncode == 0:
                # 通常输出形式为 "Python X.Y.Z"
                version_text = version_simple.stdout or version_simple.stderr
                if "Python" in version_text:
                    version = version_text.split("Python")[1].strip()
                    return {
                        "version": version,
                        "path": python_path
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取Python版本信息失败: {str(e)}")
            return None
    
    def get_default_python(self):
        """
        获取默认Python安装
        
        Returns:
            默认Python安装信息，如果没有则返回None
        """
        return self.default_installation
    
    def set_default_python(self, python_path):
        """
        设置默认Python安装
        
        Args:
            python_path: 要设为默认的Python路径
            
        Returns:
            是否成功设置默认Python
        """
        try:
            # 查找Python安装
            for install in self.python_installations:
                if install["path"] == python_path:
                    # 先清除其他默认标记
                    for other in self.python_installations:
                        if other != install and other.get('is_default', False):
                            other['is_default'] = False
                    
                    # 设置新的默认
                    install['is_default'] = True
                    self.default_installation = install
                    
                    # 保存配置
                    self._save_python_installations()
                    
                    # 通知pip管理器更新显示
                    try:
                        from pipx.pip_manager import PipManager
                        if hasattr(self, 'pip_manager'):
                            self.pip_manager._update_python_environment_info()
                    except ImportError:
                        pass
                    
                    # 更新系统Python信息显示
                    if self.settings_manager:
                        self.settings_manager.set("python_versions.default_version", python_path)
                        self.settings_manager.save_settings()
                    
                    return True
            
            # 如果未找到指定的安装，则返回失败
            logger.warning(f"未找到Python安装: {python_path}")
            return False
            
        except Exception as e:
            logger.error(f"设置默认Python失败: {str(e)}")
            return False
    
    def get_all_installations(self):
        """
        获取所有Python安装
        
        Returns:
            Python安装列表
        """
        return self.python_installations
    
    def add_python_installation(self, python_path, is_default=False):
        """
        添加Python安装
        
        Args:
            python_path: Python可执行文件路径
            is_default: 是否设为默认安装
            
        Returns:
            是否成功添加
        """
        result = self._add_python_installation(python_path, is_default)
        if result:
            self._save_python_installations()
        return result
    
    def remove_python_installation(self, python_path):
        """
        移除Python安装
        
        Args:
            python_path: 要移除的Python路径
            
        Returns:
            是否成功移除
        """
        try:
            # 查找安装
            for i, install in enumerate(self.python_installations):
                if install["path"] == python_path:
                    # 如果是默认安装，需要重新选择默认
                    is_default = install.get('is_default', False)
                    
                    # 移除安装
                    self.python_installations.pop(i)
                    
                    # 如果移除的是默认安装，并且还有其他安装，选择第一个作为默认
                    if is_default and self.python_installations:
                        self.python_installations[0]['is_default'] = True
                        self.default_installation = self.python_installations[0]
                    elif not self.python_installations:
                        self.default_installation = None
                    
                    # 保存配置
                    self._save_python_installations()
                    return True
            
            # 未找到指定安装
            logger.warning(f"未找到Python安装: {python_path}")
            return False
            
        except Exception as e:
            logger.error(f"移除Python安装失败: {str(e)}")
            return False