"""
PyQuick pip管理模块

提供pip包的版本检查、安装、卸载和升级功能
"""
import os
import sys
import logging
import threading
import importlib

# 获取日志记录器
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger

logger = get_logger()

# 导入所需模块
try:
    from pip.check_ver import show_pip_version, retry_pip, get_pip_version, get_latest_pip_version
    from pip.upgrade import upgrade_pip
    from pip.install_uninstall import install_package, uninstall_package
    from pip.upgrade_package import upgrade_package, monitor_package_version, check_package_upgradeable
    
    logger.info("成功导入pip管理模块")
except ImportError as e:
    logger.error(f"导入pip管理模块失败: {e}")
    
    # 定义降级版本的函数，以防导入失败
    def show_pip_version(*args, **kwargs):
        logger.error("无法使用pip版本检查功能")
        
    def retry_pip(*args, **kwargs):
        logger.error("无法使用pip重试功能")
        
    def upgrade_pip(*args, **kwargs):
        logger.error("无法使用pip升级功能")
        
    def install_package(*args, **kwargs):
        logger.error("无法使用包安装功能")
        
    def uninstall_package(*args, **kwargs):
        logger.error("无法使用包卸载功能")
        
    def upgrade_package(*args, **kwargs):
        logger.error("无法使用包升级功能")
        
    def monitor_package_version(*args, **kwargs):
        logger.error("无法使用包版本监控功能")
        
    def check_package_upgradeable(*args, **kwargs):
        logger.error("无法检查包是否可升级")
        return None

# 安全地重新加载模块
def reload_modules():
    """安全地重新加载所有pip管理模块"""
    try:
        # 获取当前模块
        this_module = sys.modules[__name__]
        
        # 重新加载子模块
        modules_to_reload = [
            'pip.check_ver',
            'pip.upgrade',
            'pip.install_uninstall',
            'pip.upgrade_package'
        ]
        
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    logger.info(f"重新加载模块 {module_name}")
                except Exception as e:
                    logger.error(f"重新加载模块 {module_name} 失败: {e}")
        
        # 重新导入函数
        from pip.check_ver import show_pip_version, retry_pip, get_pip_version, get_latest_pip_version
        from pip.upgrade import upgrade_pip
        from pip.install_uninstall import install_package, uninstall_package
        from pip.upgrade_package import upgrade_package, monitor_package_version, check_package_upgradeable
        
        # 更新当前模块中的函数
        this_module.show_pip_version = show_pip_version
        this_module.retry_pip = retry_pip
        this_module.get_pip_version = get_pip_version
        this_module.get_latest_pip_version = get_latest_pip_version
        this_module.upgrade_pip = upgrade_pip
        this_module.install_package = install_package
        this_module.uninstall_package = uninstall_package
        this_module.upgrade_package = upgrade_package
        this_module.monitor_package_version = monitor_package_version
        this_module.check_package_upgradeable = check_package_upgradeable
        
        logger.info("成功重新加载pip管理模块")
        return True
    except Exception as e:
        logger.error(f"重新加载pip管理模块失败: {e}")
        return False

# 导出的函数
__all__ = [
    'show_pip_version',
    'retry_pip',
    'upgrade_pip',
    'install_package',
    'uninstall_package',
    'upgrade_package',
    'monitor_package_version',
    'check_package_upgradeable',
    'get_pip_version',
    'get_latest_pip_version',
    'reload_modules'
] 