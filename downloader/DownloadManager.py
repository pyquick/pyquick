from .downloader import Downloader
import os
import time
import threading
import uuid
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
from .DownloadTask import DownloadStatus
from .MultiThreadDownloader import MultiThreadDownloader

# 尝试导入日志系统，如果不存在则使用标准日志
try:
    from log import download_logger, error_logger
except ImportError:
    # 使用标准日志模块作为后备
    download_logger = logging.getLogger("download")
    error_logger = logging.getLogger("error")

class TaskStatus(Enum):
    """下载任务状态"""
    WAITING = "waiting"      # 等待中
    DOWNLOADING = "downloading"  # 下载中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 错误
    CANCELLED = "cancelled"  # 已取消
    CONNECTING = "connecting"  # 连接中

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
        self.total_size = 0      # 文件总大小
        self.downloaded_size = 0 # 已下载大小
        self._last_update_time = time.time() # 添加最后更新时间
        
        # 速度计算相关属性
        self._last_downloaded_size = 0
        self._last_size_update_time = time.time()
        self._speed_history = []  # 速度历史记录，用于平滑速度显示

    def update_status(self, status, error=""):
        """更新任务状态"""
        self.status = status
        if error:
            self.error = error
        self.notify_callbacks()

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
                    download_logger.error(f"回调错误: {e}")

    def on_progress(self, progress, speed, status):
        """进度更新回调"""
        current_time = time.time()
        self.progress = progress
        self.speed = speed
        
        # 如果状态发生变化，则更新任务状态
        if status != self.status:
            self.status = status
            if status == 'completed':
                self.end_time = time.time()
            elif status == 'error' and self.downloader:
                self.error = self.downloader.error
                
        # 更新下载和总大小（如果有downloader）
        if self.downloader:
            if hasattr(self.downloader, 'total_size') and self.downloader.total_size > 0:
                self.total_size = self.downloader.total_size
            if hasattr(self.downloader, 'downloaded_size') and self.downloader.downloaded_size >= 0:
                self.downloaded_size = self.downloader.downloaded_size
                
        # 节流控制：每100ms最多通知一次回调
        if hasattr(self, '_last_notify_time'):
            if current_time * 1000 - self._last_notify_time < 100:
                return
        
        self._last_notify_time = current_time * 1000
        # 通知回调
        self.notify_callbacks()

    def start(self):
        """开始下载任务"""
        if not self.downloader:
            self.downloader = Downloader(
                url=self.url,
                file_path=self.file_path,
                num_threads=self.thread_count,
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
            download_logger.info(f"开始下载任务: {self.task_id}, URL: {self.url}")
            self.downloader.start()
        except Exception as e:
            error_msg = str(e)
            error_logger.error(f"下载任务 {self.task_id} 出错: {error_msg}")
            self.status = 'error'
            self.error = error_msg
            self.notify_callbacks()

    def pause(self):
        """暂停下载任务"""
        if self.downloader and self.status == 'downloading':
            download_logger.info(f"暂停下载任务: {self.task_id}")
            self.downloader.pause()
            self.status = 'paused'
            self.notify_callbacks()
            return True
        return False

    def resume(self):
        """恢复下载任务"""
        if self.downloader and self.status == 'paused':
            download_logger.info(f"恢复下载任务: {self.task_id}")
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
            download_logger.info(f"取消下载任务: {self.task_id}")
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

    def get_eta(self):
        """获取预计剩余时间（秒）"""
        if self.speed <= 0 or self.total_size <= 0 or self.downloaded_size >= self.total_size:
            return 0
            
        remaining_bytes = self.total_size - self.downloaded_size
        return remaining_bytes / self.speed

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
            "status": self.status,
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
                num_threads_per_download=4, on_task_status_changed=None, status_callback=None, on_task_progress=None):
        """初始化下载管理器
        
        优化参数:
        - max_concurrent_downloads: 并发下载数从3降为2，减少系统负载
        - num_threads_per_download: 每个下载的线程数从5降为4，平衡性能与资源占用
        
        Args:
            task_db_path: 任务数据库路径
            max_concurrent_downloads: 最大并发下载数
            num_threads_per_download: 每个下载的线程数
            on_task_status_changed: 任务状态变化回调
            status_callback: 状态回调函数
            on_task_progress: 下载进度回调函数
        """
        self.tasks: Dict[str, DownloadTask] = {}  # 任务字典 {任务ID: 任务对象}
        # self.downloaders dictionary removed - DownloadTask manages its own downloader
        self.max_concurrent_downloads = max_concurrent_downloads
        self.num_threads_per_download = num_threads_per_download
        self.on_task_status_changed = on_task_status_changed
        self.status_callback = status_callback
        self.on_task_progress = on_task_progress  # 添加进度回调属性
        
        # 任务队列
        self.task_queue = []  # 待处理任务队列
        self.active_tasks = []  # 活跃任务队列
        self.completed_tasks = []  # 已完成任务队列
        self.waiting_queue = []  # 等待中的任务队列
        
        # 线程同步
        self.lock = threading.RLock()
        self.queue_event = threading.Event()
        
        # 启动队列处理线程
        self.queue_thread = None
        self._start_queue_processor()
        
        # 启动任务监控线程
        self.monitoring = True
        self._start_task_monitor()
        
        download_logger.info(f"下载管理器初始化: 最大并发={max_concurrent_downloads}, 线程数={num_threads_per_download}")
    
    def _start_task_monitor(self):
        """启动任务监控线程"""
        monitor_thread = threading.Thread(
            target=self._monitor_tasks,
            daemon=True
        )
        monitor_thread.start()
        download_logger.info("任务监控线程已启动")
    
    def _monitor_tasks(self):
        """监控所有活动任务的状态和进度"""
        while self.monitoring:
            try:
                with self.lock:
                    # 定期检查队列处理
                    self._process_queue()
                    
                    # 输出任务状态概览，帮助调试
                    active_count = len(self.active_tasks)
                    waiting_count = len(self.waiting_queue)
                    download_logger.info(f"任务监控 - 活动任务: {active_count}/{self.max_concurrent_downloads}, 等待任务: {waiting_count}")
                    
                    # 检查活动任务
                    for task_id in list(self.active_tasks):
                        if task_id in self.tasks:
                            task = self.tasks[task_id]
                            
                            # 检查任务是否有downloader
                            if hasattr(task, 'downloader') and task.downloader:
                                # 获取downloader的属性更新任务
                                if hasattr(task.downloader, 'total_size') and task.downloader.total_size > 0:
                                    task.total_size = task.downloader.total_size
                                    download_logger.debug(f"更新任务 {task_id} 总大小: {task.total_size/1024/1024:.2f}MB")
                                
                                if hasattr(task.downloader, 'downloaded_size') and task.downloader.downloaded_size >= 0:
                                    # 计算前后下载量差值，用于计算速度
                                    now = time.time()
                                    if hasattr(task, '_last_size_update_time') and hasattr(task, '_last_downloaded_size'):
                                        time_diff = now - task._last_size_update_time
                                        size_diff = task.downloader.downloaded_size - task._last_downloaded_size
                                        
                                        if time_diff > 0 and size_diff >= 0:
                                            # 计算当前速度
                                            current_speed = size_diff / time_diff
                                            
                                            # 记录到速度历史
                                            task._speed_history.append(current_speed)
                                            # 保持历史记录长度
                                            if len(task._speed_history) > 5:
                                                task._speed_history.pop(0)
                                                
                                            # 计算平滑速度
                                            if task._speed_history:
                                                task.speed = sum(task._speed_history) / len(task._speed_history)
                                                
                                            # 更新进度
                                            if task.total_size > 0:
                                                task.progress = min(100.0, (task.downloader.downloaded_size / task.total_size) * 100)
                                            
                                            # 调试日志
                                            if task.speed > 0:
                                                download_logger.debug(f"任务 {task_id} - 当前速度: {current_speed/1024/1024:.2f}MB/s, 平均速度: {task.speed/1024/1024:.2f}MB/s, 进度: {task.progress:.1f}%")
                                    
                                    # 更新上次下载大小和时间
                                    task._last_downloaded_size = task.downloader.downloaded_size
                                    task._last_size_update_time = now
                                    task.downloaded_size = task.downloader.downloaded_size
                                
                                # 更新任务状态
                                progress_updated = False
                                if hasattr(task.downloader, 'status'):
                                    downloader_status = task.downloader.status
                                    if downloader_status != task.status:
                                        task.update_status(downloader_status)
                                        download_logger.info(f"更新任务 {task_id} 状态: {task.status}")
                        
                            # 记录任务状态
                            download_logger.info(f"监控任务: {task_id}, 状态: {task.status}, 进度: {task.progress:.1f}%, 速度: {task.speed/1024/1024:.2f}MB/s, 大小: {task.downloaded_size}/{task.total_size}")
                                    
                        else:
                            # 任务不存在，从活动队列中移除
                            error_logger.warning(f"任务 {task_id} 在活动队列但不在tasks字典中，移除")
                            self.active_tasks.remove(task_id)
                
                # 暂停监控线程，减少资源占用
                time.sleep(1)
                
            except Exception as e:
                error_logger.error(f"监控任务异常: {str(e)}")
                time.sleep(2)  # 发生异常时增加延迟
    
    def add_task(self, url: str, file_path: str, thread_count: int = None, 
               proxies: Optional[Dict[str, str]] = None) -> str:
        """添加下载任务
        
        Args:
            url: 下载URL
            file_path: 文件保存路径
            thread_count: 下载线程数
            proxies: 代理配置
            
        Returns:
            任务ID
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 如果未指定线程数，使用默认值
            if thread_count is None:
                thread_count = self.num_threads_per_download
                
            # 创建下载任务
            task = DownloadTask(
                url=url,
                file_path=file_path,
                task_id=task_id,
                thread_count=thread_count,
                proxies=proxies
            )
            
            # 注册回调 - 使用正确的回调函数名
            if hasattr(self, '_on_progress_callback') and callable(self._on_progress_callback):
                task.register_callback(self._on_progress_callback)

            # 将任务添加到管理器和等待队列
            with self.lock:
                self.tasks[task_id] = task
                # Add to waiting queue, status will be updated later
                if task_id not in self.waiting_queue:
                     self.waiting_queue.append(task_id)
                task.update_status(TaskStatus.WAITING.value) # Set initial status

            download_logger.info(f"添加下载任务：{task_id}, URL: {url}, Status: {task.status}")

            return task_id
            
        except Exception as e:
            error_logger.error(f"添加下载任务失败: {str(e)}")
            raise Exception(f"添加下载任务失败: {str(e)}")
    
    def start_task(self, task_id: str) -> bool:
        """
        开始下载任务
        
        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功启动或加入等待队列
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                error_logger.error(f"启动任务失败: 任务 {task_id} 不存在于 tasks 字典")
                return False

            # 如果任务已经在运行，直接返回成功
            if task.status == TaskStatus.DOWNLOADING.value:
                download_logger.info(f"任务 {task_id} 已在下载中，无需启动")
                return True
                
            # 如果任务已完成或取消，无法再次启动
            if task.status in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]:
                download_logger.warning(f"任务 {task_id} 状态为 {task.status}，无法启动")
                return False

            # 检查是否可以立即开始
            if len(self.active_tasks) < self.max_concurrent_downloads:
                download_logger.info(f"尝试立即启动任务: {task_id}")
                
                # 从等待队列移除(如果在里面)
                if task_id in self.waiting_queue:
                    self.waiting_queue.remove(task_id)
                    
                # 添加到活动任务列表
                if task_id not in self.active_tasks:
                    self.active_tasks.append(task_id)
                
                try:
                    # 更新状态为connecting
                    task.update_status(TaskStatus.CONNECTING.value)
                    
                    if self.on_task_status_changed:
                        try:
                            self.on_task_status_changed(task)
                        except Exception as cb_err:
                            error_logger.error(f"任务状态回调失败: {cb_err}")
                    
                    # 启动下载 - 使用新的方法
                    self._start_download_task(task)
                    download_logger.info(f"成功启动任务: {task_id}")
                    return True
                    
                except Exception as e:
                    error_logger.error(f"启动任务 {task_id} 失败: {str(e)}")
                    # 移除出活动队列
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                    # 更新状态为错误
                    task.update_status(TaskStatus.ERROR.value, str(e))
                    return False
            else:
                # 添加到等待队列
                if task_id not in self.waiting_queue:
                    self.waiting_queue.append(task_id)
                # 更新状态为等待
                if task.status != TaskStatus.WAITING.value:
                    task.update_status(TaskStatus.WAITING.value)
                    
                    if self.on_task_status_changed:
                        try:
                            self.on_task_status_changed(task)
                        except Exception as cb_err:
                            error_logger.error(f"等待任务状态回调失败: {cb_err}")
                            
                download_logger.info(f"并发数已满，任务 {task_id} 添加到等待队列")
                return True
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停下载任务
        
        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功暂停
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                error_logger.error(f"暂停任务失败: 任务 {task_id} 不存在")
                return False

            # 如果任务正在下载，调用 task.pause()
            if task.status == TaskStatus.DOWNLOADING.value:
                if task.pause(): # task.pause updates status and calls callbacks
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                    download_logger.info(f"暂停下载任务: {task_id}")
                    self._process_queue() # Check if a waiting task can start
                    return True
                else:
                    error_logger.error(f"调用 task.pause() 失败 for {task_id}")
                    return False

            # 如果任务在等待，从队列中移除并标记为暂停
            elif task.status == TaskStatus.WAITING.value:
                if task_id in self.waiting_queue:
                    self.waiting_queue.remove(task_id)
                task.update_status(TaskStatus.PAUSED.value) # Manually update status
                download_logger.info(f"从等待队列移除并标记为暂停: {task_id}")
                # Trigger status change callback if needed
                if self.on_task_status_changed:
                     try:
                         self.on_task_status_changed(task)
                     except Exception as cb_err:
                         error_logger.error(f"暂停等待任务状态回调失败 for {task_id}: {cb_err}")
                return True
                
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢复下载任务
        
        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功恢复或加入等待队列
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                error_logger.error(f"恢复任务失败: 任务 {task_id} 不存在")
                return False

            # 只有暂停的任务才能恢复
            if task.status != TaskStatus.PAUSED.value:
                download_logger.warning(f"任务 {task_id} 状态为 {task.status}，无法恢复")
                return False

            # 检查是否可以立即开始
            if len(self.active_tasks) < self.max_concurrent_downloads:
                download_logger.info(f"尝试立即恢复任务: {task_id}")
                
                # 添加到活动任务列表
                if task_id not in self.active_tasks:
                    self.active_tasks.append(task_id)
                
                try:
                    # 更新状态为connecting
                    task.update_status(TaskStatus.CONNECTING.value)
                    
                    if self.on_task_status_changed:
                        try:
                            self.on_task_status_changed(task)
                        except Exception as cb_err:
                            error_logger.error(f"恢复任务状态回调失败: {cb_err}")
                    
                    # 恢复下载 - 使用辅助方法
                    self._start_download_task(task)
                    download_logger.info(f"成功恢复任务: {task_id}")
                    return True
                    
                except Exception as e:
                    error_logger.error(f"恢复任务 {task_id} 失败: {str(e)}")
                    # 移除出活动队列
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                    # 更新状态为错误
                    task.update_status(TaskStatus.ERROR.value, str(e))
                    return False
            else:
                # 添加到等待队列
                if task_id not in self.waiting_queue:
                    self.waiting_queue.append(task_id)
                # 更新状态为等待
                task.update_status(TaskStatus.WAITING.value)
                
                if self.on_task_status_changed:
                    try:
                        self.on_task_status_changed(task)
                    except Exception as cb_err:
                        error_logger.error(f"暂停任务切换到等待状态回调失败: {cb_err}")
                        
                download_logger.info(f"并发数已满，恢复的任务 {task_id} 添加到等待队列")
                return True

    def cancel_task(self, task_id: str) -> bool:
        """
        取消下载任务
        
        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                error_logger.error(f"取消任务失败: 任务 {task_id} 不存在")
                return False

            original_status = task.status

            # 调用 task.cancel() - this handles downloader cancellation and status update
            if task.cancel():
                download_logger.info(f"取消下载任务: {task_id}")

                # 从活动或等待队列中移除
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                if task_id in self.waiting_queue:
                    self.waiting_queue.remove(task_id)

                # 如果任务之前是活动的，尝试启动下一个等待的任务
                if original_status == TaskStatus.DOWNLOADING.value:
                    self._process_queue()

                return True
            else:
                # task.cancel() might return False if already completed/cancelled/error
                download_logger.warning(f"调用 task.cancel() 未成功 for {task_id} (可能已完成或取消)")
                # Still remove from queues if present
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                if task_id in self.waiting_queue:
                    self.waiting_queue.remove(task_id)
                # Ensure status is CANCELLED if possible
                if task.status not in [TaskStatus.COMPLETED.value, TaskStatus.ERROR.value]:
                     task.update_status(TaskStatus.CANCELLED.value)
                return False # Indicate that the task wasn't actively cancelled now
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
                download_logger.error(f"移除任务失败: 任务 {task_id} 不存在")
                return False
                
            # 先尝试取消任务 (idempotent)
            self.cancel_task(task_id)

            task = self.tasks.get(task_id) # Re-get task in case cancel_task modified it

            # 删除文件
            if task and delete_file:
                if os.path.exists(task.file_path):
                    try:
                        os.remove(task.file_path)
                        download_logger.info(f"删除文件: {task.file_path}")
                    except Exception as e:
                        error_logger.error(f"删除文件失败 {task.file_path}: {e}")

            # 移除任务引用
            if task_id in self.tasks:
                del self.tasks[task_id]
                # Remove from queues just in case
                if task_id in self.active_tasks: self.active_tasks.remove(task_id)
                if task_id in self.waiting_queue: self.waiting_queue.remove(task_id)

                # 回调通知 (Consider if a specific 'removed' callback is needed)
                # if self.on_task_removed:
                #     self.on_task_removed(task_id)

                download_logger.info(f"移除下载任务引用: {task_id}")
            if delete_file:
                task = self.tasks[task_id]
                if os.path.exists(task.file_path):
                    try:
                        os.remove(task.file_path)
                        download_logger.info(f"删除文件: {task.file_path}")
                    except Exception as e:
                        error_logger.error(f"删除文件失败 {task.file_path}: {e}")
                        
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
        download_logger.info("暂停所有下载任务")
        with self.lock:
            for task_id in list(self.tasks.keys()):
                self.pause_task(task_id)
    
    def resume_all(self):
        """恢复所有下载"""
        download_logger.info("恢复所有暂停的下载任务")
        with self.lock:
            for task_id, task in self.tasks.items():
                if task.status == DownloadStatus.PAUSED:
                    self.resume_task(task_id)
    
    def cancel_all(self):
        """取消所有任务"""
        with self.lock:
            tasks_to_cancel = list(self.tasks.keys())  # 创建副本，避免在循环中修改字典
            
            cancel_count = 0
            for task_id in tasks_to_cancel:
                try:
                    # 可以先尝试暂停任务，然后取消
                    if self.pause_task(task_id):
                        time.sleep(0.1)  # 给暂停一点时间
                    
                    # 现在取消任务
                    if self.cancel_task(task_id):
                        cancel_count += 1
                except Exception as e:
                    error_logger.error(f"取消任务 {task_id} 失败: {e}")
            
            # 清理任务列表
            self.active_tasks = []
            self.waiting_queue = []
            
            download_logger.info(f"已取消 {cancel_count} 个下载任务")
            return cancel_count
    
    def set_max_concurrent_downloads(self, count: int):
        """设置最大并行下载数"""
        with self.lock:
            old_value = self.max_concurrent_downloads
            self.max_concurrent_downloads = max(1, count)
            download_logger.info(f"设置最大并发下载数: {old_value} -> {self.max_concurrent_downloads}")
            
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
            # 添加日志用于调试
            download_logger.info(f"处理队列: 活动任务数={len(self.active_tasks)}, 等待任务数={len(self.waiting_queue)}")
            
            # 先检查是否有空闲插槽
            if len(self.active_tasks) >= self.max_concurrent_downloads:
                download_logger.info("处理队列: 当前活动任务数已达最大值，无法启动新任务")
                return

            # 如果没有等待的任务，直接返回
            if not self.waiting_queue:
                download_logger.info("处理队列: 没有等待中的任务")
                return
                
            # 尝试启动等待队列中的任务
            tasks_started = 0
            # 获取等待队列副本，避免迭代过程中修改原队列
            waiting_queue_copy = list(self.waiting_queue)
            
            for task_id in waiting_queue_copy:
                # 再次检查是否达到最大并发数
                if len(self.active_tasks) >= self.max_concurrent_downloads:
                    download_logger.info("处理队列: 已达最大并发数，停止启动更多任务")
                    break 

                task = self.tasks.get(task_id)
                if not task:
                    # 任务不存在，从等待队列移除
                    download_logger.warning(f"处理队列: 任务 {task_id} 在等待队列但不在 tasks 字典中，将其移除")
                    if task_id in self.waiting_queue:
                        self.waiting_queue.remove(task_id)
                    continue
                    
                if task.status != TaskStatus.WAITING.value:
                    # 任务状态不是等待中，从等待队列移除
                    download_logger.warning(f"处理队列: 任务 {task_id} 在等待队列但状态为 {task.status}，将其移除")
                    if task_id in self.waiting_queue:
                        self.waiting_queue.remove(task_id)
                    continue
                
                download_logger.info(f"处理队列: 尝试启动等待中的任务 {task_id}")
                
                # 从等待队列移除
                if task_id in self.waiting_queue:
                    self.waiting_queue.remove(task_id)
                
                # 添加到活动队列
                if task_id not in self.active_tasks:
                    self.active_tasks.append(task_id)
                
                # 启动任务
                try:
                    # 先将状态更新为connecting
                    task.update_status(TaskStatus.CONNECTING.value)
                    
                    # 启动下载
                    self._start_download_task(task)
                    tasks_started += 1
                    
                    # 通知状态变化
                    if self.on_task_status_changed:
                        self.on_task_status_changed(task)
                        
                    download_logger.info(f"成功启动任务 {task_id}")
                except Exception as e:
                    error_logger.error(f"启动任务 {task_id} 失败: {str(e)}")
                    # 启动失败，将任务从活动队列中移除
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                    # 更新状态为错误
                    task.update_status(TaskStatus.ERROR.value, str(e))
                    continue

            if tasks_started > 0:
                download_logger.info(f"处理队列: 启动了 {tasks_started} 个等待中的任务")
                
    def _start_download_task(self, task):
        """启动下载任务(内部方法)"""
        # 这个辅助方法负责创建和启动下载器
        try:
            from . import downloader
            
            # 如果是恢复暂停的任务
            if task.status == TaskStatus.PAUSED.value:
                # 处理恢复逻辑
                if task.downloader:
                    task.downloader.resume(task.task_id)
                    task.update_status(TaskStatus.DOWNLOADING.value)
                    download_logger.info(f"恢复暂停的任务 {task.task_id}")
                else:
                    # 如果没有downloader,需要重新创建一个
                    download_logger.info(f"暂停的任务没有downloader,重新创建: {task.task_id}")
                    self._create_new_download(task)
            else:
                # 新任务，创建下载器
                self._create_new_download(task)
                
        except Exception as e:
            error_logger.error(f"启动下载任务失败: {str(e)}")
            raise
    
    def _create_new_download(self, task):
        """创建新的下载器实例"""
        from . import downloader
        
        # 设置回调函数
        def progress_callback(downloaded, total, speed):
            # 更新任务进度
            try:
                # 确保update_progress方法存在
                if hasattr(task, 'update_progress'):
                    task.update_progress(downloaded, total, speed)
                else:
                    # 备用方案：如果方法不存在，则直接更新属性
                    task.downloaded_size = downloaded
                    task.content_length = total 
                    task.speed = speed
                    if total > 0:
                        task.progress = min(100.0, (downloaded / total) * 100)
                    task._notify_callbacks() if hasattr(task, '_notify_callbacks') else None
                
                # 通知管理器 - 安全检查
                if hasattr(self, '_on_progress_callback') and callable(self._on_progress_callback):
                    try:
                        self._on_progress_callback(task)
                    except Exception as e:
                        error_logger.error(f"通知进度回调函数失败: {e}")
            except Exception as e:
                error_logger.error(f"更新进度时出错: {e}")
                
        def complete_callback(file_path=None, total_size=0, speed=0):
            # 更新任务状态为完成
            task.update_status(TaskStatus.COMPLETED.value)
            # 通知管理器 - 安全检查
            if hasattr(self, '_on_complete_callback') and callable(self._on_complete_callback):
                try:
                    self._on_complete_callback(task)
                except Exception as e:
                    error_logger.error(f"通知完成回调函数失败: {e}")
                
        def error_callback(error_msg):
            # 更新任务状态为错误
            task.update_status(TaskStatus.ERROR.value, error_msg)
            # 通知管理器 - 安全检查
            if hasattr(self, '_on_error_callback') and callable(self._on_error_callback):
                try:
                    self._on_error_callback(task, error_msg)
                except Exception as e:
                    error_logger.error(f"通知错误回调函数失败: {e}")
                
        # 启动下载
        try:
            download_id = downloader.download_file(
                url=task.url,
                save_path=task.file_path,
                headers=None,  # 可以根据需要添加头信息
                proxy=task.proxies,
                on_progress=progress_callback,
                on_complete=complete_callback,
                on_error=error_callback,
                num_connections=task.thread_count,
                resume=True
            )
            
            # 保存downloader返回的ID
            task.downloader_id = download_id
            
            # 更新任务状态为下载中
            task.update_status(TaskStatus.DOWNLOADING.value)
            download_logger.info(f"创建新下载任务: {task.task_id}, 下载器ID: {download_id}")
            return download_id
        except Exception as e:
            error_logger.error(f"创建下载任务失败: {str(e)}")
            task.update_status(TaskStatus.ERROR.value, str(e))
            raise

    def _on_progress_callback(self, task: DownloadTask):
        """下载进度回调"""
        # 节流控制，减少不必要的回调
        if hasattr(self, '_last_progress_time'):
            current_time = time.time()
            if current_time - self._last_progress_time < 0.1:  # 每100ms最多更新一次
                return
            self._last_progress_time = current_time
        else:
            self._last_progress_time = time.time()
            
        # 增加对on_task_progress属性的检查
        if hasattr(self, 'on_task_progress') and self.on_task_progress is not None and callable(self.on_task_progress):
            try:
                self.on_task_progress(task)
            except Exception as e:
                error_logger.error(f"调用进度回调函数失败: {e}")
        else:
            # 如果没有设置进度回调函数，使用任务状态变化回调
            if hasattr(self, 'on_task_status_changed') and self.on_task_status_changed is not None and callable(self.on_task_status_changed):
                try:
                    self.on_task_status_changed(task)
                except Exception as e:
                    error_logger.error(f"调用状态变化回调函数失败: {e}")
    
    def _on_complete_callback(self, task: DownloadTask):
        """下载完成回调"""
        with self.lock:
            if task.task_id in self.tasks:
                # 从活动任务列表移除
                if task.task_id in self.active_tasks:
                    self.active_tasks.remove(task.task_id)
                else:
                     # Task completed but wasn't in active_tasks? Log warning.
                     download_logger.warning(f"任务 {task.task_id} 完成但不在 active_tasks 列表中")

                download_logger.info(f"下载任务完成: {task.task_id}")

                # 处理队列中的下一个任务
                self._process_queue()
                
                # 状态回调
                if hasattr(self, 'on_task_status_changed') and self.on_task_status_changed is not None and callable(self.on_task_status_changed):
                    try:
                        self.on_task_status_changed(task)
                    except Exception as e:
                        error_logger.error(f"完成回调中调用状态变化回调函数失败: {e}")
    
    def _on_error_callback(self, task: DownloadTask, error_msg: str):
        """下载错误回调"""
        with self.lock:
            if task.task_id in self.tasks:
                 # 从活动任务列表移除
                if task.task_id in self.active_tasks:
                    self.active_tasks.remove(task.task_id)
                else:
                    # Task errored but wasn't in active_tasks? Log warning.
                    download_logger.warning(f"任务 {task.task_id} 出错但不在 active_tasks 列表中")

                error_logger.error(f"下载任务错误: {task.task_id}, {error_msg}")

                # 处理队列中的下一个任务
                self._process_queue()
                
                # 状态回调
                if hasattr(self, 'on_task_status_changed') and self.on_task_status_changed is not None and callable(self.on_task_status_changed):
                    try:
                        self.on_task_status_changed(task)
                    except Exception as e:
                        error_logger.error(f"错误回调中调用状态变化回调函数失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.monitoring = False  # 停止监控线程
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
        status_str = task.status
        if isinstance(task.status, Enum):
            status_str = task.status.value
            
        return {
            "task_id": task.task_id,
            "url": task.url,
            "filename": task.get_file_name(),
            "status": status_str,
            "progress": task.progress,
            "total_size": self.format_size(task.total_size),
            "downloaded_size": self.format_size(task.downloaded_size),
            "speed": self.format_speed(task),
            "eta": self.get_eta(task) if task.status == 'downloading' else "",
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.start_time) if task.start_time else time.time()),
            "error_message": task.error
        }

    def get_task_count(self):
        """获取各种状态的任务数量"""
        counts = {status.value: 0 for status in DownloadStatus}
        counts["total"] = 0
        
        with self.lock:
            for task in self.tasks.values():
                status = task.status
                if isinstance(status, Enum):
                    status = status.value
                elif isinstance(status, str):
                    status = status
                
                if status in counts:
                    counts[status] += 1
                counts["total"] += 1
                
        return counts
        
    def get_progress(self, task_id: str) -> float:
        """
        获取下载进度百分比
        
        Args:
            task_id: 任务ID
            
        Returns:
            float: 进度百分比 (0-100)
        """
        task = self.get_task(task_id)
        if not task:
            return 0.0
            
        return task.progress
