import platform
import psutil
from memory_profiler import memory_usage
from get_system_build.system_build import get_system_release_build_version, get_mac_machine

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
    
    # 获取磁盘信息
    disk_info = {}
    for d in psutil.disk_partitions():
        if d.fstype:
            usage = psutil.disk_usage(d.mountpoint)
            disk_info[d.mountpoint] = {
                "总空间": f"{usage.total / (1024**3):.1f}GB",
                "已用": f"{usage.used / (1024**3):.1f}GB",
                "可用": f"{usage.free / (1024**3):.1f}GB",
                "使用率": f"{usage.percent}%"
            }
    
    return {
        "系统类型": platform.system(),
        "处理器架构": platform.machine(),
        "Mac芯片类型": get_mac_machine(),
        "物理核心数": psutil.cpu_count(logical=False),
        "逻辑核心数": psutil.cpu_count(),
        "内存信息": {
            "总量": f"{total_gb:.1f}GB",
            "已用": f"{used_gb:.1f}GB",
            "可用": f"{free_gb:.1f}GB",
            "使用率": f"{mem.percent}%"
        },
        "磁盘使用": disk_info,
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