import subprocess
import re
import logging
from typing import Tuple, Optional
import requests
from packaging import version

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_pip_version() -> str:
    """获取当前pip版本"""
    try:
        output = subprocess.check_output(['pip3', '--version'], 
                                      stderr=subprocess.STDOUT,
                                      text=True)
        version_match = re.search(r'pip (\d+\.\d+(?:\.\d+)?)', output)
        if version_match:
            return version_match.group(1)
        return "Unknown"
    except subprocess.CalledProcessError as e:
        logger.error(f"获取pip版本失败: {str(e)}")
        return "Unknown"

def get_latest_pip_version() -> str:
    """获取最新pip版本"""
    try:
        response = requests.get('https://pypi.org/pypi/pip/json', timeout=10)
        response.raise_for_status()
        return response.json()['info']['version']
    except Exception as e:
        logger.error(f"获取最新pip版本失败: {str(e)}")
        return "Unknown"

def needs_upgrade() -> Tuple[bool, str, str]:
    """检查是否需要升级pip
    
    Returns:
        (需要升级, 当前版本, 最新版本)
    """
    current = get_current_pip_version()
    latest = get_latest_pip_version()
    
    if current == "Unknown" or latest == "Unknown":
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
        # 检查是否需要升级
        need_upgrade, current_ver, latest_ver = needs_upgrade()
        if not need_upgrade:
            logger.info("pip已经是最新版本")
            return True
            
        logger.info(f"正在将pip从{current_ver}升级到{latest_ver}")
        
        # 构建升级命令
        cmd = [
            'pip3', 'install', '--upgrade', 'pip',
            '--disable-pip-version-check',  # 禁用版本检查以加快速度
            '--no-cache-dir'  # 禁用缓存以确保获取最新版本
        ]
        
        # 执行升级
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
            if output and show_output:
                logger.info(output.strip())
                
        # 等待进程完成并获取返回码
        return_code = process.wait()
        
        if return_code != 0:
            error = process.stderr.read()
            logger.error(f"pip升级失败: {error}")
            return False
            
        # 验证升级后的版本
        new_version = get_current_pip_version()
        if new_version != "Unknown" and version.parse(new_version) >= version.parse(latest_ver):
            logger.info(f"pip已成功升级到版本 {new_version}")
            return True
        else:
            logger.error(f"pip升级后版本验证失败: {new_version} < {latest_ver}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"pip升级失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"pip升级过程中出现未知错误: {str(e)}")
        return False
