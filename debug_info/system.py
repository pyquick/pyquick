import platform
import psutil
from memory_profiler import memory_usage
from get_system_build.system_build import get_system_release_build_version, get_mac_machine

def get_system_info():
    """
    获取完整的系统硬件信息
    返回格式化的字典数据
    """
    return {
        "系统类型": platform.system(),
        "处理器架构": platform.machine(),
        "Mac芯片类型": get_mac_machine(),
        "物理核心数": psutil.cpu_count(logical=False),
        "逻辑核心数": psutil.cpu_count(),
        "内存总量": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        "磁盘使用": {d.mount_point: f"{d.percent}%" for d in psutil.disk_partitions() if d.fstype}
    }

def get_memory_usage():
    """
    获取当前进程内存使用情况
    返回格式化的字符串
    """
    mem_usage = memory_usage(-1, interval=0.2, timeout=1)
    return f"{max(mem_usage) if mem_usage else 0:.2f} MB"