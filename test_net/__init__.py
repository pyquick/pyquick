"""
网络测试模块

提供网络测试功能，用于测试镜像站点的连接质量和响应速度。
包含ping测试、URL测试等基本功能，以及专门针对Python和pip镜像的测试UI界面。
"""

from .base import NetworkTester
from typing import Dict, List, Optional

# 创建一个NetworkTester实例
network_tester = NetworkTester()

# 预定义Python镜像站点
PYTHON_MIRRORS = [
    {"name": "官方源", "url": "https://www.python.org/ftp/python/"},
    {"name": "淘宝镜像", "url": "https://npm.taobao.org/mirrors/python/"},
    {"name": "华为镜像", "url": "https://mirrors.huaweicloud.com/python/"},
    {"name": "腾讯镜像", "url": "https://mirrors.cloud.tencent.com/python/"},
    {"name": "阿里云", "url": "https://mirrors.aliyun.com/python/"}
]

# 预定义pip镜像站点
PIP_MIRRORS = [
    {"name": "官方源", "url": "https://pypi.org/simple/"},
    {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple/"},
    {"name": "清华大学", "url": "https://pypi.tuna.tsinghua.edu.cn/simple/"},
    {"name": "中国科技大学", "url": "https://pypi.mirrors.ustc.edu.cn/simple/"},
    {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple/"},
    {"name": "豆瓣", "url": "https://pypi.doubanio.com/simple/"}
]

def test_python_mirrors(callback=None) -> Dict[str, Dict]:
    """
    测试Python镜像站点
    
    Args:
        callback: 每个站点测试完成后的回调函数
        
    Returns:
        测试结果字典
    """
    return network_tester.test_mirrors(PYTHON_MIRRORS, callback)

def test_pip_mirrors(callback=None) -> Dict[str, Dict]:
    """
    测试Pip镜像站点
    
    Args:
        callback: 每个站点测试完成后的回调函数
        
    Returns:
        测试结果字典
    """
    return network_tester.test_mirrors(PIP_MIRRORS, callback)

def get_best_python_mirror() -> Optional[Dict]:
    """
    获取最佳Python镜像站点
    
    Returns:
        最佳镜像站点信息，如果没有可用镜像则返回None
    """
    results = test_python_mirrors()
    best_mirror = None
    best_score = -1
    
    for name, result in results.items():
        score = result['overall']['score']
        if score > best_score and result['overall']['success']:
            best_score = score
            best_mirror = next((m for m in PYTHON_MIRRORS if m['name'] == name), None)
    
    return best_mirror

def get_best_pip_mirror() -> Optional[Dict]:
    """
    获取最佳Pip镜像站点
    
    Returns:
        最佳镜像站点信息，如果没有可用镜像则返回None
    """
    results = test_pip_mirrors()
    best_mirror = None
    best_score = -1
    
    for name, result in results.items():
        score = result['overall']['score']
        if score > best_score and result['overall']['success']:
            best_score = score
            best_mirror = next((m for m in PIP_MIRRORS if m['name'] == name), None)
    
    return best_mirror

__all__ = [
    'network_tester',
    'NetworkTester',
    'PYTHON_MIRRORS',
    'PIP_MIRRORS',
    'test_python_mirrors',
    'test_pip_mirrors',
    'get_best_python_mirror',
    'get_best_pip_mirror'
] 