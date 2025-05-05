import platform
import psutil
import os
import threading
import time
from memory_profiler import memory_usage
from get_system_build.system_build import get_system_release_build_version, get_mac_machine
from get_system_build.block_features import is_windows11

# 全局缓存的磁盘信息
_disk_info = {}
_disk_info_lock = threading.Lock()
_last_update_time = 0
_update_interval = 5  # 更新磁盘信息的间隔（秒）

def preload_disk_info():
    """
    预加载磁盘信息
    """
    global _disk_info, _last_update_time
    
    with _disk_info_lock:
        # 获取磁盘信息
        disk_info = {}
        
        try:
            for d in psutil.disk_partitions(all=True):
                if d.fstype:
                    try:
                        usage = psutil.disk_usage(d.mountpoint)
                        # 特殊处理Windows盘符，保留冒号
                        if platform.system() == 'Windows' and d.mountpoint.endswith('\\'):
                            mountpoint = d.mountpoint.rstrip('\\')
                        else:
                            mountpoint = d.mountpoint
                            
                        disk_info[mountpoint] = {
                            "总空间": f"{usage.total / (1024**3):.1f}GB",
                            "已用": f"{usage.used / (1024**3):.1f}GB",
                            "可用": f"{usage.free / (1024**3):.1f}GB",
                            "使用率": f"{usage.percent}%",
                            "文件系统": d.fstype
                        }
                    except PermissionError:
                        # 一些磁盘可能不可访问，跳过
                        pass
                    except Exception as e:
                        # 其他错误，记录但不中断
                        print(f"获取磁盘信息错误 ({d.mountpoint}): {e}")
        except Exception as e:
            print(f"获取磁盘列表出错: {e}")
            
        _disk_info = disk_info
        _last_update_time = time.time()

def get_disk_info(force_update=False):
    """
    获取磁盘信息，使用缓存机制减少IO操作
    
    Args:
        force_update: 是否强制更新缓存
        
    Returns:
        dict: 磁盘信息字典
    """
    global _disk_info, _last_update_time
    
    current_time = time.time()
    
    # 如果强制更新或者超过更新间隔
    if force_update or not _disk_info or (current_time - _last_update_time) > _update_interval:
        preload_disk_info()
    
    return _disk_info

def get_system_info():
    """
    获取完整的系统硬件信息
    返回格式化的字典数据
    """
    # 获取内存信息
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024**3)
    used_gb = (mem.total - mem.available) / (1024**3)
    free_gb = mem.available / (1024**3)
    
    # 获取系统信息
    system_name = platform.system()
    
    # 检查是否为Windows 11
    is_win11 = False
    if system_name == 'Windows':
        is_win11 = is_windows11()
    
    return {
        "系统类型": system_name + (" 11" if is_win11 else ""),
        "系统版本": platform.version(),
        "处理器架构": platform.machine(),
        "Mac芯片类型": get_mac_machine() if system_name == "Darwin" else "N/A",
        "物理核心数": psutil.cpu_count(logical=False),
        "逻辑核心数": psutil.cpu_count(),
        "内存信息": {
            "总量": f"{total_gb:.1f}GB",
            "已用": f"{used_gb:.1f}GB",
            "可用": f"{free_gb:.1f}GB",
            "使用率": f"{mem.percent}%"
        },
        "磁盘使用": get_disk_info(),
        "CPU使用率": f"{psutil.cpu_percent()}%"
    }

def get_memory_usage():
    """
    获取当前进程内存使用情况
    返回格式化的字符串
    """
    process = psutil.Process()
    mem_info = process.memory_info()
    rss_mb = mem_info.rss / (1024 * 1024)  # RSS(实际物理内存)
    vms_mb = mem_info.vms / (1024 * 1024)  # VMS(虚拟内存)
    
    return {
        "物理内存": f"{rss_mb:.1f}MB",
        "虚拟内存": f"{vms_mb:.1f}MB",
        "内存占用率": f"{process.memory_percent():.1f}%"
    }