"""
PIP管理模块，提供包安装、卸载和升级功能
"""

from .upgrade_pip import (
    get_current_pip_version,
    get_latest_pip_version,
    needs_upgrade,
    upgrade_pip
)

from .install_unsi import (
    install_package,
    uninstall_package,
    verify_package_exists,
    get_installed_version,
    check_dependencies
)

# 版本信息
__version__ = '1965' 