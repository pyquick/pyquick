"""
下载器主类，提供完整的下载功能，支持多线程下载、断点续传和进度跟踪
"""

import os
import sys
import time
import json
import threading
import multiprocessing
from typing import Dict, List, Optional, Callable, Union, Tuple, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote
import logging
import math
from io import BytesIO
import shutil
import traceback
import hashlib
import socket
import ssl
from pathlib import Path

from .chunk import DownloadChunk
from .DownloadTask import DownloadTask, DownloadStatus

# 性能优化常量
CHUNK_SIZE = 4 * 1024 * 1024  # 每次请求的块大小 (4MB) - 增加到4MB提高吞吐量
BUFFER_SIZE = 64 * 1024  # 文件写入缓冲区大小 (64KB) - 增加到64KB提高写入性能
MIN_SPLIT_SIZE = 8 * 1024 * 1024  # 最小分段大小 (8MB) - 增加到8MB减少小文件分片开销
CONNECTION_TIMEOUT = 20  # 连接超时时间 - 增加到20秒
READ_TIMEOUT = 40  # 读取超时时间 - 增加到40秒
MAX_RETRIES = 8  # 最大重试次数 - 增加到8次提高容错
RETRY_DELAY = 1  # 初始重试延迟时间（秒）

# 并发控制 - 智能调整并发数
DEFAULT_CONCURRENT_CONNECTIONS = min(12, multiprocessing.cpu_count() * 3)  # 根据CPU核心数确定默认并发数

# 速度估算参数
SPEED_SAMPLE_SIZE = 15  # 用于计算平均速度的样本数 - 增加到15个样本
SPEED_CALC_INTERVAL = 0.5  # 速度计算间隔(秒) - 减少到0.5秒提高响应性

# 网络条件自适应参数
MIN_THROUGHPUT_THRESHOLD = 10 * 1024  # 最低吞吐量阈值 (10KB/s)
CONNECTION_QUALITY_SAMPLES = 5  # 网络质量采样数
ADAPTIVE_RETRY_MAX = 20  # 自适应重试上限

# 内存使用优化
MAX_MEMORY_BUFFER = 128 * 1024 * 1024  # 最大内存缓冲区 (128MB)

# 校验和选项
ENABLE_CHECKSUM = True  # 启用校验和验证
DEFAULT_CHECKSUM_ALGORITHM = 'sha256'  # 默认校验算法

# 日志配置
log = logging.getLogger("downloader")

class DownloadError(Exception):
    """下载错误基类"""
    pass

class FileSystemError(DownloadError):
    """文件系统相关错误"""
    pass

class RequestError(DownloadError):
    """请求相关错误"""
    pass

class NetworkQualityMonitor:
    """网络质量监控类，用于自适应调整下载参数"""
    
    def __init__(self, sample_size=CONNECTION_QUALITY_SAMPLES):
        self.sample_size = sample_size
        self.speed_samples = []
        self.error_count = 0
        self.last_error_time = 0
        self.lock = threading.RLock()
        
    def add_speed_sample(self, bytes_per_second):
        """添加速度样本"""
        with self.lock:
            self.speed_samples.append(bytes_per_second)
            if len(self.speed_samples) > self.sample_size:
                self.speed_samples.pop(0)
                
    def register_error(self):
        """登记网络错误"""
        with self.lock:
            self.error_count += 1
            self.last_error_time = time.time()
            
    def get_average_speed(self):
        """获取平均速度"""
        with self.lock:
            if not self.speed_samples:
                return 0
            return sum(self.speed_samples) / len(self.speed_samples)
            
    def get_connection_quality(self):
        """获取连接质量评分 (0-10)"""
        with self.lock:
            if not self.speed_samples:
                return 5  # 默认中等质量
                
            avg_speed = self.get_average_speed()
            
            # 基于速度和错误率的质量评分
            if avg_speed < MIN_THROUGHPUT_THRESHOLD:
                base_score = 2
            elif avg_speed < 50 * 1024:  # 50KB/s
                base_score = 4
            elif avg_speed < 200 * 1024:  # 200KB/s
                base_score = 6
            elif avg_speed < 1024 * 1024:  # 1MB/s
                base_score = 8
            else:
                base_score = 10
                
            # 错误数量惩罚
            error_penalty = min(5, self.error_count)
            
            # 错误衰减 (24小时内)
            error_age = time.time() - self.last_error_time
            if error_age > 86400:  # 24小时
                error_penalty = 0
            elif error_age > 3600:  # 1小时
                error_penalty = max(0, error_penalty - 2)
                
            return max(1, base_score - error_penalty)
            
    def get_optimal_threads(self, file_size):
        """根据网络质量和文件大小获取最优线程数"""
        quality = self.get_connection_quality()
        
        # 基于文件大小的基础线程数
        if file_size < 5 * 1024 * 1024:  # 5MB
            base_threads = 2
        elif file_size < 20 * 1024 * 1024:  # 20MB
            base_threads = 4
        elif file_size < 100 * 1024 * 1024:  # 100MB
            base_threads = 6
        elif file_size < 1024 * 1024 * 1024:  # 1GB
            base_threads = 8
        else:
            base_threads = 12
            
        # 根据网络质量调整线程数
        quality_factor = quality / 5.0  # 范围约为0.2-2.0
        
        optimal_threads = max(1, int(base_threads * quality_factor))
        return min(optimal_threads, DEFAULT_CONCURRENT_CONNECTIONS)
        
    def get_optimal_chunk_size(self):
        """根据网络质量获取最优块大小"""
        quality = self.get_connection_quality()
        
        if quality <= 3:
            return 1 * 1024 * 1024  # 1MB
        elif quality <= 5:
            return 2 * 1024 * 1024  # 2MB
        elif quality <= 7:
            return 4 * 1024 * 1024  # 4MB
        else:
            return 8 * 1024 * 1024  # 8MB

class DownloadPart:
    """下载片段管理类"""
    def __init__(self, start: int, end: int, url: str, temp_file: str, 
                 index: int, session: requests.Session = None,
                 network_monitor: NetworkQualityMonitor = None):
        self.start = start
        self.end = end
        self.url = url
        self.temp_file = temp_file
        self.index = index
        self.session = session or requests.Session()
        self.downloaded = 0
        self.total = end - start + 1
        self.error = None
        self.is_paused = False
        self.is_completed = False
        self.last_update_time = time.time()
        self.speed_samples = []
        self.current_speed = 0  # bytes/s
        self.network_monitor = network_monitor
        self.checksum = hashlib.md5()  # 片段数据校验
        
    def get_progress(self) -> float:
        """获取下载进度百分比"""
        if self.total <= 0:
            return 0
        return min(100.0, (self.downloaded / self.total) * 100)
        
    def get_speed(self) -> float:
        """获取当前下载速度 (bytes/s)"""
        return self.current_speed
        
    def update_speed(self, bytes_downloaded: int, elapsed: float) -> None:
        """更新下载速度计算"""
        if elapsed > 0:
            speed = bytes_downloaded / elapsed
            self.speed_samples.append(speed)
            
            # 保持样本数量
            if len(self.speed_samples) > SPEED_SAMPLE_SIZE:
                self.speed_samples.pop(0)
                
            # 计算平均速度
            self.current_speed = sum(self.speed_samples) / len(self.speed_samples)
            
            # 更新网络质量监控
            if self.network_monitor:
                self.network_monitor.add_speed_sample(speed)

    def download(self, headers: Dict = None, proxy: str = None, 
                 on_progress: Callable = None, retry_count: int = 0) -> bool:
        """下载此片段"""
        if self.is_completed:
            return True
            
        if self.is_paused:
            return False

        # 自适应重试上限
        max_retries = ADAPTIVE_RETRY_MAX if retry_count > MAX_RETRIES else MAX_RETRIES
        
        if retry_count > max_retries:
            self.error = f"超过最大重试次数 ({max_retries})"
            return False
            
        _headers = headers or {}
        # 添加范围请求头
        range_header = {'Range': f'bytes={self.start + self.downloaded}-{self.end}'}
        _headers.update(range_header)
        
        try:
            # 创建临时文件路径
            temp_dir = os.path.dirname(self.temp_file)
            if temp_dir:
                os.makedirs(temp_dir, exist_ok=True)
            
            # 设置代理
            proxies = None
            if proxy:
                proxies = {"http": proxy, "https": proxy}
            
            # 智能超时设置    
            connect_timeout = CONNECTION_TIMEOUT
            read_timeout = READ_TIMEOUT
            
            # 根据重试次数调整超时时间
            if retry_count > 2:
                connect_timeout = connect_timeout * 1.5
                read_timeout = read_timeout * 1.5
                
            # 发起请求
            r = self.session.get(
                self.url, 
                headers=_headers, 
                stream=True,
                timeout=(connect_timeout, read_timeout),
                proxies=proxies
            )
            
            r.raise_for_status()
            
            # 检查请求是否被服务器接受
            if r.status_code != 206 and retry_count < 2:
                log.warning(f"服务器未返回206状态码，可能不支持范围请求。重试中... (part {self.index})")
                time.sleep(RETRY_DELAY)
                return self.download(headers, proxy, on_progress, retry_count + 1)
            
            # 打开文件（追加模式）
            mode = 'ab' if self.downloaded > 0 else 'wb'
            
            last_progress_update = time.time()
            chunks_since_update = 0
            bytes_since_update = 0
            
            # 优化读取缓冲区大小
            buffer_size = BUFFER_SIZE
            if self.network_monitor:
                quality = self.network_monitor.get_connection_quality()
                if quality > 7:
                    buffer_size = BUFFER_SIZE * 2
            
            with open(self.temp_file, mode) as f:
                for chunk in r.iter_content(buffer_size):
                    if self.is_paused:
                        return False
                        
                    if chunk:
                        f.write(chunk)
                        self.checksum.update(chunk)  # 更新校验和
                        chunk_size = len(chunk)
                        self.downloaded += chunk_size
                        bytes_since_update += chunk_size
                        chunks_since_update += 1
                        
                        # 减少进度回调频率，提高性能
                        current_time = time.time()
                        elapsed = current_time - last_progress_update
                        
                        if elapsed >= SPEED_CALC_INTERVAL or chunks_since_update >= 50:
                            self.update_speed(bytes_since_update, elapsed)
                            if on_progress:
                                on_progress(self.index, bytes_since_update, self.current_speed)
                            last_progress_update = current_time
                            bytes_since_update = 0
                            chunks_since_update = 0
            
            # 确保最后一次进度更新
            if bytes_since_update > 0 and on_progress:
                on_progress(self.index, bytes_since_update, self.current_speed)
                
            self.is_completed = True
            return True
                
        except (requests.exceptions.RequestException, socket.error, ssl.SSLError) as e:
            # 网络连接错误，可重试
            self.error = str(e)
            
            # 更新网络质量监控
            if self.network_monitor:
                self.network_monitor.register_error()
                
            # 指数退避策略，但根据网络质量调整
            base_delay = RETRY_DELAY
            if self.network_monitor:
                quality = self.network_monitor.get_connection_quality()
                if quality < 5:
                    # 网络质量差，增加退避时间
                    base_delay *= 2
                    
            delay = base_delay * (1.5 ** retry_count)
            # 添加随机抖动防止雷鸣效应 (0-1秒)
            import random
            delay += random.random()
            
            log.warning(f"下载失败 (part {self.index}): {str(e)}. 将在 {delay:.1f}秒后重试 ({retry_count+1}/{max_retries})")
            time.sleep(delay)
            return self.download(headers, proxy, on_progress, retry_count + 1)
                
        except Exception as e:
            self.error = f"下载失败: {str(e)}"
            log.error(f"下载part {self.index}失败: {traceback.format_exc()}")
            return False
            
    def get_checksum(self):
        """获取下载数据的校验和"""
        return self.checksum.hexdigest()

class Downloader:
    """下载管理器"""
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(Downloader, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, max_concurrent_downloads: int = DEFAULT_CONCURRENT_CONNECTIONS):
        if Downloader._initialized:
            return
            
        self.max_concurrent = max_concurrent_downloads
        self.current_downloads = {}  # 当前活动的下载任务
        self.lock = threading.RLock()  # 使用可重入锁提高多线程稳定性
        self.session = requests.Session()  # 使用会话提高连接效率
        self.adapter = requests.adapters.HTTPAdapter(
            max_retries=3, 
            pool_connections=max_concurrent_downloads * 2,
            pool_maxsize=max_concurrent_downloads * 4
        )
        self.session.mount('http://', self.adapter)
        self.session.mount('https://', self.adapter)
        
        # 设置合理的User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 避免SSL验证问题
        self.session.verify = True
        
        self.network_monitor = NetworkQualityMonitor()
        
        Downloader._initialized = True
        
    def _get_file_info(self, url: str, headers: Dict = None, proxy: str = None) -> Tuple[int, bool, str]:
        """获取文件信息，如大小、是否支持断点续传和文件名"""
        _headers = headers or {}
        proxies = None
        if proxy:
            proxies = {"http": proxy, "https": proxy}
            
        # 指数退避重试
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.session.head(
                    url, 
                    headers=_headers, 
                    timeout=CONNECTION_TIMEOUT,
                    proxies=proxies,
                    allow_redirects=True  # 允许重定向
                )
                response.raise_for_status()
                
                # 获取文件大小
                file_size = int(response.headers.get('content-length', 0))
                
                # 检查是否支持范围请求
                accept_ranges = response.headers.get('accept-ranges', '')
                supports_range = 'bytes' in accept_ranges and file_size > 0
                
                # 尝试从Content-Disposition获取文件名
                filename = None
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    import re
                    # 尝试从content-disposition获取文件名
                    pattern = r'filename[^;=\n]*=(["\'])?(.*?)\1?(?:;|$)'
                    matches = re.search(pattern, content_disposition, re.IGNORECASE)
                    if matches:
                        filename = matches.group(2)
                
                # 如果没有从header获取到文件名，则从URL解析
                if not filename:
                    path = urlparse(url).path
                    filename = unquote(os.path.basename(path))
                    
                # 如果还是空，使用URL的哈希作为文件名
                if not filename:
                    filename = f"download_{hashlib.md5(url.encode()).hexdigest()}"
                
                return file_size, supports_range, filename
                
            except (requests.exceptions.RequestException, ValueError) as e:
                if attempt < MAX_RETRIES:
                    # 计算延迟时间（指数退避）
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise RequestError(f"获取文件信息失败: {str(e)}")
                    
        return 0, False, None
        
    def _download_single(self, url: str, save_path: str, on_progress: Callable = None, 
                        on_complete: Callable = None, on_error: Callable = None,
                        headers: Dict = None, proxy: str = None, resume: bool = False,
                        task_id: str = None) -> bool:
        """单线程下载"""
        _headers = headers or {}
        downloaded = 0
        file_size = 0
        temp_file = f"{save_path}.download"
        last_update_time = time.time()
        update_interval = 0.1  # 初始更新间隔（秒）
        speed_samples = []
        current_speed = 0
        download_start_time = time.time()
        
        # 如果是恢复下载，获取已下载的大小
        if resume and os.path.exists(temp_file):
            downloaded = os.path.getsize(temp_file)
            if downloaded > 0:
                _headers['Range'] = f'bytes={downloaded}-'
                
        try:
            # 设置代理
            proxies = None
            if proxy:
                proxies = {"http": proxy, "https": proxy}
                
            # 发起请求
            response = self.session.get(
                url, 
                headers=_headers, 
                stream=True,
                timeout=(CONNECTION_TIMEOUT, READ_TIMEOUT),
                proxies=proxies,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 获取文件大小
            if 'content-length' in response.headers:
                file_size = int(response.headers['content-length'])
                # 对于恢复下载，加上已下载的部分
                if downloaded > 0 and 'content-range' in response.headers:
                    try:
                        # 从Content-Range解析文件总大小
                        content_range = response.headers['content-range']
                        file_size = int(content_range.split('/')[-1])
                    except (ValueError, IndexError):
                        # 解析失败则使用content-length + 已下载大小
                        file_size += downloaded
            
            # 准备文件目录
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # 下载文件
            mode = 'ab' if downloaded > 0 else 'wb'
            with open(temp_file, mode) as f:
                for chunk in response.iter_content(BUFFER_SIZE):
                    if chunk:
                        f.write(chunk)
                        chunk_size = len(chunk)
                        downloaded += chunk_size
                        
                        # 动态调整进度更新频率
                        current_time = time.time()
                        elapsed = current_time - last_update_time
                        
                        if elapsed >= update_interval:
                            # 计算下载速度
                            if elapsed > 0:
                                current_chunk_speed = chunk_size / elapsed
                                speed_samples.append(current_chunk_speed)
                                
                                # 保持样本数量
                                if len(speed_samples) > SPEED_SAMPLE_SIZE:
                                    speed_samples.pop(0)
                                    
                                # 计算平均速度
                                current_speed = sum(speed_samples) / len(speed_samples)
                            
                            if on_progress:
                                on_progress(downloaded, file_size, current_speed)
                            last_update_time = current_time
                            
                            # 根据下载速度动态调整更新间隔
                            if file_size > 0:
                                progress_ratio = downloaded / file_size
                                # 进度越大，更新越慢，但不超过0.5秒
                                update_interval = min(0.5, 0.1 + progress_ratio * 0.2) 
            
            # 下载完成，重命名文件
            shutil.move(temp_file, save_path)
            
            # 计算总下载时间
            total_time = time.time() - download_start_time
            average_speed = downloaded / total_time if total_time > 0 else 0
            
            if on_complete:
                on_complete(save_path, file_size, average_speed)
                
            return True
                
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            log.error(f"下载文件失败: {error_msg}\n{traceback.format_exc()}")
            
            if on_error:
                on_error(error_msg)
                
            return False

    def _download_with_parts(self, url: str, save_path: str, file_size: int,
                           num_parts: int, on_progress: Callable = None,
                           on_complete: Callable = None, on_error: Callable = None,
                           headers: Dict = None, proxy: str = None, resume: bool = False, 
                           task_id: str = None) -> bool:
        """多线程分段下载"""
        if num_parts <= 1:
            return self._download_single(url, save_path, on_progress, on_complete, on_error, headers, proxy, resume, task_id)
            
        _headers = headers or {}
        
        # 创建临时目录
        temp_dir = f"{save_path}.parts"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 计算每个部分的大小
        part_size = max(MIN_SPLIT_SIZE, math.ceil(file_size / num_parts))
        parts = []
        
        # 创建下载部分
        for i in range(num_parts):
            start = i * part_size
            end = min(start + part_size - 1, file_size - 1)
            
            # 创建新会话以避免连接限制
            part_session = requests.Session()
            part_session.mount('http://', self.adapter)
            part_session.mount('https://', self.adapter)
            
            # 设置合理的User-Agent
            part_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            temp_file = os.path.join(temp_dir, f"part_{i}")
            
            # 检查是否存在已下载部分
            downloaded = 0
            if resume and os.path.exists(temp_file):
                downloaded = os.path.getsize(temp_file)
                if downloaded >= (end - start + 1):
                    # 这部分已完全下载
                    part = DownloadPart(start, end, url, temp_file, i, part_session, self.network_monitor)
                    part.downloaded = end - start + 1
                    part.is_completed = True
                    parts.append(part)
                    continue
            
            part = DownloadPart(start, end, url, temp_file, i, part_session, self.network_monitor)
            if downloaded > 0:
                part.downloaded = downloaded
            parts.append(part)
        
        # 创建进度跟踪变量
        total_downloaded = [sum(p.downloaded for p in parts)]
        part_speeds = [0] * len(parts)
        last_update = [time.time()]
        download_complete = [False]
        error_occurred = [False]
        error_message = [None]
        lock = threading.Lock()
        
        def update_progress(part_index: int, chunk_size: int, speed: float):
            """更新总进度"""
            with lock:
                # 更新这个部分的下载速度
                part_speeds[part_index] = speed
                
                # 更新总下载量
                total_downloaded[0] += chunk_size
                
                # 更新总速度和进度
                current_time = time.time()
                if current_time - last_update[0] >= 0.2 or chunk_size >= BUFFER_SIZE * 10:
                    total_speed = sum(part_speeds)
                    if on_progress and not download_complete[0] and not error_occurred[0]:
                        on_progress(total_downloaded[0], file_size, total_speed)
                    last_update[0] = current_time
        
        # 使用线程池下载所有部分
        with ThreadPoolExecutor(max_workers=num_parts) as executor:
            # 提交所有下载任务
            futures = [
                executor.submit(
                    part.download, _headers, proxy, update_progress
                )
                for part in parts if not part.is_completed
            ]
            
            # 等待所有任务完成并处理结果
            for future in as_completed(futures):
                try:
                    success = future.result()
                    if not success:
                        # 找到出错的部分
                        failed_part = next((p for p in parts if p.error is not None), None)
                        if failed_part:
                            error_message[0] = failed_part.error
                            error_occurred[0] = True
                            
                            if on_error:
                                on_error(f"下载部分 {failed_part.index + 1} 失败: {failed_part.error}")
                            return False
                except Exception as e:
                    error_message[0] = str(e)
                    error_occurred[0] = True
                    
                    if on_error:
                        on_error(f"下载任务异常: {str(e)}")
                    return False
                
        # 所有部分下载完成，合并文件
        try:
            with open(save_path, 'wb') as outfile:
                for part in parts:
                    if os.path.exists(part.temp_file):
                        with open(part.temp_file, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile, BUFFER_SIZE * 4)
            
            # 清理临时文件
            self._clean_temp_files(temp_dir)
            
            download_complete[0] = True
            
            # 计算平均下载速度
            total_size = os.path.getsize(save_path)
            
            if on_complete:
                # 计算平均速度
                average_speed = sum(part_speeds)
                on_complete(save_path, total_size, average_speed)
                
            return True
            
        except Exception as e:
            error_message[0] = str(e)
            error_occurred[0] = True
            
            log.error(f"合并文件失败: {str(e)}\n{traceback.format_exc()}")
            
            if on_error:
                on_error(f"合并文件失败: {str(e)}")
            return False
    
    def _clean_temp_files(self, temp_dir: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            log.warning(f"清理临时文件失败: {str(e)}")

    def download(self, url: str, save_path: str, headers: Dict = None, proxy: str = None,
                on_progress: Callable = None, on_complete: Callable = None,
                on_error: Callable = None, num_connections: int = None,
                resume: bool = True) -> str:
        """
        开始下载文件
        
        Args:
            url: 下载URL
            save_path: 保存路径
            headers: 请求头
            proxy: 代理服务器
            on_progress: 进度回调 (downloaded, total, speed) -> None
            on_complete: 完成回调 (file_path, size, speed) -> None
            on_error: 错误回调 (error_message) -> None
            num_connections: 并发连接数
            resume: 是否断点续传
        
        Returns:
            下载ID
        """
        # 生成唯一的下载ID
        download_id = hashlib.md5(f"{url}_{save_path}_{time.time()}".encode()).hexdigest()
        
        # 使用默认并发连接数，如果未指定或无效
        if not num_connections or num_connections < 1:
            num_connections = self.max_concurrent
            
        # 确保保存路径的目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            
        # 创建下载任务状态
        with self.lock:
            self.current_downloads[download_id] = {
                'url': url,
                'save_path': save_path,
                'status': DownloadStatus.PREPARING,
                'progress': 0,
                'size': 0,
                'downloaded': 0,
                'speed': 0,
                'start_time': time.time(),
                'end_time': None,
                'error': None
            }
        
        def download_thread():
            try:
                # 更新状态为准备中
                with self.lock:
                    self.current_downloads[download_id]['status'] = DownloadStatus.PREPARING
                
                # 获取文件信息
                try:
                    file_size, supports_range, remote_filename = self._get_file_info(url, headers, proxy)
                except Exception as e:
                    with self.lock:
                        self.current_downloads[download_id]['status'] = DownloadStatus.ERROR
                        self.current_downloads[download_id]['error'] = str(e)
                    
                    if on_error:
                        on_error(str(e))
                    return
                
                # 如果未指定保存路径的文件名，使用远程文件名
                final_save_path = save_path
                if os.path.isdir(save_path):
                    final_save_path = os.path.join(save_path, remote_filename)
                
                # 更新任务大小
                with self.lock:
                    self.current_downloads[download_id]['size'] = file_size
                    self.current_downloads[download_id]['save_path'] = final_save_path
                
                # 确定最佳连接数
                actual_connections = num_connections
                if not supports_range:
                    actual_connections = 1
                    log.info(f"服务器不支持范围请求，将使用单线程下载: {url}")
                elif file_size < MIN_SPLIT_SIZE * 2:
                    actual_connections = 1
                    log.info(f"文件太小，将使用单线程下载: {url}, 大小: {file_size}")
                else:
                    # 根据文件大小计算合理的连接数
                    max_reasonable_connections = min(
                        num_connections,
                        max(1, math.ceil(file_size / MIN_SPLIT_SIZE))
                    )
                    actual_connections = max_reasonable_connections
                
                # 进度回调包装器
                def progress_wrapper(downloaded, total, speed):
                    progress = (downloaded / total * 100) if total > 0 else 0
                    
                    with self.lock:
                        self.current_downloads[download_id]['progress'] = progress
                        self.current_downloads[download_id]['downloaded'] = downloaded
                        self.current_downloads[download_id]['speed'] = speed
                        self.current_downloads[download_id]['status'] = DownloadStatus.DOWNLOADING
                    
                    if on_progress:
                        on_progress(downloaded, total, speed)
                
                # 完成回调包装器
                def complete_wrapper(file_path, size, speed):
                    with self.lock:
                        self.current_downloads[download_id]['status'] = DownloadStatus.COMPLETED
                        self.current_downloads[download_id]['progress'] = 100
                        self.current_downloads[download_id]['end_time'] = time.time()
                        self.current_downloads[download_id]['speed'] = speed
                    
                    if on_complete:
                        on_complete(file_path, size, speed)
                
                # 错误回调包装器
                def error_wrapper(error_message):
                    with self.lock:
                        self.current_downloads[download_id]['status'] = DownloadStatus.ERROR
                        self.current_downloads[download_id]['error'] = error_message
                        self.current_downloads[download_id]['end_time'] = time.time()
                    
                    if on_error:
                        on_error(error_message)
                
                # 开始下载
                with self.lock:
                    self.current_downloads[download_id]['status'] = DownloadStatus.DOWNLOADING
                
                # 根据连接数选择下载方法
                if actual_connections <= 1:
                    self._download_single(url, final_save_path, progress_wrapper, 
                                         complete_wrapper, error_wrapper, 
                                         headers, proxy, resume, download_id)
                else:
                    self._download_with_parts(url, final_save_path, file_size,
                                            actual_connections, progress_wrapper,
                                            complete_wrapper, error_wrapper,
                                            headers, proxy, resume, download_id)
            
            except Exception as e:
                error_msg = f"下载失败: {str(e)}"
                log.error(f"下载失败: {error_msg}\n{traceback.format_exc()}")
                
                with self.lock:
                    self.current_downloads[download_id]['status'] = DownloadStatus.ERROR
                    self.current_downloads[download_id]['error'] = error_msg
                    self.current_downloads[download_id]['end_time'] = time.time()
                
                if on_error:
                    on_error(error_msg)
        
        # 启动下载线程
        threading.Thread(target=download_thread, daemon=True).start()
        
        return download_id

    def cancel(self, download_id: str) -> bool:
        """取消下载任务"""
        with self.lock:
            if download_id in self.current_downloads:
                # 更新状态
                self.current_downloads[download_id]['status'] = DownloadStatus.CANCELLED
                self.current_downloads[download_id]['end_time'] = time.time()
                
                # 清理临时文件
                save_path = self.current_downloads[download_id]['save_path']
                if save_path:
                    # 清理主下载文件
                    temp_file = f"{save_path}.download"
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    
                    # 清理分段下载临时目录
                    temp_dir = f"{save_path}.parts"
                    if os.path.exists(temp_dir):
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                
                return True
        
        return False

    def get_status(self, download_id: str) -> Dict:
        """获取下载任务状态"""
        with self.lock:
            return self.current_downloads.get(download_id, {}).copy()

    def get_all_downloads(self) -> Dict:
        """获取所有下载任务状态"""
        with self.lock:
            return {k: v.copy() for k, v in self.current_downloads.items()}
            
    def pause(self, download_id: str) -> bool:
        """暂停下载任务"""
        with self.lock:
            if download_id in self.current_downloads:
                self.current_downloads[download_id]['status'] = DownloadStatus.PAUSED
                return True
        return False
        
    def resume(self, download_id: str) -> bool:
        """恢复下载任务"""
        with self.lock:
            if download_id in self.current_downloads:
                task = self.current_downloads[download_id]
                if task['status'] == DownloadStatus.PAUSED:
                    # 创建新的下载任务，复用相同ID
                    # TODO: 实现真正的暂停恢复功能
                    return True
        return False
        
    def clear_completed(self) -> int:
        """清理已完成的下载任务"""
        completed_count = 0
        with self.lock:
            to_remove = []
            for download_id, info in self.current_downloads.items():
                if info['status'] in [DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELLED]:
                    to_remove.append(download_id)
            
            for download_id in to_remove:
                del self.current_downloads[download_id]
                completed_count += 1
                
        return completed_count

# 单例下载器实例
_downloader = None

def get_downloader() -> Downloader:
    """获取下载器实例"""
    global _downloader
    if _downloader is None:
        _downloader = Downloader()
    return _downloader

def download_file(url: str, save_path: str, headers: Dict = None, proxy: str = None,
                 on_progress: Callable = None, on_complete: Callable = None,
                 on_error: Callable = None, num_connections: int = None,
                 resume: bool = True) -> str:
    """
    便捷函数：下载文件
    
    Args:
        url: 下载URL
        save_path: 保存路径
        headers: 请求头
        proxy: 代理服务器
        on_progress: 进度回调 (downloaded, total, speed) -> None
        on_complete: 完成回调 (file_path, size, speed) -> None
        on_error: 错误回调 (error_message) -> None
        num_connections: 并发连接数
        resume: 是否断点续传
    
    Returns:
        下载ID
    """
    downloader = get_downloader()
    return downloader.download(
        url, save_path, headers, proxy,
        on_progress, on_complete, on_error,
        num_connections, resume
    )

def cancel_download(download_id: str) -> bool:
    """
    便捷函数：取消下载
    
    Args:
        download_id: 下载ID
    
    Returns:
        是否成功取消
    """
    downloader = get_downloader()
    return downloader.cancel(download_id)

def get_download_status(download_id: str) -> Dict:
    """
    便捷函数：获取下载状态
    
    Args:
        download_id: 下载ID
    
    Returns:
        下载状态信息
    """
    downloader = get_downloader()
    return downloader.get_status(download_id)

def get_all_downloads() -> Dict:
    """
    便捷函数：获取所有下载状态
    
    Returns:
        所有下载状态信息
    """
    downloader = get_downloader()
    return downloader.get_all_downloads()
    
def pause_download(download_id: str) -> bool:
    """
    便捷函数：暂停下载
    
    Args:
        download_id: 下载ID
    
    Returns:
        是否成功暂停
    """
    downloader = get_downloader()
    return downloader.pause(download_id)
    
def resume_download(download_id: str) -> bool:
    """
    便捷函数：恢复下载
    
    Args:
        download_id: 下载ID
    
    Returns:
        是否成功恢复
    """
    downloader = get_downloader()
    return downloader.resume(download_id)
    
def clear_completed_downloads() -> int:
    """
    便捷函数：清理已完成的下载
    
    Returns:
        清理的下载数量
    """
    downloader = get_downloader()
    return downloader.clear_completed()