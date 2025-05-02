from get_system_build import system_build
import platform
import os

def is_windows11():
    """
    检查当前系统是否为Windows 11
    
    Windows 11的build版本号为22000及以上
    
    Returns:
        bool: 如果是Windows 11则返回True，否则返回False
    """
    try:
        if system_build.get_system_name() != 'Windows':
            return False
            
        # 获取Windows版本信息
        win_version = platform.version()
        
        # 解析build版本号
        # 格式通常为：major.minor.build，例如：10.0.22000
        version_parts = win_version.split('.')
        if len(version_parts) >= 3:
            build_number = int(version_parts[2])
            return build_number >= 22000
        
        return False
    except Exception as e:
        # 出错时返回False
        return False

def block_start():
    """
    检查当前系统是否支持运行程序
    
    Returns:
        bool: True表示支持运行，False表示不支持
    """
    system = system_build.get_system_name()
    
    # Windows 系统支持
    if system == 'Windows':
        # Windows 7 及以上版本支持
        try:
            win_version = int(platform.version().split('.')[0])
            return win_version >= 6  # Windows 7 及以上
        except:
            # 解析版本失败时默认允许运行
            return True
    
    # macOS 系统要求 10.13 (Darwin 17) 及以上
    elif system == 'Darwin':
        try:
            darwin_version = int(system_build.get_system_release_build_version().split('.')[0])
            return darwin_version >= 17
        except:
            return False
    
    # Linux 系统支持
    elif system == 'Linux':
        return True
    
    # 其他系统默认不支持
    return False

def block_theme():
    """
    检查当前系统是否支持主题功能
    
    Returns:
        bool: True表示支持，False表示不支持
    """
    system = system_build.get_system_name()
    
    # Windows 10 及以上支持主题
    if system == 'Windows':
        try:
            win_version = int(platform.version().split('.')[0])
            return win_version >= 10
        except:
            return True
    
    # macOS 要求 Monterey (Darwin 21) 及以上
    elif system == 'Darwin':
        try:
            darwin_version = int(system_build.get_system_release_build_version().split('.')[0])
            return darwin_version >= 21
        except:
            return False
    
    # Linux 系统支持
    elif system == 'Linux':
        return True
    
    return False

def block_python2():
    """
    检查当前系统是否禁用Python2
    
    Returns:
        bool: True表示应禁用Python2，False表示应允许Python2
    """
    system = system_build.get_system_name()
    
    # Windows 系统不禁用Python2
    if system == 'Windows':
        return False
    
    # macOS 12 以上禁用Python2
    elif system == 'Darwin':
        try:
            darwin_version = int(system_build.get_system_release_build_version().split('.')[0])
            return darwin_version >= 21
        except:
            return False
    
    return False

def get_system_info():
    """
    获取当前系统信息
    
    Returns:
        dict: 包含系统信息的字典
    """
    system = system_build.get_system_name()
    
    info = {
        "system": system,
        "is_windows": system == "Windows",
        "is_macos": system == "Darwin",
        "is_linux": system == "Linux",
        "version": system_build.get_system_release_build_version(),
        "username": os.environ.get("USERNAME" if system == "Windows" else "USER", "unknown")
    }
    
    # 添加系统特定信息
    if system == "Windows":
        info["home_dir"] = os.environ.get("USERPROFILE", "C:\\Users\\{}".format(info["username"]))
        info["python_cmd_pattern"] = "python{}.exe"
        info["pip_cmd_pattern"] = "pip{}.exe"
    else:  # macOS/Linux
        info["home_dir"] = os.environ.get("HOME", "/Users/{}".format(info["username"]))
        info["python_cmd_pattern"] = "python{}"
        info["pip_cmd_pattern"] = "pip{}"
    
    return info