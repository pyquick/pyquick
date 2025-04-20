"""
pip_manager.py - Multi-version pip management module

Provides functionality to:
- Scan all pip versions installed on the system
- Get current pip version
- Switch between different pip versions
"""

import os
import re
import subprocess
import logging
from typing import List, Dict, Optional

# 获取日志记录器
logger = logging.getLogger("PyQuick")

def scan_pip_versions() -> List[Dict[str, str]]:
    """
    扫描系统中安装的所有pip版本
    
    返回:
        List[Dict]: 包含pip版本信息的字典列表，每个字典包含:
            - python_version: 关联的Python版本
            - pip_version: pip版本
            - pip_path: pip可执行文件路径
            - python_path: 关联的Python可执行文件路径
    """
    pip_versions = []
    
    try:
        # 使用where命令查找所有Python可执行文件
        result = subprocess.run(["where", "python"], capture_output=True, text=True, shell=True)
        python_paths = [p.strip() for p in result.stdout.split("\n") if p.strip()]
        
        # 去重并处理路径
        unique_paths = []
        seen = set()
        for path in python_paths:
            norm_path = os.path.normpath(path)
            if norm_path not in seen:
                seen.add(norm_path)
                unique_paths.append(norm_path)
        
        # 获取每个Python环境的pip信息
        for path in unique_paths:
            try:
                # 获取Python版本
                version_result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                version_output = version_result.stdout.strip()
                version_match = re.search(r"Python (\d+\.\d+\.\d+)", version_output)
                
                if version_match:
                    env_info = {
                        "python_path": path,
                        "python_version": version_match.group(1),
                        "pip_version": None,
                        "pip_path": None
                    }
                    
                    # 检查pip是否安装并获取版本
                    try:
                        pip_result = subprocess.run(
                            [path, "-m", "pip", "--version"],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if pip_result.returncode == 0:
                            pip_output = pip_result.stdout.strip()
                            pip_match = re.search(r"pip (\d+\.\d+\.\d+)", pip_output)
                            if pip_match:
                                env_info["pip_version"] = pip_match.group(1)
                                # 获取pip可执行文件路径
                                pip_path_result = subprocess.run(
                                    [path, "-m", "pip", "show", "pip"],
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                if pip_path_result.returncode == 0:
                                    for line in pip_path_result.stdout.split("\n"):
                                        if line.startswith("Location:"):
                                            pip_location = line.split(":")[1].strip()
                                            env_info["pip_path"] = os.path.join(pip_location, "pip.exe")
                                            break
                    
                    except Exception as e:
                        logger.warning(f"获取pip版本失败 {path}: {e}")
                    
                    if env_info["pip_version"]:
                        pip_versions.append(env_info)
                        
            except Exception as e:
                logger.error(f"获取Python版本失败 {path}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"扫描Python环境失败: {e}")
        
    return pip_versions

def get_current_pip_version() -> Optional[str]:
    """
    获取当前pip版本
    
    返回:
        str: 当前pip版本号，如果获取失败返回None
    """
    try:
        result = subprocess.run(
            ["pip", "--version"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            match = re.search(r"pip (\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except Exception as e:
        logger.error(f"获取当前pip版本失败: {e}")
    return None

def switch_pip_version(python_path: str) -> bool:
    """
    切换到指定Python环境的pip版本
    
    参数:
        python_path: Python可执行文件路径
        
    返回:
        bool: 是否切换成功
    """
    try:
        # 验证Python路径
        if not os.path.exists(python_path):
            logger.error(f"Python路径不存在: {python_path}")
            return False
            
        # 获取pip信息
        pip_result = subprocess.run(
            [python_path, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if pip_result.returncode != 0:
            logger.error(f"指定的Python环境没有安装pip: {python_path}")
            return False
            
        # 更新系统PATH环境变量，将目标pip路径放在前面
        pip_dir = os.path.dirname(python_path)
        if pip_dir not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] = pip_dir + os.pathsep + os.environ["PATH"]
            
        return True
    except Exception as e:
        logger.error(f"切换pip版本失败: {e}")
        return False
