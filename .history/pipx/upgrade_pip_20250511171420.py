import subprocess
import re
import logging
from typing import Tuple, Optional
import requests
from packaging import version
import sys
import platform
from settings.save import SettingsManager
from save_path import create_folder
from typing import Dict, Any, Optional, List, Tuple, Union
version="1965"
config_path=create_folder.get_path("pyquick",version)
manage=SettingsManager(config_path)
settings_all=manage.load_settings()
path_python=str(manage.get_setting("python_versions.installations.path")).strip('" ')
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_pip_version() -> str:
    """获取当前pip版本"""
    try:
        # 根据系统选择合适的命令
        if platform.system() == "Windows":
            cmd = [pa, "-3", "-m", "pip", "--version"]
        else:
            cmd = ["pip3", "--version"]#macOS
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        if "pip" in output:
            version = output.split()[1]
            return version
    except Exception as e:
        logger.error(f"获取pip版本失败: {e}")
    return ""

def get_latest_pip_version() -> str:
    """获取最新pip版本"""
    try:
        # 根据系统选择合适的命令
        if platform.system() == "Windows":
            cmd = ["py", "-3", "-m", "pip", "install", "--upgrade", "pip", "--dry-run"]
        else:
            cmd = ["pip3", "install", "--upgrade", "pip", "--dry-run"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        if "pip" in output:
            # 解析输出获取最新版本
            # 由于输出格式可能因pip版本而异，可能需要更复杂的解析
            return output.split("pip-")[1].split(" ")[0] if "pip-" in output else ""
    except Exception as e:
        logger.error(f"获取最新pip版本失败: {e}")
    return ""

def needs_upgrade() -> Tuple[bool, str, str]:
    """检查是否需要升级pip
    Returns:
        (需要升级, 当前版本, 最新版本)
    """
    current = get_current_pip_version()
    latest = get_latest_pip_version()
    if current == "" or latest == "":
        return False, current, latest
    try:
        return version.parse(current) < version.parse(latest), current, latest
    except version.InvalidVersion:
        return False, current, latest

def upgrade_pip(show_output: bool = False) -> bool:
    """升级pip到最新版本
    
    Args:
        show_output: 是否显示升级过程的输出
        
    Returns:
        是否升级成功
    """
    try:
        print("正在升级pip...")
        
        # 根据系统选择合适的命令
        if platform.system() == "Windows":
            cmd = ["py", "-3", "-m", "pip", "install", "--upgrade", "pip"]
        else:
            cmd = ["pip3", "install", "--upgrade", "pip"]
            
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print("pip升级成功!")
            return True
        else:
            print(f"pip升级失败: {stderr}")
        return False
    except Exception as e:
        print(f"pip升级过程中出错: {e}")
        return False
