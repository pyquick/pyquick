import os
import time
import requests
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from concurrent.futures import ThreadPoolExecutor
from .DownloadTask import DownloadTask, DownloadStatus

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MultiThreadDownloader")


class DownloadPart:
    """下载分片类，表示一个文件下载的一部分"""
    
    def __init__(self, part_id: int, start: int, end: int, task: DownloadTask):
        """
        初始化下载分片
        
        Args:
            part_id: 分片ID
            start: 起始字节
            end: 结束字节（包含）
            task: 所属的下载任务
        """
        self.part_id = part_id
        self.start = start
        self.end = end
        self.task = task
        self.temp_file = os.path.join(task.get_temp_dir(), f"part_{part_id}")
        self.downloaded = 0  # 已下载字节数
        self.status = DownloadStatus.WAITING
        self.retry_count = 0
        self.error = ""


class MultiThreadDownloader:
    """多线程下载器，负责执行一个下载任务"""
    
    def __init__(self, task: DownloadTask):
        """初始化下载器"""
        self.task = task
        self.threads: List[threading.Thread] = []
        self.stop_event = threading.Event()
        self.lock = threading.RLock()  # 改用可重入锁
        
        # 性能优化参数
        self.chunk_size = 32768  # 32KB的块大小
        self.buffer_size = 1024 * 1024  # 1MB的缓冲区
        self.min_split_size = 5 * 1024 * 1024  # 最小分片大小5MB
        
        # 速度计算相关
        self.speed_calculator = SpeedCalculator()
        self.last_progress_update = 0
        self.progress_update_interval = 0.1  # 100ms更新一次进度
        
        # 下载临时目录
        self.temp_dir = os.path.join(self.task.save_dir, f".temp_{os.path.basename(self.task.file_path)}")
        
        # 日志记录器
        self.logger = logging.getLogger("MultiThreadDownloader")
        
    def set_callbacks(self, 
                     progress_callback: Optional[Callable[[str, int, float, float], None]] = None,
                     completion_callback: Optional[Callable[[str], None]] = None,
                     error_callback: Optional[Callable[[str, str], None]] = None):
        """
        设置回调函数
        
        Args:
            progress_callback: 进度回调(task_id, downloaded_bytes, percent, speed)
            completion_callback: 完成回调(task_id)
            error_callback: 错误回调(task_id, error_message)
        """
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
    
    def start(self):
        """开始下载"""
        if self.task.status == DownloadStatus.DOWNLOADING:
            return
            
        # 创建临时目录
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            
        # 设置状态为下载中
        self.task.update_status(DownloadStatus.DOWNLOADING)
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 启动下载线程
        self._start_download()
    
    def stop(self):
        """停止下载"""
        self.stop_event.set()
        
        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
                
        self.threads.clear()
    
    def pause(self):
        """暂停下载"""
        if self.task.status != DownloadStatus.DOWNLOADING:
            return
            
        self.stop()
        self.task.update_status(DownloadStatus.PAUSED)
        self.logger.info(f"任务已暂停: {self.task.task_id}")
    
    def resume(self):
        """恢复下载"""
        if self.task.status != DownloadStatus.PAUSED:
            return
            
        self.start()
        self.logger.info(f"任务已恢复: {self.task.task_id}")
    
    def cancel(self):
        """取消下载"""
        self.stop()
        self.task.update_status(DownloadStatus.CANCELLED)
        self._cleanup_temp_files()
        self.logger.info(f"任务已取消: {self.task.task_id}")
    
    def _start_download(self):
        """开始下载流程"""
        try:
            # 获取文件信息
            self._get_file_info()
            
            if self.stop_event.is_set():
                return
                
            # 如果支持断点续传，则使用多线程下载
            if self.task.is_resumable and self.task.content_length > 0:
                self._download_with_threads()
            else:
                # 不支持断点续传，使用单线程
                self._download_single_thread()
                
        except Exception as e:
            self.task.update_status(DownloadStatus.ERROR, str(e))
            if self.error_callback:
                self.error_callback(self.task.task_id, str(e))
            self.logger.error(f"下载出错: {self.task.task_id}, {str(e)}")
    
    def _get_file_info(self):
        """获取要下载的文件信息"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 发送HEAD请求获取文件信息
            response = requests.head(
                self.task.url, 
                headers=headers,
                proxies=self.task.proxies,
                timeout=10
            )
            
            response.raise_for_status()
            
            # 保存响应头信息
            self.task.headers = dict(response.headers)
            
            # 获取文件大小
            content_length = response.headers.get('Content-Length')
            self.task.content_length = int(content_length) if content_length else 0
            
            # 检查是否支持断点续传
            accept_ranges = response.headers.get('Accept-Ranges')
            self.task.is_resumable = accept_ranges == 'bytes'
            
            # 获取文件名
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                import re
                filename_match = re.search(r'filename="(.+?)"', content_disposition)
                if filename_match:
                    self.task.file_name = filename_match.group(1)
                    self.task.file_path = os.path.join(self.task.save_dir, self.task.file_name)
            
            self.logger.info(f"获取文件信息: {self.task.file_name}, 大小: {self.task.get_formatted_size()}, 断点续传: {self.task.is_resumable}")
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {str(e)}")
            raise Exception(f"获取文件信息失败: {str(e)}")
    
    def _download_single_thread(self):
        """单线程下载（不支持断点续传的情况）"""
        thread = threading.Thread(target=self._download_thread_func, args=(0, 0, self.task.content_length))
        self.threads.append(thread)
        thread.start()
    
    def _download_with_threads(self):
        """多线程下载"""
        # 计算每个线程的下载范围
        chunk_size = self.task.content_length // self.task.thread_count
        
        self.task.parts = []
        for i in range(self.task.thread_count):
            start = i * chunk_size
            end = (i + 1) * chunk_size - 1 if i < self.task.thread_count - 1 else self.task.content_length - 1
            
            self.task.parts.append({
                "index": i,
                "start": start,
                "end": end,
                "size": end - start + 1,
                "downloaded": 0
            })
            
            # 创建并启动下载线程
            thread = threading.Thread(target=self._download_thread_func, args=(i, start, end))
            self.threads.append(thread)
            thread.start()
    
    def _download_thread_func(self, thread_index: int, start_byte: int, end_byte: int):
        """优化的下载线程函数"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Range': f'bytes={start_byte}-{end_byte}'
            }
            
            temp_file = os.path.join(self.temp_dir, f"part_{thread_index}.tmp")
            self.task.temp_files.append(temp_file)
            
            # 断点续传处理
            current_size = 0
            if os.path.exists(temp_file) and self.task.is_resumable:
                current_size = os.path.getsize(temp_file)
                if current_size > 0:
                    new_start = start_byte + current_size
                    if new_start >= end_byte:
                        return
                    headers['Range'] = f'bytes={new_start}-{end_byte}'
                    with self.lock:
                        self.task.downloaded_size += current_size
            
            with requests.get(
                self.task.url,
                headers=headers,
                stream=True,
                proxies=self.task.proxies,
                timeout=(10, 30),
                verify=False
            ) as response:
                response.raise_for_status()
                
                chunk_size = self._calculate_chunk_size(end_byte - start_byte)
                mode = 'ab' if current_size > 0 else 'wb'
                
                with open(temp_file, mode) as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if self.stop_event.is_set():
                            return
                            
                        if chunk:
                            f.write(chunk)
                            chunk_size = len(chunk)
                            
                            with self.lock:
                                self.task.downloaded_size += chunk_size
                                self.speed_calculator.add_bytes(chunk_size)
                                
                                # 节流进度更新
                                current_time = time.time()
                                if current_time - self.last_progress_update >= self.progress_update_interval:
                                    speed = self.speed_calculator.get_speed()
                                    progress = (self.task.downloaded_size / self.task.content_length) * 100
                                    self.task.update_progress(self.task.downloaded_size, speed)
                                    self.last_progress_update = current_time
            
        except Exception as e:
            self.logger.error(f"Thread {thread_index} error: {str(e)}")
            with self.lock:
                if not self.stop_event.is_set():
                    self.stop_event.set()
                    self.task.update_status(DownloadStatus.ERROR, str(e))
    
    def _check_all_parts_completed(self) -> bool:
        """
        检查所有分片是否下载完成
        
        Returns:
            是否全部完成
        """
        with self.lock:
            # 检查是否所有线程都还活着
            all_threads_done = all(not thread.is_alive() for thread in self.threads)
            
            if not all_threads_done:
                return False
                
            # 检查下载的总大小是否等于文件大小
            if self.task.content_length > 0:
                return self.task.downloaded_size >= self.task.content_length
                
            # 如果无法确定文件大小，则检查所有线程是否已退出
            return True
    
    def _merge_files(self):
        """合并所有临时文件"""
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(self.task.file_path), exist_ok=True)
            
            # 创建完整文件
            with open(self.task.file_path, 'wb') as out_file:
                for i in range(len(self.task.parts)):
                    temp_file = os.path.join(self.temp_dir, f"part_{i}.tmp")
                    if os.path.exists(temp_file):
                        with open(temp_file, 'rb') as in_file:
                            out_file.write(in_file.read())
            
            # 更新状态为完成
            self.task.update_status(DownloadStatus.COMPLETED)
            
            # 清理临时文件
            self._cleanup_temp_files()
            
            # 调用完成回调
            if self.completion_callback:
                self.completion_callback(self.task.task_id)
                
            self.logger.info(f"下载完成: {self.task.file_path}")
                
        except Exception as e:
            self.logger.error(f"合并文件失败: {str(e)}")
            self.task.update_status(DownloadStatus.ERROR, f"合并文件失败: {str(e)}")
            if self.error_callback:
                self.error_callback(self.task.task_id, str(e))
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for temp_file in self.task.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
                
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {str(e)}")
    
    def _calculate_optimal_threads(self, file_size: int) -> int:
        """计算最优线程数"""
        # 根据文件大小动态调整线程数
        if file_size < 10 * 1024 * 1024:  # 小于10MB
            return 2
        elif file_size < 100 * 1024 * 1024:  # 小于100MB
            return min(4, self.task.thread_count)
        else:
            return min(8, self.task.thread_count)
            
    def _calculate_chunk_size(self, part_size: int) -> int:
        """计算最优的数据块大小"""
        if part_size < 1024 * 1024:  # 1MB
            return 8192  # 8KB
        elif part_size < 10 * 1024 * 1024:  # 10MB
            return 32768  # 32KB
        else:
            return 65536  # 64KB


class SpeedCalculator:
    """下载速度计算器"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size  # 计算窗口大小（秒）
        self.bytes_window = []  # [(timestamp, bytes)]
        self.lock = threading.Lock()
        
    def add_bytes(self, bytes_count: int):
        """添加新的字节计数"""
        with self.lock:
            now = time.time()
            self.bytes_window.append((now, bytes_count))
            
            # 清理超出窗口的数据
            cutoff_time = now - self.window_size
            self.bytes_window = [(t, b) for t, b in self.bytes_window if t >= cutoff_time]
            
    def get_speed(self) -> float:
        """获取当前速度（字节/秒）"""
        with self.lock:
            if not self.bytes_window:
                return 0.0
                
            now = time.time()
            window_start = now - self.window_size
            
            # 计算窗口内的总字节数
            total_bytes = sum(bytes_count for t, bytes_count in self.bytes_window if t >= window_start)
            
            # 获取实际时间窗口
            if self.bytes_window:
                actual_window = now - max(window_start, self.bytes_window[0][0])
                if actual_window > 0:
                    return total_bytes / actual_window
                    
            return 0.0