import subprocess
import sys
import re
import logging
import requests
from typing import Tuple, Optional, Dict, Any
from packaging import version
import platform

# 尝试获取日志记录器
try:
    from log import app_logger as logger
except ImportError:
    # 创建基本的日志记录器
    logger = logging.getLogger("pipx")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def verify_package_exists(package_name: str) -> Tuple[bool, Optional[str]]:
    """
    验证包是否存在于PyPI
    
    Args:
        package_name: 包名
        
    Returns:
        (是否存在, 最新版本号)
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return False, None
            
        response.raise_for_status()
        data = response.json()
        latest_version = data['info']['version']
        return True, latest_version
        
    except requests.RequestException as e:
        logger.error(f"验证包{package_name}失败: {str(e)}")
        return False, None

def get_installed_version(package_name: str) -> Optional[str]:
    """
    获取已安装的包版本
    
    Args:
        package_name: 包名
        
    Returns:
        版本号，如果未安装返回None
    """
    try:
        output = subprocess.check_output(
            [sys.executable, '-m', 'pip', 'show', package_name],
            stderr=subprocess.STDOUT,
            text=True
        )
        version_match = re.search(r'Version: ([\d\.]+)', output)
        return version_match.group(1) if version_match else None
    except subprocess.CalledProcessError:
        return None

def check_dependencies(package_name: str) -> Dict[str, Any]:
    """
    检查包的依赖关系
    
    Args:
        package_name: 包名
        
    Returns:
        依赖信息字典
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        requires_dist = data['info'].get('requires_dist', [])
        
        dependencies = {
            'runtime': [],
            'optional': [],
            'python_version': data['info'].get('requires_python', '')
        }
        
        if requires_dist:
            for dep in requires_dist:
                # 解析依赖字符串
                if ';' in dep:  # 有条件的依赖
                    req, cond = dep.split(';', 1)
                    if 'extra ==' in cond:  # 可选依赖
                        dependencies['optional'].append(req.strip())
                    else:
                        dependencies['runtime'].append(req.strip())
                else:  # 无条件的依赖
                    dependencies['runtime'].append(dep.strip())
                    
        return dependencies
    except Exception as e:
        logger.error(f"获取{package_name}依赖失败: {str(e)}")
        return {'runtime': [], 'optional': [], 'python_version': ''}

def install_package(package_name, version=None, upgrade=False, show_output=True):
    """
    安装Python包
    
    Args:
        package_name: 包名称
        version: 特定版本，如果不指定则安装最新版本
        upgrade: 是否升级现有包
        show_output: 是否实时显示输出
        
    Returns:
        bool: 安装是否成功
    """
    try:
        if not package_name:
            logger.error("未指定包名称")
            return False
            
        package_spec = package_name
        if version:
            package_spec = f"{package_name}=={version}"
        logger.info(f"开始安装包: {package_spec}")
        # 根据系统选择合适的命令
        if platform.system() == "Windows":
            base_cmd = ["py", "-3", "-m", "pip"]
        else:
            base_cmd = ["pip3"]
        # 构建安装命令
        cmd = base_cmd + ["install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package_spec)
        # 执行安装命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 获取结果
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logger.info(f"包 {package_name} 安装成功")
            return True
        else:
            logger.error(f"包 {package_name} 安装失败: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"安装包 {package_name} 时出错: {str(e)}")
        return False

def uninstall_package(package_name, show_output=True):
    """
    卸载Python包
    
    Args:
        package_name: 包名称
        show_output: 是否实时显示输出
        
    Returns:
        bool: 卸载是否成功
    """
    try:
        if not package_name:
            logger.error("未指定包名称")
            return False
        
        logger.info(f"开始卸载包: {package_name}")
        
        # 根据系统选择合适的命令
        if platform.system() == "Windows":
            base_cmd = ["py", "-3", "-m", "pip"]
        else:
            base_cmd = ["pip3"]
            
        # 构建卸载命令
        cmd = base_cmd + ["uninstall", "-y", package_name]
        
        # 执行卸载命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 获取结果
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"包 {package_name} 卸载成功")
            return True
        else:
            logger.error(f"包 {package_name} 卸载失败: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"卸载包 {package_name} 时出错: {str(e)}")
        return False
