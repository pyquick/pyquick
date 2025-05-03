from enum import Enum
import os
import logging
import time
import uuid
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    """下载状态枚举"""
    WAITING = "waiting"       # 等待下载
    PREPARING = "preparing"   # 准备中
    CONNECTING = "connecting" # 正在连接
    DOWNLOADING = "downloading" # 正在下载
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 出错
    CANCELLED = "cancelled"  # 已取消

class DownloadTask:
    """下载任务类"""
    
    def __init__(self, url: str, file_path: str, task_id: str = None, 
                thread_count: int = 4, proxies: Optional[Dict[str, str]] = None):
        """
        初始化下载任务
        
        Args:
            url: 下载URL
            file_path: 保存路径
            task_id: 任务ID，如果不提供则自动生成
            thread_count: 线程数
            proxies: 代理设置
        """
        self.url = url
        self.file_path = file_path
        self.task_id = task_id or str(uuid.uuid4())
        self.thread_count = thread_count
        self.proxies = proxies
        
        # 文件信息
        self.file_name = os.path.basename(file_path)
        self.save_dir = os.path.dirname(file_path)
        self.content_length = 0
        self.headers = {}
        self.is_resumable = False
        
        # 下载状态
        self.status = DownloadStatus.WAITING
        self.error_message = ""
        self.start_time = None
        self.end_time = None
        self.downloaded_size = 0
        self.speed = 0  # bytes/s
        self.progress = 0.0  # 0-100
        
        # 多线程下载相关
        self.parts = []
        self.temp_files = []
        
        # 回调函数
        self.callbacks = []
        
        # 时间跟踪
        self.created_time = time.time()
        self.last_active_time = 0.0
        
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
            
    def update_status(self, status, error_message: str = ""):
        """
        更新任务状态
        
        Args:
            status: 新状态
            error_message: 错误信息（如果有）
        """
        try:
            # 如果提供的状态是枚举值，则直接使用
            if isinstance(status, DownloadStatus):
                self.status = status
            # 如果是枚举值的字符串表示，则转换为枚举
            elif isinstance(status, str):
                try:
                    # 尝试直接转换
                    self.status = DownloadStatus(status)
                except ValueError:
                    # 如果直接转换失败，尝试查找匹配的枚举
                    for s in DownloadStatus:
                        if s.value == status:
                            self.status = s
                            break
                    else:
                        # 如果仍然找不到匹配，使用默认值
                        logger.warning(f"未知的状态值: {status}，使用默认值 WAITING")
                        self.status = DownloadStatus.WAITING
            # 处理其他情况
            else:
                logger.warning(f"不支持的状态类型: {type(status)}，使用默认值 WAITING")
                self.status = DownloadStatus.WAITING
            
            # 处理错误信息
            if error_message:
                self.error_message = error_message
                
            # 根据状态更新时间信息
            if self.status == DownloadStatus.DOWNLOADING and not self.start_time:
                self.start_time = time.time()
            elif self.status in [DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELLED]:
                self.end_time = time.time()
                
            # 通知回调
            self._notify_callbacks()
            
            # 更新最后活动时间
            self.last_active_time = time.time()
            
        except Exception as e:
            # 记录错误但不中断流程
            logger.error(f"更新任务状态失败: {e}")
            # 确保错误信息被保存
            if error_message:
                self.error_message = error_message
    
    def register_callback(self, callback: Callable[["DownloadTask"], None]):
        """
        注册状态变更回调函数
        
        Args:
            callback: 回调函数，接收任务对象作为参数
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[["DownloadTask"], None]):
        """
        取消注册回调函数
        
        Args:
            callback: 要取消的回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """通知所有回调函数"""
        for callback in self.callbacks[:]:  # 使用副本避免回调过程中的修改
            try:
                callback(self)
            except Exception as e:
                print(f"回调函数执行出错: {e}")
    
    def update_progress(self, downloaded_bytes: int, total_bytes: int, speed: float):
        """
        更新下载进度
        
        Args:
            downloaded_bytes: 已下载字节数
            total_bytes: 总字节数
            speed: 当前速度 (bytes/s)
        """
        self.downloaded_size = downloaded_bytes
        self.content_length = total_bytes
        self.speed = speed
        
        if total_bytes > 0:
            self.progress = min(100.0, (downloaded_bytes / total_bytes) * 100)
        
        # 通知回调
        self._notify_callbacks()
        
        self.last_active_time = time.time()
        
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

    def get_eta(self) -> int:
        """获取预计剩余时间（秒）"""
        if self.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING]:
            return 0
            
        if self.speed <= 0 or self.content_length <= 0:
            return -1  # 无法估计
                
        remaining_bytes = self.content_length - self.downloaded_size
        return int(remaining_bytes / self.speed)
    
    def get_formatted_eta(self) -> str:
        """获取格式化的预计剩余时间"""
        eta = self.get_eta()
        
        if eta < 0:
            return "未知"
        elif eta < 60:
            return f"{eta}秒"
        elif eta < 3600:
            minutes = eta // 60
            seconds = eta % 60
            return f"{minutes}分{seconds}秒"
        elif eta < 86400:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}小时{minutes}分"
        else:
            days = eta // 86400
            hours = (eta % 86400) // 3600
            return f"{days}天{hours}小时"

    def get_elapsed_time(self) -> float:
        """获取已用时间(秒)"""
        if self.start_time == 0:
            return 0.0
            
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time
        
    def get_formatted_size(self) -> str:
        """获取格式化的文件大小"""
        size = self.content_length
        
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.2f} GB"
        
    def get_formatted_downloaded_size(self) -> str:
        """获取格式化的已下载大小"""
        return self._format_size(self.downloaded_size)
        
    def get_formatted_speed(self) -> str:
        """获取格式化的速度"""
        speed = self.speed
        
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed/1024:.1f} KB/s"
        else:
            return f"{speed/(1024*1024):.1f} MB/s"
        
    def get_formatted_progress(self) -> str:
        """获取格式化的进度信息"""
        try:
            return f"{float(self.progress):.1f}%"
        except (ValueError, TypeError):
            return "0.0%"
        
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
        temp_dir = os.path.join(self.save_dir, f".temp_{self.task_id}")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
        
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

    def start(self):
        """开始下载任务"""
        try:
            # 更新任务状态
            self.update_status(DownloadStatus.CONNECTING)
            self.start_time = time.time()
            logger.info(f"开始下载任务: {self.task_id}")
            return True
        except Exception as e:
            logger.error(f"开始下载任务失败: {str(e)}")
            return False
            
    def resume(self):
        """恢复暂停的下载任务"""
        try:
            if self.status != DownloadStatus.PAUSED:
                logger.warning(f"只有暂停的任务才能恢复, 当前状态: {self.status}")
                return False
                
            # 更新状态
            self.update_status(DownloadStatus.CONNECTING)
            logger.info(f"恢复下载任务: {self.task_id}")
            return True
        except Exception as e:
            logger.error(f"恢复下载任务失败: {str(e)}")
            return False
            
    def pause(self):
        """暂停下载任务"""
        try:
            if self.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING]:
                logger.warning(f"只有正在下载或连接中的任务才能暂停, 当前状态: {self.status}")
                return False
                
            # 更新状态
            self.update_status(DownloadStatus.PAUSED)
            logger.info(f"暂停下载任务: {self.task_id}")
            return True
        except Exception as e:
            logger.error(f"暂停下载任务失败: {str(e)}")
            return False
            
    def cancel(self):
        """取消下载任务"""
        try:
            if self.status in [DownloadStatus.COMPLETED, DownloadStatus.CANCELLED]:
                logger.warning(f"任务已完成或已取消, 无法再次取消, 当前状态: {self.status}")
                return False
                
            # 更新状态
            self.update_status(DownloadStatus.CANCELLED)
            
            # 清理资源
            self.cleanup()
            
            logger.info(f"取消下载任务: {self.task_id}")
            return True
        except Exception as e:
            logger.error(f"取消下载任务失败: {str(e)}")
            return False