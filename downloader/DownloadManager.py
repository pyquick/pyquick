from .downloader import Downloader
import os
import time
import threading
import uuid
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
import logging

from .DownloadTask import DownloadStatus
from .MultiThreadDownloader import MultiThreadDownloader

class TaskStatus(Enum):
    """下载任务状态"""
    WAITING = "waiting"      # 等待中
    DOWNLOADING = "downloading"  # 下载中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 错误
    CANCELLED = "cancelled"  # 已取消

class DownloadTask:
    """表示一个下载任务"""
    def __init__(self, url, file_path, task_id, thread_count, proxies=None):
        self.url = url
        self.file_path = file_path
        self.task_id = task_id
        self.thread_count = thread_count
        self.proxies = proxies
        self.downloader = None
        self.status = 'pending'  # pending, downloading, paused, completed, cancelled, error
        self.progress = 0.0
        self.speed = 0
        self.start_time = None
        self.end_time = None
        self.error = None
        self.callbacks = []  # 回调函数列表

    def register_callback(self, callback):
        """注册状态变化回调"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        """取消回调注册"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def notify_callbacks(self):
        """通知所有回调"""
        # 使用线程池异步执行回调，避免阻塞主线程
        with ThreadPoolExecutor(max_workers=4) as executor:
            for callback in self.callbacks:
                try:
                    executor.submit(callback, self)
                except Exception as e:
                    print(f"回调错误: {e}")

    def on_progress(self, progress, speed, status):
        """进度更新回调"""
        self.progress = progress
        self.speed = speed
        
        # 如果状态发生变化，则更新任务状态
        if status != self.status:
            self.status = status
            if status == 'completed':
                self.end_time = time.time()
            elif status == 'error' and self.downloader:
                self.error = self.downloader.error
                
        # 节流控制：每100ms最多通知一次回调
        current_time = time.time() * 1000
        if hasattr(self, '_last_notify_time'):
            if current_time - self._last_notify_time < 100:
                return
        
        self._last_notify_time = current_time
        # 通知回调
        self.notify_callbacks()

    def start(self):
        """开始下载任务"""
        if not self.downloader:
            self.downloader = Downloader(
                url=self.url,
                file_path=self.file_path,
                num_threads=self.num_threads,
                proxies=self.proxies,
                on_progress=self.on_progress
            )
            
        self.start_time = time.time()
        self.status = 'downloading'
        self.notify_callbacks()
        
        # 启动下载器
        threading.Thread(
            target=self._start_download,
            daemon=True
        ).start()
        
    def _start_download(self):
        """启动下载器的线程函数"""
        try:
            self.downloader.start()
        except Exception as e:
            self.status = 'error'
            self.error = str(e)
            self.notify_callbacks()

    def pause(self):
        """暂停下载任务"""
        if self.downloader and self.status == 'downloading':
            self.downloader.pause()
            self.status = 'paused'
            self.notify_callbacks()
            return True
        return False

    def resume(self):
        """恢复下载任务"""
        if self.downloader and self.status == 'paused':
            self.status = 'downloading'  
            self.notify_callbacks()
            
            # 启动下载器
            threading.Thread(
                target=self._start_download,
                daemon=True
            ).start()
            
            return True
        return False

    def cancel(self):
        """取消下载任务"""
        if self.downloader and self.status in ['downloading', 'paused']:
            self.downloader.cancel()
            self.status = 'cancelled'
            self.notify_callbacks()
            return True
        return False

    def get_file_name(self):
        """获取文件名"""
        return os.path.basename(self.file_path)

    def get_formatted_speed(self):
        """获取格式化的速度字符串"""
        if self.speed < 1024:
            return f"{self.speed:.1f} B/s"
        elif self.speed < 1024 * 1024:
            return f"{self.speed/1024:.1f} KB/s"
        else:
            return f"{self.speed/(1024*1024):.1f} MB/s"

    def get_duration(self):
        """获取下载持续时间（秒）"""
        if self.start_time is None:
            return 0
            
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def get_formatted_duration(self):
        """获取格式化的下载时间"""
        duration = self.get_duration()
        
        if duration < 60:
            return f"{int(duration)} 秒"
        elif duration < 3600:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes} 分 {seconds} 秒"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            return f"{hours} 小时 {minutes} 分"

    def __str__(self):
        return f"DownloadTask(id={self.task_id}, url={self.url}, status={self.status})"
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "url": self.url,
            "save_path": self.file_path,
            "filename": self.get_file_name(),
            "full_path": self.file_path,
            "status": self.status.value,
            "progress": self.progress,
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "speed": self.speed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error,
            "extra_info": {}
        }

class DownloadManager:
    """下载管理器，负责管理多个下载任务"""
    
    def __init__(self, task_db_path=None, max_concurrent_downloads=2, 
                num_threads_per_download=4, on_task_status_changed=None, status_callback=None):
        """初始化下载管理器
        self.lock = threading.Lock()
        self.status_callback = status_callback
        
        优化参数:
        - max_concurrent_downloads: 并发下载数从3降为2，减少系统负载
        - num_threads_per_download: 每个下载的线程数从5降为4，平衡性能与资源占用
        
        Args:
            task_db_path: 任务数据库路径
            max_concurrent_downloads: 最大并发下载数
            num_threads_per_download: 每个下载的线程数
            on_task_status_changed: 任务状态变化回调
        """
        self.tasks: Dict[str, DownloadTask] = {}
        self.downloaders: Dict[str, Downloader] = {}
        self.lock = threading.RLock()
        self.max_concurrent_downloads = max_concurrent_downloads
        self.active_downloads = 0
        self.task_queue: List[str] = []
        self.is_queue_running = False
        self.task_db_path = task_db_path
        self.num_threads_per_download = num_threads_per_download
        
        # 回调函数
        self.on_task_status_changed = on_task_status_changed
        self.on_task_added = None
        self.on_task_removed = None
        self.on_task_progress = None
        
        # 启动队列处理线程
        self._start_queue_processor()
        super().__init__()
        
    def add_task(self, url: str, file_path: str, thread_count: int , 
               proxies: Optional[Dict[str, str]] = None) -> str:
        """
        添加新的下载任务
        
        Args:
            url: 下载链接
            file_path: 文件保存路径
            thread_count: 下载线程数
            proxies: 代理配置
            
        Returns:
            任务ID
        """
        with self.lock:
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务
            task = DownloadTask(
                task_id=task_id,
                url=url,
                file_path=file_path,
                thread_count=thread_count,
                proxies=proxies
            )
            
            # 添加到任务列表
            self.tasks[task_id] = task
            
            # 创建下载器
            downloader = Downloader(
                task=task,
                on_progress=self._on_progress_callback,
                on_complete=self._on_complete_callback,
                on_error=self._on_error_callback
            )
            self.downloaders[task_id] = downloader
            
            # 添加到下载队列
            self.task_queue.append(task_id)
            
            # 回调通知
            if self.on_task_added:
                self.on_task_added(task)
            
            return task_id
    
    def start_task(self, task_id: str) -> bool:
        """
        开始下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.tasks or task_id not in self.downloaders:
                return False
                
            task = self.tasks[task_id]
            
            # 如果任务已经在运行，直接返回
            if task.status == DownloadStatus.DOWNLOADING:
                return True
                
            # 如果已经完成，无法再次启动
            if task.status == DownloadStatus.COMPLETED:
                return False
                
            # 如果正在等待，直接返回
            if task.status == DownloadStatus.WAITING:
                return True
            
            # 如果可以立即开始
            if self.active_downloads < self.max_concurrent_downloads:
                self.active_downloads += 1
                task.update_status(DownloadStatus.DOWNLOADING)
                
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
                    
                # 启动下载器
                self.downloaders[task_id].start()
                return True
            else:
                # 添加到等待队列
                if task_id not in self.task_queue:
                    self.task_queue.append(task_id)
                task.update_status(DownloadStatus.WAITING)
                
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
                    
                return True
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.tasks or task_id not in self.downloaders:
                return False
                
            task = self.tasks[task_id]
            downloader = self.downloaders[task_id]
            
            # 如果任务正在下载，暂停它
            if task.status == DownloadStatus.DOWNLOADING:
                downloader.pause()
                self.active_downloads -= 1
                return True
                
            # 如果任务在等待，从队列中移除
            elif task.status == DownloadStatus.WAITING:
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)
                task.update_status(DownloadStatus.PAUSED)
                
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
                    
                return True
                
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢复下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.tasks or task_id not in self.downloaders:
                return False
                
            task = self.tasks[task_id]
            downloader = self.downloaders[task_id]
            
            # 只有暂停的任务才能恢复
            if task.status != DownloadStatus.PAUSED:
                return False
                
            # 如果可以立即恢复
            if self.active_downloads < self.max_concurrent_downloads:
                self.active_downloads += 1
                downloader.resume()
                return True
            else:
                # 添加到等待队列
                if task_id not in self.task_queue:
                    self.task_queue.append(task_id)
                task.update_status(DownloadStatus.WAITING)
                
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
                    
                return True
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.tasks or task_id not in self.downloaders:
                return False
                
            task = self.tasks[task_id]
            downloader = self.downloaders[task_id]
            
            # 如果任务在等待队列中，移除
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
                
            # 如果任务正在下载，减少活动下载数
            if task.status == DownloadStatus.DOWNLOADING:
                self.active_downloads -= 1
                
            # 取消下载
            downloader.cancel()
            
            return True
    
    def remove_task(self, task_id: str, delete_file: bool = False) -> bool:
        """
        移除下载任务
        
        Args:
            task_id: 任务ID
            delete_file: 是否删除已下载的文件
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            # 先取消任务
            if task_id in self.downloaders:
                self.cancel_task(task_id)
                
            # 删除文件
            if delete_file:
                task = self.tasks[task_id]
                if os.path.exists(task.file_path):
                    try:
                        os.remove(task.file_path)
                    except Exception:
                        pass
                        
            # 移除任务和下载器
            if task_id in self.downloaders:
                del self.downloaders[task_id]
            del self.tasks[task_id]
            
            # 回调通知
            if self.on_task_removed:
                self.on_task_removed(task_id)
                
            return True
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务信息"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())
    
    def pause_all(self):
        """暂停所有下载"""
        with self.lock:
            for task_id in list(self.tasks.keys()):
                self.pause_task(task_id)
    
    def resume_all(self):
        """恢复所有下载"""
        with self.lock:
            for task_id, task in self.tasks.items():
                if task.status == DownloadStatus.PAUSED:
                    self.resume_task(task_id)
    
    def cancel_all(self):
        """取消所有下载"""
        with self.lock:
            for task_id in list(self.tasks.keys()):
                self.cancel_task(task_id)
    
    def set_max_concurrent_downloads(self, count: int):
        """设置最大并行下载数"""
        with self.lock:
            self.max_concurrent_downloads = max(1, count)
            
            # 处理队列，可能有新的下载可以开始
            self._process_queue()
    
    def _start_queue_processor(self):
        """启动队列处理线程"""
        self.is_queue_running = True
        threading.Thread(
            target=self._queue_processor, 
            daemon=True
        ).start()
    
    def _queue_processor(self):
        """队列处理线程"""
        while self.is_queue_running:
            self._process_queue()
            time.sleep(1)  # 每秒检查一次队列
    
    def _process_queue(self):
        """处理下载队列"""
        with self.lock:
            # 如果没有等待的任务或已达到最大并行下载数，直接返回
            if not self.task_queue or self.active_downloads >= self.max_concurrent_downloads:
                return
                
            # 处理等待任务
            while self.task_queue and self.active_downloads < self.max_concurrent_downloads:
                task_id = self.task_queue[0]
                self.task_queue.pop(0)
                
                if task_id in self.tasks and task_id in self.downloaders:
                    task = self.tasks[task_id]
                    downloader = self.downloaders[task_id]
                    
                    # 根据任务状态进行处理
                    if task.status == DownloadStatus.WAITING:
                        self.active_downloads += 1
                        task.update_status(DownloadStatus.DOWNLOADING)
                        
                        if self.on_task_status_changed:
                            self.on_task_status_changed(task)
                            
                        downloader.start()
                    elif task.status == DownloadStatus.PAUSED:
                        self.active_downloads += 1
                        downloader.resume()
    
    def _on_progress_callback(self, task: DownloadTask):
        """下载进度回调"""
        if self.on_task_progress:
            self.on_task_progress(task)
    
    def _on_complete_callback(self, task: DownloadTask):
        """下载完成回调"""
        with self.lock:
            if task.task_id in self.tasks:
                self.active_downloads -= 1
                
                # 处理队列中的下一个任务
                self._process_queue()
                
                # 状态回调
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
    
    def _on_error_callback(self, task: DownloadTask, error_msg: str):
        """下载错误回调"""
        with self.lock:
            if task.task_id in self.tasks:
                self.active_downloads -= 1
                
                # 处理队列中的下一个任务
                self._process_queue()
                
                # 状态回调
                if self.on_task_status_changed:
                    self.on_task_status_changed(task)
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.is_queue_running = False
        if hasattr(self, 'lock'):
            self.pause_all()  # 暂停所有下载

    def get_eta(self, task):
        """获取预计剩余时间"""
        if task.speed <= 0 or task.total_size <= 0:
            return "未知"
            
        remaining_bytes = task.total_size - task.downloaded_size
        remaining_seconds = remaining_bytes / task.speed
        
        if remaining_seconds < 60:
            return f"{int(remaining_seconds)}秒"
        elif remaining_seconds < 3600:
            return f"{int(remaining_seconds / 60)}分钟"
        else:
            hours = int(remaining_seconds / 3600)
            minutes = int((remaining_seconds % 3600) / 60)
            return f"{hours}小时{minutes}分钟"
            
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.2f}MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.2f}GB"
            
    def format_speed(self, task):
        """格式化下载速度"""
        if task.speed < 1024:
            return f"{task.speed:.1f}B/s"
        elif task.speed < 1024 * 1024:
            return f"{task.speed/1024:.1f}KB/s"
        else:
            return f"{task.speed/(1024*1024):.2f}MB/s"
            
    def to_dict(self, task):
        """转换为字典格式"""
        return {
            "task_id": task.task_id,
            "url": task.url,
            "filename": task.get_file_name(),
            "status": task.status.value,
            "progress": task.progress,
            "total_size": self.format_size(task.total_size),
            "downloaded_size": self.format_size(task.downloaded_size),
            "speed": self.format_speed(task),
            "eta": self.get_eta(task) if task.status == 'downloading' else "",
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.start_time)),
            "error_message": task.error
        }

    def get_task_count(self):
        """获取各种状态的任务数量"""
        counts = {status.value: 0 for status in DownloadStatus}
        counts["total"] = 0
        
        with self.lock:
            for task in self.tasks.values():
                counts[task.status.value] += 1
                counts["total"] += 1
                
        return counts