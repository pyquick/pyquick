"""
下载器主类，提供完整的下载功能
"""

import os
import time
import json
import threading
import multiprocessing
from typing import Dict, List, Optional, Callable, Union, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote
import logging

from .chunk import DownloadChunk
from .DownloadTask import DownloadTask, DownloadStatus

class DownloadPart:
    """下载分片信息"""
    
    def __init__(self, start: int, end: int, index: int):
        self.start = start        # 起始字节
        self.end = end            # 结束字节
        self.index = index        # 分片索引
        self.downloaded = 0       # 已下载字节数
        self.complete = False     # 是否完成
        self.temp_file = ""       # 临时文件路径
        

class Downloader:
    """文件下载器实现"""
    
    def __init__(self, 
                 task: DownloadTask, 
                 on_progress: Optional[Callable[[DownloadTask], None]] = None,
                 on_complete: Optional[Callable[[DownloadTask], None]] = None,
                 on_error: Optional[Callable[[DownloadTask, str], None]] = None):
        """
        初始化下载器
        
        Args:
            task: 下载任务
            on_progress: 进度回调
            on_complete: 完成回调
            on_error: 错误回调
        """
        self.task = task
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        
        self.stop_event = threading.Event()
        self.parts: List[DownloadPart] = []
        self.lock = threading.Lock()
        self.thread_pool = None
        self.progress_thread = None
        self.last_update_time = 0
        self.last_downloaded_bytes = 0
            
    def start(self):
        """开始下载"""
        if self.task.status == DownloadStatus.DOWNLOADING:
            return
            
        self.stop_event.clear()
        threading.Thread(target=self._download_thread, daemon=True).start()
        
    def pause(self):
        """暂停下载"""
        if self.task.status != DownloadStatus.DOWNLOADING:
            return
            
        self.task.update_status(DownloadStatus.PAUSED)
        self.stop_event.set()
        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = None
        
    def resume(self):
        """恢复下载"""
        if self.task.status != DownloadStatus.PAUSED:
            return
            
        self.stop_event.clear()
        threading.Thread(target=self._download_thread, daemon=True).start()
        
    def cancel(self):
        """取消下载"""
        self.task.update_status(DownloadStatus.CANCELLED)
        self.stop_event.set()
        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = None
            
        # 清理临时文件
        self._clean_temp_files()
    
    def _download_thread(self):
        """下载线程"""
        try:
            # 更新任务状态
            self.task.update_status(DownloadStatus.DOWNLOADING)
            
            # 获取文件信息
            file_info = self._get_file_info()
            if not file_info:
                return
                
            file_name, file_size, accept_ranges = file_info
            self.task.set_file_info(file_name, file_size, accept_ranges)
            
            # 创建保存目录
            if not os.path.exists(self.task.save_dir):
                os.makedirs(self.task.save_dir, exist_ok=True)
                
            # 开始下载
            if accept_ranges and file_size > 0 and self.task.thread_count > 1:
                # 多线程分片下载
                self._download_with_parts(file_size)
            else:
                # 单线程下载
                self._download_single()
                
        except Exception as e:
            self._handle_error(f"下载异常: {str(e)}")
    
    def _get_file_info(self) -> Optional[Tuple[str, int, bool]]:
        """
        获取文件信息
        
        Returns:
            如果成功，返回(文件名, 文件大小, 是否支持断点续传)；否则返回None
        """
        try:
            # 第一处修改 - _get_file_info 方法中的 HEAD 请求
            response = requests.head(
                self.task.url, 
                timeout=10, 
                allow_redirects=True,
                proxies=self.task.proxies,
                verify=False  # 添加此参数
            )
    
            # 第二处修改 - _download_single 方法中的 GET 请求
            response = requests.get(
                self.task.url,
                headers=headers,
                stream=True,
                timeout=30,
                proxies=self.task.proxies,
                verify=False  # 添加此参数
            )
    
            # 第三处修改 - _download_part 方法中的 GET 请求
            response = requests.get(
                self.task.url,
                headers=headers,
                stream=True,
                timeout=30,
                proxies=self.task.proxies,
                verify=False  # 添加此参数
            )
            
            if response.status_code != 200:
                self._handle_error(f"服务器响应错误: {response.status_code}")
                return None
                
            # 获取文件大小
            content_length = response.headers.get('Content-Length')
            file_size = int(content_length) if content_length else 0
            
            # 是否支持断点续传
            accept_ranges = response.headers.get('Accept-Ranges') == 'bytes'
            
            # 获取文件名
            file_name = self._extract_filename(response)
            
            return file_name, file_size, accept_ranges
                
        except Exception as e:
            self._handle_error(f"获取文件信息失败: {str(e)}")
            return None
    
    def _extract_filename(self, response) -> str:
        """从响应头或URL中提取文件名"""
        # 尝试从Content-Disposition获取
        cd = response.headers.get('Content-Disposition')
        if cd:
            import re
            if 'filename=' in cd:
                filename = re.findall('filename="(.+?)"', cd) or re.findall('filename=(.+)', cd)
                if filename:
                    return filename[0].strip('"')
        
        # 从URL中提取
        url_path = urlparse(self.task.url).path
        file_name = os.path.basename(unquote(url_path))
        
        # 如果URL中没有文件名，使用任务ID
        if not file_name or file_name.endswith('/'):
            file_name = f"download_{self.task.task_id}"
            
        return file_name
    
    def _download_single(self):
        """单线程下载文件"""
        temp_file = f"{self.task.file_path}.tmp"
        
        # 检查是否存在未完成的下载
        start_pos = 0
        if os.path.exists(temp_file) and self.task.resumable:
            start_pos = os.path.getsize(temp_file)
            mode = 'ab'
        else:
            mode = 'wb'
            
        headers = {}
        if start_pos > 0:
            headers['Range'] = f'bytes={start_pos}-'
            
        try:
            # 开始下载
            response = requests.get(
                self.task.url,
                headers=headers,
                stream=True,
                timeout=30,
                proxies=self.task.proxies
            )
            
            if response.status_code not in [200, 206]:
                self._handle_error(f"服务器响应错误: {response.status_code}")
                return
                
            # 开始进度更新线程
            self._start_progress_tracker()
                
            # 写入文件
            with open(temp_file, mode) as f:
                downloaded = start_pos
                
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set():
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        with self.lock:
                            self.task.update_progress(downloaded, self.task.file_size, 0)
            
            # 完成下载
            if os.path.exists(temp_file):
                # 如果目标文件已存在，先删除
                if os.path.exists(self.task.file_path):
                    os.remove(self.task.file_path)
                # 重命名临时文件
                os.rename(temp_file, self.task.file_path)
                
            self._complete_download()
                
        except Exception as e:
            self._handle_error(f"下载失败: {str(e)}")
    
    def _download_with_parts(self, file_size: int):
        """
        多线程分片下载
        
        Args:
            file_size: 文件总大小
        """
        # 创建临时目录
        temp_dir = f"{self.task.file_path}.parts"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        
        # 智能计算分块大小
        optimal_part_size = max(5 * 1024 * 1024, file_size // 4)  # 最小5MB，最多4个分块
        part_size = min(optimal_part_size, file_size // 2)
        
        # 动态调整线程数
        actual_threads = min(4, max(2, file_size // (10 * 1024 * 1024)))  # 每10MB分配1个线程，2-4个线程
        
        # 创建分片
        self.parts.clear()
        for i in range(actual_threads):
            start = i * part_size
            end = min(start + part_size - 1, file_size - 1)
            
            part = DownloadPart(start, end, i)
            part.temp_file = os.path.join(temp_dir, f"part_{i}")
            
            # 检查是否有已下载的部分
            if os.path.exists(part.temp_file):
                part.downloaded = os.path.getsize(part.temp_file)
                if part.downloaded >= (end - start + 1):
                    part.complete = True
                    part.downloaded = end - start + 1
            
            self.parts.append(part)
        
        # 开始进度更新线程
        self._start_progress_tracker()
        
        # 创建线程池下载
        self.thread_pool = ThreadPoolExecutor(max_workers=actual_threads)
        futures = []
        
        for part in self.parts:
            if not part.complete:
                futures.append(self.thread_pool.submit(self._download_part, part))
                        
        # 等待所有分片完成
        completed = True
        for future in futures:
            if self.stop_event.is_set():
                completed = False
                break
                
            try:
                if not future.result():
                    completed = False
            except Exception as e:
                self._handle_error(f"下载分片失败: {str(e)}")
                completed = False
                break
        
        # 停止线程池
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
            self.thread_pool = None
        
        # 如果全部完成，合并文件
        if completed:
            if self._merge_parts():
                self._complete_download()
    
    def _download_part(self, part: DownloadPart) -> bool:
        """
        下载分片
        
        Args:
            part: 分片信息
            
        Returns:
            是否成功
        """
        if part.complete:
            return True
            
        start_pos = part.start + part.downloaded
        headers = {'Range': f'bytes={start_pos}-{part.end}'}
        
        try:
            # 开始下载
            response = requests.get(
                self.task.url,
                headers=headers,
                stream=True,
                timeout=30,
                proxies=self.task.proxies
            )
            
            if response.status_code != 206:
                self._handle_error(f"分片下载失败，服务器响应: {response.status_code}")
                return False
            
            # 写入文件
            mode = 'ab' if part.downloaded > 0 else 'wb'
            with open(part.temp_file, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set():
                        return False
                        
                    if chunk:
                        f.write(chunk)
                        with self.lock:
                            part.downloaded += len(chunk)
            
            # 标记完成
            part.complete = True
            return True
                
        except Exception as e:
            self._handle_error(f"下载分片失败: {str(e)}")
            return False
            
    def _merge_parts(self) -> bool:
        """
        合并分片文件
        
        Returns:
            是否成功
        """
        temp_dir = f"{self.task.file_path}.parts"
        
        try:
            # 检查所有分片是否完成
            for part in self.parts:
                if not part.complete:
                    return False
                
            # 如果目标文件已存在，先删除
            if os.path.exists(self.task.file_path):
                os.remove(self.task.file_path)
            
            # 合并文件
            with open(self.task.file_path, 'wb') as outfile:
                for part in sorted(self.parts, key=lambda p: p.index):
                    with open(part.temp_file, 'rb') as infile:
                        outfile.write(infile.read())
            
            # 清理临时文件
            self._clean_temp_files()
                
            return True
            
        except Exception as e:
            self._handle_error(f"合并文件失败: {str(e)}")
            return False
    
    def _clean_temp_files(self):
        """清理临时文件"""
        try:
            # 删除分片临时文件
            temp_dir = f"{self.task.file_path}.parts"
            if os.path.exists(temp_dir):
                for part in self.parts:
                    if os.path.exists(part.temp_file):
                        os.remove(part.temp_file)
                os.rmdir(temp_dir)
            
            # 删除单线程临时文件
            temp_file = f"{self.task.file_path}.tmp"
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception:
            pass  # 忽略清理失败
            
    def _start_progress_tracker(self):
        """启动进度跟踪线程"""
        if self.progress_thread and self.progress_thread.is_alive():
            return
            
        self.last_update_time = time.time()
        self.last_downloaded_bytes = self._get_total_downloaded()
        
        self.progress_thread = threading.Thread(
            target=self._progress_thread,
            daemon=True
        )
        self.progress_thread.start()
    
    def _progress_thread(self):
        """进度更新线程"""
        while not self.stop_event.is_set() and self.task.status == DownloadStatus.DOWNLOADING:
            try:
                # 每秒更新一次进度
                time.sleep(1.0)
            
                # 计算下载速度
                current_time = time.time()
                downloaded = self._get_total_downloaded()
                
                time_diff = current_time - self.last_update_time
                bytes_diff = downloaded - self.last_downloaded_bytes
                
                if time_diff > 0:
                    speed = bytes_diff / time_diff
                else:
                    speed = 0
                
                # 更新进度信息
                with self.lock:
                    self.task.update_progress(downloaded, self.task.file_size, speed)
                
                # 更新基准值
                self.last_update_time = current_time
                self.last_downloaded_bytes = downloaded
                
                # 调用进度回调
                if self.on_progress:
                    self.on_progress(self.task)
                    
            except Exception:
                pass
    
    def _get_total_downloaded(self) -> int:
        """获取总下载量"""
        if self.parts:
            # 多线程模式
            return sum(part.downloaded for part in self.parts)
        else:
            # 单线程模式
            return self.task.downloaded_bytes
    
    def _complete_download(self):
        """完成下载"""
        with self.lock:
            self.task.update_status(DownloadStatus.COMPLETED)
            
            # 确保进度100%
            if self.task.file_size > 0:
                self.task.update_progress(self.task.file_size, self.task.file_size, 0)
        
        # 停止进度线程
        self.stop_event.set()
        
        # 清理临时文件
        self._clean_temp_files()
        
        # 回调
        if self.on_complete:
            self.on_complete(self.task)
    
    def _handle_error(self, error_msg: str):
        """处理错误"""
        with self.lock:
            if self.task.status not in [DownloadStatus.PAUSED, DownloadStatus.CANCELLED]:
                self.task.update_status(DownloadStatus.ERROR, error_msg)
                
                # 调用错误回调
                if self.on_error:
                    self.on_error(self.task, error_msg)
                    
        # 停止下载
        self.stop_event.set()