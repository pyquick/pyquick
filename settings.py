"""
PyQuick Settings Module

提供设置的全局管理、加载和保存功能
"""
import os
import json
import logging
import shutil
import platform
import subprocess
import re
import sys
from typing import Dict, List, Any, Optional, Tuple, Union

# 获取日志记录器
logger = logging.getLogger("PyQuick")

# 默认设置
DEFAULT_SETTINGS = {
    "language": "zh_CN",
    "theme": "light",
    "python_mirror": "default",
    "pip_mirror": "default",
    "max_log_size": 10,
    "log_size_unit": "MB",
    "allow_multithreading": True,
    "check_pip_update": True,
    "custom_python_mirrors": [],
    "custom_pip_mirrors": []
}

# 默认Python镜像源
DEFAULT_PYTHON_MIRRORS = [
    "https://www.python.org/ftp/python",
    "https://mirrors.huaweicloud.com/python",
    "https://mirrors.tuna.tsinghua.edu.cn/python",
    "https://mirrors.aliyun.com/python"
]

# 默认pip镜像源
DEFAULT_PIP_MIRRORS = [
    "https://pypi.org/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.mirrors.ustc.edu.cn/simple",
    "https://mirrors.cloud.tencent.com/pypi/simple/"
]

# 获取应用数据目录
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", ""), "pyquick")
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
SETTINGS_BACKUP_FILE = os.path.join(APP_DATA_DIR, "settings.backup.json")
SETTINGS_CHANGES_FILE = os.path.join(APP_DATA_DIR, "settings_changes.json")

# 确保应用数据目录存在
os.makedirs(APP_DATA_DIR, exist_ok=True)

# 全局设置对象
settings = {}

# Python环境扫描结果
python_environments = []

# 环境配置存储
environment_configs = {}

def get_environment_config(env_name):
    """获取指定环境的配置"""
    return environment_configs.setdefault(env_name, {
        'python_path': '',
        'pip_version': '',
        'packages': []
    })

def set_environment_pip_version(env_name, pip_version):
    """设置环境的pip版本"""
    env_config = get_environment_config(env_name)
    
    # 初始化pip_versions列表
    if 'pip_versions' not in env_config:
        env_config['pip_versions'] = []
    
    # 添加新版本到列表（如果不存在）
    if pip_version not in env_config['pip_versions']:
        env_config['pip_versions'].append(pip_version)
    
    # 设置当前使用的pip版本
    env_config['current_pip_version'] = pip_version
    
    # 保存到全局设置
    settings.setdefault('environments', {})[env_name] = env_config
    save_settings(settings.get('config_path', ''))

def get_environment_pip_versions(env_name):
    """获取环境的所有pip版本"""
    env_config = get_environment_config(env_name)
    return env_config.get('pip_versions', [])

def get_current_pip_version(env_name):
    """获取环境当前使用的pip版本"""
    env_config = get_environment_config(env_name)
    return env_config.get('current_pip_version', 
                        env_config.get('pip_version', None))  # 向后兼容

def set_current_pip_version(env_name, pip_version):
    """设置环境当前使用的pip版本"""
    env_config = get_environment_config(env_name)
    if 'pip_versions' in env_config and pip_version in env_config['pip_versions']:
        env_config['current_pip_version'] = pip_version
        settings.setdefault('environments', {})[env_name] = env_config
        save_settings(settings.get('config_path', ''))

def init_settings(config_path: str) -> None:
    """
    初始化设置，创建必要的配置文件和目录
    
    参数:
        config_path: 配置文件路径
    """
    global settings
    
    # 确保配置目录存在
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    
    # 如果设置文件不存在，创建默认设置
    if not os.path.exists(SETTINGS_FILE):
        settings = DEFAULT_SETTINGS.copy()
        save_settings(config_path)
    else:
        load_settings(config_path)
    
    # 确保旧配置文件的兼容性
    ensure_compatibility(config_path)

def load_settings(config_path: str = None) -> Dict[str, Any]:
    """
    从配置文件加载设置
    
    参数:
        config_path: 配置文件路径（可选，保留参数以保持兼容性）
        
    返回:
        Dict: 加载的设置
    """
    global settings
    
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                
                # 确保所有默认设置都存在
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                
                settings = loaded_settings
                logger.info("成功加载设置")
        else:
            # 如果设置文件不存在，使用默认设置
            settings = DEFAULT_SETTINGS.copy()
            logger.info("使用默认设置")
            save_settings(config_path)
            
    except Exception as e:
        logger.error(f"加载设置失败: {str(e)}")
        # 如果主设置文件损坏，尝试从备份恢复
        if os.path.exists(SETTINGS_BACKUP_FILE):
            try:
                with open(SETTINGS_BACKUP_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info("已从备份恢复设置")
            except Exception as backup_e:
                logger.error(f"从备份恢复设置失败: {str(backup_e)}")
                settings = DEFAULT_SETTINGS.copy()
        else:
            settings = DEFAULT_SETTINGS.copy()
        
    return settings

def save_settings(config_path: str) -> bool:
    """
    保存所有设置到配置文件
    
    参数:
        config_path: 配置文件路径（保留参数以保持兼容性）
        
    返回:
        bool: 保存是否成功
    """
    global settings
    
    try:
        # 如果已存在设置文件，先创建备份
        if os.path.exists(SETTINGS_FILE):
            shutil.copy2(SETTINGS_FILE, SETTINGS_BACKUP_FILE)
        
        # 确保目录存在
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        
        # 保存所有设置到单一JSON文件
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        # 保存成功后清除变更记录
        clear_settings_changes()
        
        return True
        
    except Exception as e:
        logger.error(f"保存设置失败: {str(e)}")
        # 如果保存失败且存在备份，尝试恢复
        if os.path.exists(SETTINGS_BACKUP_FILE):
            try:
                shutil.copy2(SETTINGS_BACKUP_FILE, SETTINGS_FILE)
                logger.info("已恢复设置备份")
            except Exception as backup_e:
                logger.error(f"恢复设置备份失败: {str(backup_e)}")
        return False

def get_setting(key: str, default: Any = None) -> Any:
    """
    获取设置值
    
    参数:
        key: 设置键名
        default: 如果设置不存在，返回的默认值
        
    返回:
        Any: 设置值或默认值
    """
    global settings
    return settings.get(key, default)

def set_setting(key: str, value: Any) -> None:
    """
    设置一个设置值并记录变更
    
    参数:
        key: 设置键名
        value: 设置值
    """
    global settings
    if key in settings and settings[key] != value:
        # 记录设置变更
        record_setting_change(key, settings[key], value)
    settings[key] = value

def record_setting_change(key: str, old_value: Any, new_value: Any) -> None:
    """记录设置变更"""
    try:
        changes = []
        
        # 读取现有变更记录
        if os.path.exists(SETTINGS_CHANGES_FILE):
            try:
                with open(SETTINGS_CHANGES_FILE, 'r', encoding='utf-8') as f:
                    changes = json.load(f)
            except:
                changes = []
        
        # 添加新的变更记录
        changes.append({
            "key": key,
            "old_value": old_value,
            "new_value": new_value
        })
        
        # 保存变更记录
        with open(SETTINGS_CHANGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(changes, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"记录设置变更失败: {str(e)}")

def check_language_changed() -> bool:
    """检查语言设置是否有变更"""
    try:
        if os.path.exists(SETTINGS_CHANGES_FILE):
            with open(SETTINGS_CHANGES_FILE, 'r', encoding='utf-8') as f:
                changes = json.load(f)
                # 检查是否有语言变更
                for change in changes:
                    if change['key'] == 'language':
                        return True
        return False
    except Exception as e:
        logger.error(f"检查语言设置变更失败: {e}")
        return False

def clear_settings_changes() -> None:
    """清除设置变更记录"""
    try:
        if os.path.exists(SETTINGS_CHANGES_FILE):
            os.remove(SETTINGS_CHANGES_FILE)
    except Exception as e:
        logger.error(f"清除设置变更记录失败: {str(e)}")

def ensure_compatibility(config_path: str) -> None:
    """
    确保与旧配置文件的兼容性
    
    参数:
        config_path: 配置文件路径
    """
    # 处理旧的语言设置文件
    language_file = os.path.join(config_path, "language.txt")
    if os.path.exists(language_file):
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                lang = f.read().strip()
                if lang and lang in ["zh_CN", "en_US"]:
                    set_setting("language", lang)
        except Exception as e:
            logger.error(f"Failed to read language file: {e}")
    
    # 处理旧的主题设置文件
    theme_file = os.path.join(config_path, "theme.txt")
    if os.path.exists(theme_file):
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                theme = f.read().strip()
                if theme and theme in ["light", "dark"]:
                    set_setting("theme", theme)
        except Exception as e:
            logger.error(f"Failed to read theme file: {e}")
    
    # 处理旧的多线程设置文件
    thread_file = os.path.join(config_path, "allowthread.txt")
    if os.path.exists(thread_file):
        try:
            with open(thread_file, 'r', encoding='utf-8') as f:
                allow_thread = f.read().strip().lower() == "true"
                set_setting("allow_multithreading", allow_thread)
        except Exception as e:
            logger.error(f"Failed to read thread file: {e}")
    
    # 处理旧的日志大小设置文件
    log_size_file = os.path.join(config_path, "log_size.txt")
    if os.path.exists(log_size_file):
        try:
            with open(log_size_file, 'r', encoding='utf-8') as f:
                size_str = f.read().strip()
                if size_str and size_str.isdigit():
                    set_setting("max_log_size", int(size_str))
        except Exception as e:
            logger.error(f"Failed to read log size file: {e}")
    
    # 保存合并后的设置
    save_settings(config_path)

def scan_python_environments() -> List[Dict[str, Any]]:
    """
    扫描系统中安装的Python环境
    
    返回:
        List[Dict]: 包含Python环境信息的字典列表
    """
    global python_environments
    environments = []
    
    try:
        if platform.system() == "Windows":
            # 使用where命令查找所有Python安装
            result = subprocess.run(
                ["where", "python"], 
                capture_output=True, 
                text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                paths = result.stdout.strip().split('\n')
                python_pattern = re.compile(r'Python(\d+)')
                
                for path in paths:
                    path = path.strip()
                    if not path:
                        continue
                        
                    # 跳过包含以下字符串的路径
                    skip_dirs = [
                        "WindowsApps",
                        "AppData\\Local\\Microsoft",
                        "AppData\\Local\\Packages"
                    ]
                    if any(skip_dir in path for skip_dir in skip_dirs):
                        logger.debug(f"跳过系统目录: {path}")
                        continue
                    
                    # 提取Python版本信息
                    try:
                        # 获取Python版本
                        version_result = subprocess.run(
                            [path, "-V"], 
                            capture_output=True, 
                            text=True, 
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if version_result.returncode == 0:
                            version_str = version_result.stdout.strip()
                            version_match = re.search(r'Python (\d+\.\d+\.\d+)', version_str)
                            
                            if version_match:
                                version = version_match.group(1)
                                
                                # 获取实际的安装路径（上级目录）
                                real_install_path = os.path.dirname(os.path.dirname(path))
                                python_base_path = None
                                
                                # 查找包含 "Python" 的父目录
                                current_path = real_install_path
                                while current_path and os.path.splitdrive(current_path)[1]:
                                    dir_name = os.path.basename(current_path)
                                    if "Python" in dir_name:
                                        python_base_path = current_path
                                        break
                                    current_path = os.path.dirname(current_path)
                                
                                if not python_base_path:
                                    python_base_path = real_install_path
                                
                                # 检查pip是否安装
                                pip_installed = False
                                pip_version = None
                                
                                try:
                                    pip_result = subprocess.run(
                                        [path, "-m", "pip", "--version"], 
                                        capture_output=True, 
                                        text=True, 
                                        creationflags=subprocess.CREATE_NO_WINDOW
                                    )
                                    
                                    if pip_result.returncode == 0:
                                        pip_installed = True
                                        pip_match = re.search(r'pip (\d+\.\d+(\.\d+)?)', pip_result.stdout)
                                        if pip_match:
                                            pip_version = pip_match.group(1)
                                except:
                                    pass
                                
                                # 提取短版本号（如 Python39 -> 39）
                                short_version = None
                                path_parts = python_base_path.split(os.sep)
                                
                                for part in reversed(path_parts):
                                    match = python_pattern.search(part)
                                    if match:
                                        short_version = match.group(1)
                                        break
                                
                                # 将信息添加到环境列表
                                env_info = {
                                    "version": version,
                                    "short_version": short_version,
                                    "path": path,
                                    "install_path": python_base_path,
                                    "pip_installed": pip_installed,
                                    "pip_version": pip_version
                                }
                                
                                # 避免重复添加
                                if not any(e["path"] == path for e in environments):
                                    environments.append(env_info)
                    except Exception as e:
                        logger.error(f"处理Python路径失败 {path}: {e}")
        
        # 按版本排序（降序）
        environments.sort(key=lambda x: [int(p) for p in x["version"].split(".")], reverse=True)
        python_environments = environments
        
    except Exception as e:
        logger.error(f"扫描Python环境失败: {e}")
    
    return environments

def is_windows10_or_lower() -> bool:
    """
    检查系统是否是Windows 10或更低版本
    
    返回:
        bool: 是否是Windows 10或更低版本
    """
    if platform.system() != "Windows":
        return False
    
    try:
        build_number = int(platform.version().split(".")[-1])
        return build_number < 22000  # Windows 11的内部版本号从22000开始
    except:
        # 如果无法确定版本，假设是较新版本
        return False

def get_python_by_version(version: str) -> Optional[Dict[str, Any]]:
    """
    根据版本号获取Python环境信息
    
    参数:
        version: Python版本号（如"3.9.1"）
        
    返回:
        Dict 或 None: Python环境信息或None（如果未找到）
    """
    global python_environments
    
    for env in python_environments:
        if env["version"] == version:
            return env
    
    return None

def get_pip_mirrors() -> List[str]:
    """获取pip镜像源列表，包括自定义源"""
    mirrors = DEFAULT_PIP_MIRRORS.copy()
    
    try:
        # 读取自定义镜像源
        custom_mirrors_file = os.path.join(APP_DATA_DIR, "custom_pip_mirrors.txt")
        if os.path.exists(custom_mirrors_file):
            with open(custom_mirrors_file, 'r') as f:
                custom_mirrors = [line.strip() for line in f.readlines() if line.strip()]
                mirrors.extend(custom_mirrors)
    except Exception as e:
        logger.error(f"Error reading custom pip mirrors: {e}")
    
    return mirrors

def get_python_mirrors() -> List[str]:
    """获取Python下载镜像源列表，包括自定义源"""
    mirrors = DEFAULT_PYTHON_MIRRORS.copy()
    
    try:
        # 读取自定义镜像源
        custom_mirrors_file = os.path.join(APP_DATA_DIR, "custom_python_mirrors.txt")
        if os.path.exists(custom_mirrors_file):
            with open(custom_mirrors_file, 'r') as f:
                custom_mirrors = [line.strip() for line in f.readlines() if line.strip()]
                mirrors.extend(custom_mirrors)
    except Exception as e:
        logger.error(f"Error reading custom Python mirrors: {e}")
    
    return mirrors

def add_custom_mirror(mirror_type: str, url: str) -> bool:
    """
    添加自定义镜像
    
    参数:
        mirror_type: 镜像类型（"python"或"pip"）
        url: 镜像URL
        
    返回:
        bool: 添加是否成功
    """
    if mirror_type not in ["python", "pip"]:
        return False
    
    # 验证URL格式
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    
    # 确保URL末尾没有斜杠
    url = url.rstrip("/")
    
    setting_key = f"custom_{mirror_type}_mirrors"
    custom_mirrors = get_setting(setting_key, [])
    
    # 检查是否已存在
    if url in custom_mirrors:
        return False
    
    # 添加到列表
    custom_mirrors.append(url)
    set_setting(setting_key, custom_mirrors)
    
    # 保存到文件
    if mirror_type == "python":
        return save_custom_python_mirror(url)
    elif mirror_type == "pip":
        return save_custom_pip_mirror(url)
    return False

def save_custom_python_mirror(url: str) -> bool:
    """保存自定义Python镜像源"""
    try:
        custom_mirrors_file = os.path.join(APP_DATA_DIR, "custom_python_mirrors.txt")
        with open(custom_mirrors_file, 'a') as f:
            f.write(f"{url}\n")
        return True
    except Exception as e:
        logger.error(f"Error saving custom Python mirror: {e}")
        return False

def save_custom_pip_mirror(url: str) -> bool:
    """保存自定义pip镜像源"""
    try:
        custom_mirrors_file = os.path.join(APP_DATA_DIR, "custom_pip_mirrors.txt")
        with open(custom_mirrors_file, 'a') as f:
            f.write(f"{url}\n")
        return True
    except Exception as e:
        logger.error(f"Error saving custom pip mirror: {e}")
        return False

def remove_custom_mirror(mirror_type: str, url: str) -> bool:
    """
    移除自定义镜像
    
    参数:
        mirror_type: 镜像类型（"python"或"pip"）
        url: 镜像URL
        
    返回:
        bool: 移除是否成功
    """
    if mirror_type not in ["python", "pip"]:
        return False
    
    setting_key = f"custom_{mirror_type}_mirrors"
    custom_mirrors = get_setting(setting_key, [])
    
    # 检查是否存在
    if url not in custom_mirrors:
        return False
    
    # 从列表移除
    custom_mirrors.remove(url)
    set_setting(setting_key, custom_mirrors)
    
    return True

def get_active_mirror(mirror_type: str) -> str:
    """获取当前使用的镜像源
    
    Args:
        mirror_type: "python" 或 "pip"
        
    Returns:
        str: 当前使用的镜像源URL
    """
    try:
        config_file = os.path.join(APP_DATA_DIR, f"{mirror_type}mirror.txt")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                mirror = f.read().strip()
                if mirror:
                    return mirror
    except Exception as e:
        logger.error(f"Error reading active {mirror_type} mirror: {e}")
    
    # 返回默认源
    if mirror_type == "python":
        return DEFAULT_PYTHON_MIRRORS[0]
    else:
        return DEFAULT_PIP_MIRRORS[0]

def set_active_mirror(mirror_type: str, url: str) -> bool:
    """
    设置当前激活的镜像
    
    参数:
        mirror_type: 镜像类型（"python"或"pip"）
        url: 镜像URL或"default"（使用默认镜像）
        
    返回:
        bool: 设置是否成功
    """
    if mirror_type not in ["python", "pip"]:
        return False
    
    setting_key = f"{mirror_type}_mirror"
    set_setting(setting_key, url)
    
    # 如果是pip镜像，还需要配置pip.ini
    if mirror_type == "pip" and url != "default":
        try:
            pip_config_dir = os.path.join(APP_DATA_DIR, "pip")
            os.makedirs(pip_config_dir, exist_ok=True)
            
            pip_config_file = os.path.join(pip_config_dir, "pip.ini")
            
            with open(pip_config_file, "w", encoding="utf-8") as f:
                f.write("[global]\n")
                f.write(f"index-url = {url}\n")
                f.write("trusted-host = " + url.split("//")[1].split("/")[0] + "\n")
        except Exception as e:
            logger.error(f"Failed to configure pip.ini: {e}")
            return False
    
    return True