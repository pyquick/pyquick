import subprocess
import sys
import re
import logging
import requests
from typing import Tuple, Optional, Dict, Any
from packaging import version

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def install_package(package_name: str, upgrade: bool = False) -> bool:
    """
    安装或升级Python包
    
    Args:
        package_name: 包名
        upgrade: 是否升级已安装的包
        
    Returns:
        是否安装成功
    """
    if not package_name:
        logger.error("包名不能为空")
        return False
        
    try:
        # 验证包是否存在
        exists, latest_version = verify_package_exists(package_name)
        if not exists:
            logger.error(f"包 {package_name} 在PyPI上不存在")
            return False
            
        # 检查已安装版本
        current_version = get_installed_version(package_name)
        if current_version and not upgrade:
            logger.info(f"包 {package_name} ({current_version}) 已安装")
            return True
            
        # 检查依赖
        deps = check_dependencies(package_name)
        if deps['python_version']:
            logger.info(f"包 {package_name} 需要 Python {deps['python_version']}")
            
        if deps['runtime']:
            logger.info(f"包 {package_name} 的运行时依赖: {', '.join(deps['runtime'])}")
            
        # 构建安装命令
        cmd = [sys.executable, '-m', 'pip', 'install']
        if upgrade:
            cmd.append('--upgrade')
        cmd.extend([
            package_name,
            '--disable-pip-version-check',
            '--no-cache-dir'
        ])
        
        # 执行安装
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 实时获取输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())
                
        return_code = process.wait()
        
        if return_code != 0:
            error = process.stderr.read()
            logger.error(f"安装失败: {error}")
            return False
            
        # 验证安装
        new_version = get_installed_version(package_name)
        if new_version:
            logger.info(f"包 {package_name} ({new_version}) 安装成功")
            return True
        else:
            logger.error(f"包 {package_name} 安装后验证失败")
            return False
            
    except Exception as e:
        logger.error(f"安装包 {package_name} 时出错: {str(e)}")
        return False

def uninstall_package(package_name: str) -> bool:
    """
    卸载Python包
    
    Args:
        package_name: 包名
        
    Returns:
        是否卸载成功
    """
    if not package_name:
        logger.error("包名不能为空")
        return False
        
    try:
        # 检查包是否已安装
        current_version = get_installed_version(package_name)
        if not current_version:
            logger.info(f"包 {package_name} 未安装")
            return True
            
        # 构建卸载命令
        cmd = [
            sys.executable, '-m', 'pip', 'uninstall',
            package_name,
            '-y',  # 自动确认
            '--disable-pip-version-check'
        ]
        
        # 执行卸载
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 实时获取输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())
                
        return_code = process.wait()
        
        if return_code != 0:
            error = process.stderr.read()
            logger.error(f"卸载失败: {error}")
            return False
            
        # 验证卸载
        if get_installed_version(package_name) is None:
            logger.info(f"包 {package_name} 已成功卸载")
            return True
        else:
            logger.error(f"包 {package_name} 卸载后仍然存在")
            return False
            
    except Exception as e:
        logger.error(f"卸载包 {package_name} 时出错: {str(e)}")
        return False
