"""
下载管理器，负责管理多个下载任务
"""

import os
import time
import json
import threading
import multiprocessing
from typing import Dict, List, Optional, Callable, Tuple, Any, Union
import uuid

from .downloader import Downloader

class DownloadTask:
    """下载任务类，封装单个下载任务的信息"""
    
    def __init__(self, 
                 task_id: str,
                 url: str,
                 file_path: str,
                 file_name: str,
                 total_size: int = 0,
                 downloader: Optional[Downloader] = None,
                 status: str = "pending",
                 progress: float = 0.0,
                 speed: float = 0.0,
                 create_time: float = 0.0,
                 start_time: float = 0.0,
                 finish_time: float = 0.0,
                 error: Optional[str] = None):
        """
        初始化下载任务
        
        参数:
            task_id: 任务ID
            url: 下载URL
            file_path: 保存路径
            file_name: 文件名
            total_size: 文件总大小
            downloader: 下载器实例
            status: 状态 (pending, downloading, paused, completed, cancelled, error)
            progress: 下载进度
            speed: 下载速度
            create_time: 创建时间
            start_time: 开始时间
            finish_time: 完成时间
            error: 错误信息
        """
        self.task_id = task_id
        self.url = url
        self.file_path = file_path
        self.file_name = file_name
        self.total_size = total_size
        self.downloader = downloader
        self.status = status
        self.progress = progress
        self.speed = speed
        self.create_time = create_time
        self.start_time = start_time
        self.finish_time = finish_time
        self.error = error
        
    def to_dict(self) -> Dict:
        """转换为字典表示"""
        return {
            'task_id': self.task_id,
            'url': self.url,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'total_size': self.total_size,
            'status': self.status,
            'progress': self.progress,
            'speed': self.speed,
            'create_time': self.create_time,
            'start_time': self.start_time,
            'finish_time': self.finish_time,
            'error': self.error
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'DownloadTask':
        """从字典创建任务"""
        return cls(
            task_id=data.get('task_id', ''),
            url=data.get('url', ''),
            file_path=data.get('file_path', ''),
            file_name=data.get('file_name', ''),
            total_size=data.get('total_size', 0),
            status=data.get('status', 'pending'),
            progress=data.get('progress', 0.0),
            speed=data.get('speed', 0.0),
            create_time=data.get('create_time', 0.0),
            start_time=data.get('start_time', 0.0),
            finish_time=data.get('finish_time', 0.0),
            error=data.get('error')
        )

class DownloadManager:
    """下载管理器，管理多个下载任务，支持暂停、恢复、取消等操作"""
    
    def __init__(self, 
                 task_db_path: str = None,
                 max_concurrent_downloads: int = 3,
                 num_threads_per_download: int = 8,
                 on_task_status_changed: Optional[Callable[[str, str], None]] = None):
        """
        初始化下载管理器
        
        参数:
            task_db_path: 任务数据库路径，用于持久化下载任务
            max_concurrent_downloads: 最大并发下载数
            num_threads_per_download: 每个下载任务的线程数
            on_task_status_changed: 任务状态变化回调函数，参数为(task_id, status)
        """
        self.tasks: Dict[str, DownloadTask] = {}
        self.active_tasks: List[str] = []
        self.task_db_path = task_db_path or os.path.expanduser("~/.pyquick/downloads.json")
        self.max_concurrent_downloads = max_concurrent_downloads
        self.num_threads_per_download = num_threads_per_download
        self.on_task_status_changed = on_task_status_changed
        self.lock = threading.Lock()
        
        # 创建任务数据库目录
        os.makedirs(os.path.dirname(self.task_db_path), exist_ok=True)
        
        # 加载保存的任务
        self._load_tasks()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_tasks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _load_tasks(self):
        """从数据库加载任务"""
        if not os.path.exists(self.task_db_path):
            return
            
        try:
            with open(self.task_db_path, 'r') as f:
                tasks_data = json.load(f)
                
            for task_data in tasks_data:
                task = DownloadTask.from_dict(task_data)
                self.tasks[task.task_id] = task
                
        except Exception as e:
            print(f"Error loading tasks: {str(e)}")
            
    def _save_tasks(self):
        """保存任务到数据库"""
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            
            with open(self.task_db_path, 'w') as f:
                json.dump(tasks_data, f)
                
        except Exception as e:
            print(f"Error saving tasks: {str(e)}")
            
    def _update_task_status(self, task_id: str, status: str, error: Optional[str] = None):
        """更新任务状态"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                
                if error:
                    task.error = error
                    
                if status == 'completed' or status == 'cancelled' or status == 'error':
                    task.finish_time = time.time()
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                        
                elif status == 'downloading' and task.start_time == 0:
                    task.start_time = time.time()
                    
                # 保存任务
                self._save_tasks()
                
                # 回调通知
                if self.on_task_status_changed:
                    self.on_task_status_changed(task_id, status)
                    
                # 检查队列中的任务
                self._check_queue()
                
    def _update_task_progress(self, task_id: str, progress: float, speed: float):
        """更新任务进度"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.progress = progress
                task.speed = speed
                
    def _monitor_tasks(self):
        """监控下载任务的状态"""
        while True:
            time.sleep(1)
            
            tasks_to_update = []
            with self.lock:
                # 复制当前任务列表，避免在遍历中修改
                for task_id, task in self.tasks.items():
                    if task.status == 'downloading' and task.downloader:
                        tasks_to_update.append((task_id, task))
                        
            # 更新任务状态
            for task_id, task in tasks_to_update:
                downloader = task.downloader
                
                if downloader.is_completed():
                    self._update_task_status(task_id, 'completed')
                elif downloader.is_cancelled():
                    self._update_task_status(task_id, 'cancelled')
                elif downloader.error:
                    self._update_task_status(task_id, 'error', str(downloader.error))
                else:
                    # 更新进度和速度
                    progress = downloader.get_progress()
                    speed = downloader.get_download_speed()
                    self._update_task_progress(task_id, progress, speed)
                    
    def _check_queue(self):
        """检查下载队列，启动等待中的任务"""
        with self.lock:
            # 检查是否有空闲槽
            if len(self.active_tasks) >= self.max_concurrent_downloads:
                return
                
            # 查找待处理的任务
            pending_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status == 'pending' and task_id not in self.active_tasks
            ]
            
            # 计算可以启动的任务数
            slots_available = self.max_concurrent_downloads - len(self.active_tasks)
            
            # 启动任务
            for task_id in pending_tasks[:slots_available]:
                self._start_task(task_id)
                
    def _start_task(self, task_id: str):
        """启动下载任务"""
        with self.lock:
            if task_id not in self.tasks:
                return
                
            task = self.tasks[task_id]
            
            # 创建下载器
            downloader = Downloader(
                url=task.url,
                file_path=os.path.join(task.file_path, task.file_name),
                num_threads=self.num_threads_per_download,
                status_callback=lambda status: self._on_downloader_status(task_id, status)
            )
            
            task.downloader = downloader
            task.status = 'downloading'
            self.active_tasks.append(task_id)
            
            # 保存任务
            self._save_tasks()
            
            # 回调通知
            if self.on_task_status_changed:
                self.on_task_status_changed(task_id, 'downloading')
                
            # 启动下载
            downloader.start()
            
    def _on_downloader_status(self, task_id: str, status: str):
        """下载器状态变化回调"""
        # 可以记录日志或触发UI更新
        pass
            
    def add_task(self, url: str, file_path: str, file_name: Optional[str] = None) -> str:
        """
        添加下载任务
        
        参数:
            url: 下载URL
            file_path: 保存目录
            file_name: 文件名，如果不提供则从URL中提取
            
        返回:
            任务ID
        """
        # 如果未提供文件名，从URL中提取
        if not file_name:
            file_name = url.split('/')[-1]
            if not file_name:
                file_name = f"download_{int(time.time())}"
                
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务
        task = DownloadTask(
            task_id=task_id,
            url=url,
            file_path=file_path,
            file_name=file_name,
            status='pending',
            create_time=time.time()
        )
        
        # 添加到任务列表
        with self.lock:
            self.tasks[task_id] = task
            
            # 保存任务
            self._save_tasks()
            
            # 检查队列
            self._check_queue()
            
        return task_id
        
    def start_task(self, task_id: str) -> bool:
        """
        启动指定的下载任务
        
        参数:
            task_id: 任务ID
            
        返回:
            是否成功启动
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 如果任务已经在下载或已完成，不重复启动
            if task.status == 'downloading' or task.status == 'completed':
                return False
                
            # 将任务标记为待处理
            task.status = 'pending'
            
            # 保存任务
            self._save_tasks()
            
            # 检查队列
            self._check_queue()
            
            return True
            
    def pause_task(self, task_id: str) -> bool:
        """
        暂停指定的下载任务
        
        参数:
            task_id: 任务ID
            
        返回:
            是否成功暂停
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 只有下载中的任务可以暂停
            if task.status != 'downloading' or not task.downloader:
                return False
                
            # 暂停下载
            task.downloader.pause()
            task.status = 'paused'
            
            # 从活动任务列表中移除
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
                
            # 保存任务
            self._save_tasks()
            
            # 回调通知
            if self.on_task_status_changed:
                self.on_task_status_changed(task_id, 'paused')
                
            # 检查队列
            self._check_queue()
            
            return True
            
    def resume_task(self, task_id: str) -> bool:
        """
        恢复指定的下载任务
        
        参数:
            task_id: 任务ID
            
        返回:
            是否成功恢复
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 只有暂停的任务可以恢复
            if task.status != 'paused' or not task.downloader:
                return False
                
            # 如果活动任务已满，则标记为待处理
            if len(self.active_tasks) >= self.max_concurrent_downloads:
                task.status = 'pending'
                
                # 保存任务
                self._save_tasks()
                
                # 回调通知
                if self.on_task_status_changed:
                    self.on_task_status_changed(task_id, 'pending')
                    
                return True
                
            # 恢复下载
            task.downloader.resume()
            task.status = 'downloading'
            self.active_tasks.append(task_id)
            
            # 保存任务
            self._save_tasks()
            
            # 回调通知
            if self.on_task_status_changed:
                self.on_task_status_changed(task_id, 'downloading')
                
            return True
            
    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定的下载任务
        
        参数:
            task_id: 任务ID
            
        返回:
            是否成功取消
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 已完成或已取消的任务不能再取消
            if task.status == 'completed' or task.status == 'cancelled':
                return False
                
            # 取消下载
            if task.downloader:
                task.downloader.cancel()
                
            task.status = 'cancelled'
            
            # 从活动任务列表中移除
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
                
            # 保存任务
            self._save_tasks()
            
            # 回调通知
            if self.on_task_status_changed:
                self.on_task_status_changed(task_id, 'cancelled')
                
            # 检查队列
            self._check_queue()
            
            return True
            
    def remove_task(self, task_id: str) -> bool:
        """
        从列表中移除下载任务
        
        参数:
            task_id: 任务ID
            
        返回:
            是否成功移除
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 如果任务正在下载，先取消
            if task.status == 'downloading' and task.downloader:
                task.downloader.cancel()
                
            # 从任务列表中移除
            del self.tasks[task_id]
            
            # 从活动任务列表中移除
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
                
            # 保存任务
            self._save_tasks()
            
            # 检查队列
            self._check_queue()
            
            return True
            
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        获取指定任务
        
        参数:
            task_id: 任务ID
            
        返回:
            下载任务对象，如果不存在则返回None
        """
        with self.lock:
            return self.tasks.get(task_id)
            
    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务列表"""
        with self.lock:
            return list(self.tasks.values())
            
    def get_task_count(self) -> Dict[str, int]:
        """获取各状态的任务数量"""
        counts = {
            'pending': 0,
            'downloading': 0,
            'paused': 0,
            'completed': 0,
            'cancelled': 0,
            'error': 0,
            'total': 0
        }
        
        with self.lock:
            for task in self.tasks.values():
                if task.status in counts:
                    counts[task.status] += 1
                counts['total'] += 1
                
        return counts
        
    def pause_all(self):
        """暂停所有下载中的任务"""
        with self.lock:
            for task_id, task in self.tasks.items():
                if task.status == 'downloading' and task.downloader:
                    task.downloader.pause()
                    task.status = 'paused'
                    
                    # 从活动任务列表中移除
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                        
                    # 回调通知
                    if self.on_task_status_changed:
                        self.on_task_status_changed(task_id, 'paused')
                        
            # 保存任务
            self._save_tasks()
            
    def resume_all(self):
        """恢复所有暂停的任务"""
        with self.lock:
            # 先找出所有暂停的任务
            paused_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status == 'paused'
            ]
            
            # 逐个恢复任务
            for task_id in paused_tasks:
                self.resume_task(task_id)
                
    def cancel_all(self):
        """取消所有未完成的任务"""
        with self.lock:
            # 先找出所有未完成的任务
            active_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status not in ['completed', 'cancelled']
            ]
            
            # 逐个取消任务
            for task_id in active_tasks:
                self.cancel_task(task_id)
                
    def clear_completed(self):
        """清除所有已完成的任务"""
        with self.lock:
            # 找出所有已完成的任务
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status in ['completed', 'cancelled']
            ]
            
            # 逐个移除任务
            for task_id in completed_tasks:
                self.remove_task(task_id)
                
    def get_total_speed(self) -> float:
        """获取总下载速度（字节/秒）"""
        total_speed = 0.0
        
        with self.lock:
            for task in self.tasks.values():
                if task.status == 'downloading':
                    total_speed += task.speed
                    
        return total_speed 