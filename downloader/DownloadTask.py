import enum
import os
import logging

logger = logging.getLogger(__name__)
import time
from typing import Dict, List, Optional

class DownloadStatus(enum.Enum):
    """下载状态枚举"""
    WAITING = "等待中"
    CONNECTING = "连接中"
    DOWNLOADING = "下载中" 
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    ERROR = "出错"

class DownloadTask:
    """下载任务类，表示一个下载任务及其相关信息"""
    
    def __init__(self, task_id: str, url: str, file_path: str, 
                thread_count: int = 5, proxies: Optional[Dict[str, str]] = None):
        # 基本信息
        self.task_id = task_id
        self.url = url
        self.file_path = file_path
        self.save_dir = os.path.dirname(file_path)
        self.thread_count = max(1, thread_count)
        self.proxies = proxies
        
        # 文件信息
        self.file_name = os.path.basename(file_path)
        self.content_length = 0
        self.mime_type = ""
        self.headers: Dict[str, str] = {}
        self.is_resumable = False
        
        # 状态信息
        self.status = DownloadStatus.WAITING
        self.error_message = ""
        self.downloaded_size = 0
        self.speed = 0.0
        self.progress = 0.0
        
        # 时间跟踪
        self.created_time = time.time()
        self.start_time = 0.0
        self.end_time = 0.0
        self.last_active_time = 0.0
        
        # 下载分片信息
        self.parts: List[Dict] = []
        self.temp_files: List[str] = []
        self.part_states: Dict[int, bool] = {}  # 分片完成状态
        
        # 性能统计
        self._speed_samples = []  # 用于计算平均速度
        self._sample_window = 10  # 保留最近10秒的样本
        self._last_progress_time = 0
        
    def update_file_info(self, file_size: int, mime_type: str = "", file_name: str = ""):
        """更新文件信息"""
        self.content_length = file_size
        if mime_type:
            self.mime_type = mime_type
        if file_name:
            self.file_name = file_name
            self.file_path = os.path.join(self.save_dir, self.file_name)
            
    def update_status(self, status: DownloadStatus, error: str = ""):
        """更新下载状态"""
        self.status = status
        self.last_active_time = time.time()
        
        if error:
            self.error_message = error
            
        if status == DownloadStatus.DOWNLOADING and self.start_time == 0:
            self.start_time = time.time()
        elif status in [DownloadStatus.COMPLETED, DownloadStatus.CANCELLED, DownloadStatus.ERROR]:
            self.end_time = time.time()
            
    def update_progress(self, downloaded_size: int, speed: float):
        """更新下载进度"""
        now = time.time()
        try:
            self.downloaded_size = int(downloaded_size)
            self.speed = float(speed)
            
            if self.content_length > 0:
                self.progress = round(min(100.0, (self.downloaded_size / self.content_length) * 100), 2)
            else:
                self.progress = 0.0
                
            # 更新速度采样，使用安全的类型转换
            self._speed_samples = [(t, float(s)) for t, s in self._speed_samples 
                                 if isinstance(t, (int, float)) and 
                                 isinstance(s, (int, float)) and 
                                 now - t <= self._sample_window]
            self._speed_samples.append((now, self.speed))
            
            self.last_active_time = now
        except (ValueError, TypeError) as e:
            logger.error(f"Error updating progress: {str(e)}")
            self.progress = 0.0
            self.speed = 0.0
        
    def get_average_speed(self) -> float:
        """获取平均下载速度(B/s)"""
        try:
            if not self._speed_samples:
                return 0.0
                
            valid_samples = [(t, s) for t, s in self._speed_samples 
                            if isinstance(s, (int, float)) and s >= 0]
            if not valid_samples:
                return 0.0
                
            total_speed = sum(speed for _, speed in valid_samples)
            return total_speed / len(valid_samples)
        except Exception as e:
            logger.error(f"Error calculating average speed: {str(e)}")
            return 0.0

    def get_eta(self) -> float:
        """获取预计剩余时间(秒)"""
        try:
            if self.status != DownloadStatus.DOWNLOADING or self.content_length <= 0:
                return 0.0
                
            avg_speed = self.get_average_speed()
            if avg_speed <= 0:
                return 0.0
                
            remaining_bytes = max(0, self.content_length - self.downloaded_size)
            return remaining_bytes / avg_speed
        except Exception as e:
            logger.error(f"Error calculating ETA: {str(e)}")
            return 0.0

    def get_elapsed_time(self) -> float:
        """获取已用时间(秒)"""
        if self.start_time == 0:
            return 0.0
            
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time
        
    def get_formatted_size(self) -> str:
        """获取格式化的文件大小"""
        return self._format_size(self.content_length)
        
    def get_formatted_downloaded_size(self) -> str:
        """获取格式化的已下载大小"""
        return self._format_size(self.downloaded_size)
        
    def get_formatted_speed(self) -> str:
        """获取格式化的下载速度"""
        return f"{self._format_size(self.speed)}/s"
        
    def get_formatted_progress(self) -> str:
        """获取格式化的进度信息"""
        try:
            return f"{float(self.progress):.1f}%"
        except (ValueError, TypeError):
            return "0.0%"
        
    def get_formatted_eta(self) -> str:
        """获取格式化的预计剩余时间"""
        return self._format_time(self.get_eta())
        
    def get_formatted_elapsed_time(self) -> str:
        """获取格式化的已用时间"""
        return self._format_time(self.get_elapsed_time())
        
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.2f}MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.2f}GB"
            
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间"""
        if seconds <= 0:
            return "未知"
            
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def get_temp_dir(self) -> str:
        """获取临时文件目录"""
        return os.path.join(self.save_dir, f".temp_{self.task_id}")
        
    def cleanup(self):
        """清理任务资源"""
        try:
            # 清理临时文件
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
            # 清理临时目录
            temp_dir = self.get_temp_dir()
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
        except Exception as e:
            print(f"清理任务资源失败: {str(e)}")