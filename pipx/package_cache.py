"""
PIP包缓存管理模块
定期扫描pip包信息并缓存到指定路径
"""
import json
import os
import subprocess
import sys
import re
from typing import Dict, List, Optional
import logging
from packaging import version

# 配置日志
logger = logging.getLogger(__name__)


def get_pip_packages() -> List[Dict[str, str]]:
    """
    获取所有已安装的pip包信息
    
    Returns:
        包含包信息的字典列表
    """
    try:
        # 使用pip list命令获取已安装包列表
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        packages = json.loads(result.stdout)
        
        # 为每个包添加是否需要升级的信息
        for pkg in packages:
            latest_version = get_latest_version(pkg['name'])
            if latest_version:
                pkg['latest_version'] = latest_version
                pkg['need_upgrade'] = version.parse(pkg['version']) < version.parse(latest_version)
            else:
                pkg['latest_version'] = None
                pkg['need_upgrade'] = False
        
        return packages
    except subprocess.CalledProcessError as e:
        logger.error(f"获取pip包列表失败: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"处理pip包列表时出错: {str(e)}")
        return []


def get_latest_version(package_name: str) -> Optional[str]:
    """
    获取包的最新版本
    
    Args:
        package_name: 包名
        
    Returns:
        最新版本号，如果获取失败返回None
    """
    try:
        # 使用PyPI API获取最新版本
        import requests
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        data = response.json()
        latest_version = data['info']['version']
        return latest_version
    except Exception as e:
        logger.error(f"获取包{package_name}最新版本失败: {str(e)}")
        return None


def save_package_cache(cache_path: str, packages: List[Dict[str, str]]) -> bool:
    """
    保存包信息到缓存文件
    
    Args:
        cache_path: 缓存文件路径
        packages: 包信息列表
        
    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(packages, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"保存包缓存失败: {str(e)}")
        return False


def load_package_cache(cache_path: str) -> Optional[List[Dict[str, str]]]:
    """
    从缓存文件加载包信息
    
    Args:
        cache_path: 缓存文件路径
        
    Returns:
        包信息列表，如果加载失败返回None
    """
    try:
        if not os.path.exists(cache_path):
            return None
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载包缓存失败: {str(e)}")
        return None


def should_scan_full() -> bool:
    """
    根据启动次数判断是否需要完整扫描
    
    Returns:
        是否需要完整扫描
    """
    try:
        # 获取启动次数
        launch_count = get_launch_count()
        
        # 每5次启动完整扫描一次
        return launch_count % 5 == 0
    except Exception as e:
        logger.error(f"判断是否需要完整扫描失败: {str(e)}")
        return True


def get_launch_count() -> int:
    """
    获取程序启动次数
    
    Returns:
        启动次数
    """
    # TODO: 实现启动次数记录功能
    return 0


def update_launch_count() -> None:
    """
    更新程序启动次数
    """
    # TODO: 实现启动次数更新功能
    pass


def get_package_info(cache_path: str) -> List[Dict[str, str]]:
    """
    获取包信息，优先从缓存读取，必要时进行完整扫描
    
    Args:
        cache_path: 缓存文件路径
        
    Returns:
        包信息列表
    """
    update_launch_count()
    
    if should_scan_full():
        logger.info("执行完整pip包扫描")
        packages = get_pip_packages()
        save_package_cache(cache_path, packages)
        return packages
    else:
        logger.info("从缓存读取pip包信息")
        packages = load_package_cache(cache_path)
        if packages is None:
            packages = get_pip_packages()
            save_package_cache(cache_path, packages)
        return packages