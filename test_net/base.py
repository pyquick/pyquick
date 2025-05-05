"""
网络测试基础模块

提供基础的网络连接测试功能，包括ping测试和HTTP连接测试。
"""

import platform
import subprocess
import re
import socket
import logging
import time
import threading
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Union, Tuple
import ssl

logger = logging.getLogger("test_net")

# 全局超时设置（秒）
DEFAULT_TIMEOUT = 5.0
DEFAULT_PING_COUNT = 4

def ping(host: str, count: int = DEFAULT_PING_COUNT, timeout: int = 2) -> Dict[str, Union[bool, float, List[float]]]:
    """
    对指定主机执行ping测试
    
    Args:
        host: 主机名或IP地址
        count: ping次数
        timeout: 超时时间(秒)
        
    Returns:
        包含ping测试结果的字典，格式为:
        {
            "success": bool,  # 是否成功
            "avg_time": float,  # 平均响应时间(毫秒)，失败时为-1
            "min_time": float,  # 最小响应时间(毫秒)，失败时为-1
            "max_time": float,  # 最大响应时间(毫秒)，失败时为-1
            "times": [float, ...],  # 各次ping的响应时间列表
            "packet_loss": float,  # 丢包率(0-1)
            "error": str  # 错误信息，成功时为空字符串
        }
    """
    result = {
        "success": False,
        "avg_time": -1.0,
        "min_time": -1.0,
        "max_time": -1.0,
        "times": [],
        "packet_loss": 1.0,
        "error": ""
    }
    
    # 移除URL协议前缀和路径
    host = re.sub(r'^https?://', '', host)
    host = host.split('/')[0]
    
    # 处理带端口的地址
    if ':' in host:
        host = host.split(':')[0]
    
    try:
        # 根据操作系统构建不同的ping命令
        system = platform.system().lower()
        
        if system == "windows":
            process = subprocess.Popen(
                ["ping", "-n", str(count), "-w", str(timeout * 1000), host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:  # Linux, Darwin (macOS)
            process = subprocess.Popen(
                ["ping", "-c", str(count), "-W", str(timeout), host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        stdout, stderr = process.communicate()
        
        # 检查stderr是否有错误信息
        if stderr:
            result["error"] = stderr.strip()
            return result
        
        # 检查进程退出码
        if process.returncode != 0:
            result["error"] = f"Ping失败，退出码: {process.returncode}"
            return result
        
        # 解析输出
        times = []
        
        # 匹配时间部分
        time_pattern = r"time=([0-9.]+)( ms)?"
        times = [float(match) for match in re.findall(time_pattern, stdout)]
        
        if not times:
            result["error"] = "无法解析ping结果"
            return result
        
        # 匹配丢包率
        loss_pattern = r"([0-9.]+)% packet loss"
        loss_match = re.search(loss_pattern, stdout)
        
        if loss_match:
            result["packet_loss"] = float(loss_match.group(1)) / 100.0
        
        # 计算统计数据
        result["times"] = times
        result["avg_time"] = sum(times) / len(times) if times else -1
        result["min_time"] = min(times) if times else -1
        result["max_time"] = max(times) if times else -1
        result["success"] = True
        
        return result
    
    except Exception as e:
        result["error"] = str(e)
        return result

def test_http_connection(url: str, timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Union[bool, float, str]]:
    """
    测试HTTP连接
    
    Args:
        url: 要测试的URL
        timeout: 超时时间(秒)
        
    Returns:
        包含测试结果的字典，格式为:
        {
            "success": bool,  # 是否成功
            "time": float,  # 响应时间(毫秒)，失败时为-1
            "status_code": int,  # HTTP状态码，失败时为-1
            "error": str  # 错误信息，成功时为空字符串
        }
    """
    result = {
        "success": False,
        "time": -1.0,
        "status_code": -1,
        "error": ""
    }
    
    # 确保URL有协议前缀
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        # 创建SSL上下文（忽略证书错误）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # 记录开始时间
        start_time = time.time()
        
        # 发起请求
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=timeout, context=ctx) as response:
            # 计算响应时间
            result["time"] = (time.time() - start_time) * 1000  # 转换为毫秒
            result["status_code"] = response.getcode()
            result["success"] = 200 <= response.getcode() < 400
    
    except urllib.error.HTTPError as e:
        end_time = time.time()
        result["time"] = (end_time - start_time) * 1000
        result["status_code"] = e.code
        result["success"] = True  # 能获取到状态码说明连接是成功的
        result["error"] = f"HTTP错误: {e.code} {e.reason}"
    
    except urllib.error.URLError as e:
        result["error"] = f"URL错误: {str(e.reason)}"
    
    except socket.timeout:
        result["error"] = f"连接超时 (>{timeout}秒)"
    
    except Exception as e:
        result["error"] = f"未知错误: {str(e)}"
    
    return result

def test_multiple_urls(urls: Dict[str, str], timeout: float = DEFAULT_TIMEOUT, parallel: bool = True) -> Dict[str, Dict]:
    """
    测试多个URL的连接性能
    
    Args:
        urls: 字典，键为名称，值为URL
        timeout: 超时时间(秒)
        parallel: 是否并行测试
        
    Returns:
        字典，键为名称，值为测试结果字典
    """
    results = {}
    
    if parallel:
        # 并行测试
        threads = []
        
        def test_url(name, url):
            results[name] = test_http_connection(url, timeout)
        
        for name, url in urls.items():
            thread = threading.Thread(target=test_url, args=(name, url))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
    else:
        # 顺序测试
        for name, url in urls.items():
            results[name] = test_http_connection(url, timeout)
    
    return results

def find_best_mirror(test_results: Dict[str, Dict]) -> Optional[Dict[str, Union[str, float]]]:
    """
    根据测试结果找出最佳镜像
    
    Args:
        test_results: 测试结果字典
        
    Returns:
        最佳镜像信息，包含name和url字段，如果没有可用镜像则返回None
    """
    # 筛选出成功的结果
    successful = {name: data for name, data in test_results.items() if data.get("success", False)}
    
    if not successful:
        return None
    
    # 按响应时间排序
    sorted_results = sorted(successful.items(), key=lambda x: x[1].get("time", float("inf")))
    
    # 返回响应时间最短的镜像
    best_name, best_data = sorted_results[0]
    
    return {
        "name": best_name,
        "url": best_data.get("url", ""),
        "time": best_data.get("time", -1)
    }

class NetworkTester:
    """
    网络测试器类，提供镜像站点测试功能
    """
    
    def __init__(self):
        """初始化网络测试器"""
        self.logger = logging.getLogger("test_net.tester")
    
    def test_mirrors(self, mirrors: List[Dict], callback=None) -> Dict[str, Dict]:
        """
        测试镜像站点
        
        Args:
            mirrors: 镜像站点列表，每个元素为包含name和url的字典
            callback: 回调函数，每测试完一个站点就调用一次
            
        Returns:
            测试结果字典
        """
        results = {}
        
        for mirror in mirrors:
            name = mirror.get("name", "未命名")
            url = mirror.get("url", "")
            
            # 测试连接
            conn_result = test_http_connection(url)
            
            # 测试ping
            ping_result = {}
            try:
                # 从URL中提取主机名
                hostname = re.sub(r'^https?://', '', url)
                hostname = hostname.split('/')[0]
                if ':' in hostname:
                    hostname = hostname.split(':')[0]
                
                ping_result = ping(hostname)
            except Exception as e:
                self.logger.error(f"Ping测试失败: {str(e)}")
                ping_result = {
                    "success": False,
                    "error": str(e)
                }
            
            # 计算综合得分 (0-100)
            # 响应时间占70分，越低越好
            # 连接成功占30分
            score = 0
            if conn_result.get("success", False):
                score += 30  # 连接成功基础分
                
                # 响应时间得分，最快100ms以下得满分，超过1000ms得0分
                resp_time = conn_result.get("time", 0)
                if resp_time > 0:
                    time_score = max(0, 70 * (1 - (resp_time - 100) / 900))
                    score += time_score
            
            # 构建结果
            result = {
                "url": url,
                "connection": conn_result,
                "ping": ping_result,
                "overall": {
                    "success": conn_result.get("success", False),
                    "score": score,
                    "time": conn_result.get("time", -1)
                }
            }
            
            results[name] = result
            
            # 调用回调函数
            if callback:
                try:
                    callback(name, result)
                except Exception as e:
                    self.logger.error(f"回调函数调用失败: {str(e)}")
        
        return results
    
    def get_best_mirror(self, test_results: Dict[str, Dict]) -> Optional[Dict]:
        """
        从测试结果中获取最佳镜像
        
        Args:
            test_results: 测试结果字典
            
        Returns:
            最佳镜像信息，如果没有可用镜像则返回None
        """
        return find_best_mirror(test_results)

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试ping
    print("测试ping:")
    ping_result = ping("www.baidu.com")
    print(f"Ping结果: {ping_result}")
    
    # 测试HTTP连接
    print("\n测试HTTP连接:")
    http_result = test_http_connection("https://www.baidu.com")
    print(f"HTTP结果: {http_result}")
    
    # 测试多个URL
    print("\n测试多个URL:")
    urls = {
        "百度": "https://www.baidu.com",
        "腾讯": "https://www.qq.com",
        "阿里云": "https://www.aliyun.com"
    }
    
    def on_url_tested(name, result):
        print(f"测试完成: {name}, 响应时间: {result.get('time', 0):.1f}ms, 状态码: {result.get('status_code', 0)}")
    
    # Removed unsupported 'callback' argument from the call below
    results = test_multiple_urls(urls)
    
    # 找出最佳镜像
    best = find_best_mirror(results)
    if best:
        print(f"\n最佳镜像: {best['name']}, 响应时间: {best['time']:.1f}ms")
    else:
        print("\n没有可用的镜像")
