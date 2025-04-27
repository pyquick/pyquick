"""
下载块管理类，负责处理单个下载块的下载、暂停和恢复
"""

import os
import time
import threading
import requests
from typing import Dict, Optional, Callable

class DownloadChunk:
    """单个下载块管理类"""
    
    def __init__(self, 
                 chunk_id: int, 
                 url: str, 
                 start_byte: int, 
                 end_byte: int, 
                 file_path: str,
                 headers: Optional[Dict] = None,
                 proxies: Optional[Dict] = None,
                 progress_callback: Optional[Callable] = None,
                 verify: bool = True):
        """
        初始化下载块
        
        参数:
            chunk_id: 块ID
            url: 下载URL
            start_byte: 起始字节
            end_byte: 结束字节
            file_path: 文件保存路径
            headers: HTTP请求头
            proxies: 代理设置
            progress_callback: 进度回调函数
            verify: SSL验证
        """
        self.chunk_id = chunk_id
        self.url = url
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.file_path = file_path
        self.headers = headers or {}
        self.proxies = proxies
        self.progress_callback = progress_callback
        self.verify = verify
        
        # 状态标志
        self.paused = threading.Event()
        self.cancelled = threading.Event()
        self.completed = threading.Event()
        self.error = None
        
        # 当前进度
        self.downloaded_bytes = 0
        self.total_bytes = end_byte - start_byte + 1
        self.current_position = start_byte
        
        # 临时文件路径
        self.temp_file = f"{file_path}.part{chunk_id}"
        
        # 恢复下载的标志
        self.resuming = False
        
    def start(self):
        """开始下载块"""
        self.paused.clear()
        self.cancelled.clear()
        self.completed.clear()
        self.error = None
        self._download()
        
    def pause(self):
        """暂停下载"""
        self.paused.set()
        
    def resume(self):
        """恢复下载"""
        if self.completed.is_set():
            return
            
        self.resuming = True
        self.paused.clear()
        self._download()
        
    def cancel(self):
        """取消下载"""
        self.cancelled.set()
        
        # 清理临时文件
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
                
    def _download(self):
        """执行下载任务"""
        # 检查是否已完成或已取消
        if self.completed.is_set() or self.cancelled.is_set():
            return
            
        thread = threading.Thread(target=self._download_thread)
        thread.daemon = True
        thread.start()
        
    def _download_thread(self):
        """下载线程实现"""
        try:
            # 如果恢复下载且临时文件存在，确定当前位置
            if self.resuming and os.path.exists(self.temp_file):
                self.current_position = self.start_byte + os.path.getsize(self.temp_file)
                self.downloaded_bytes = self.current_position - self.start_byte
                self.resuming = False
                
            # 设置范围请求头
            range_header = {'Range': f'bytes={self.current_position}-{self.end_byte}'}
            headers = {**self.headers, **range_header}
            
            # 开始请求
            with requests.get(self.url, 
                             headers=headers, 
                             stream=True, 
                             proxies=self.proxies,
                             verify=self.verify) as response:
                response.raise_for_status()
                
                # 打开文件准备写入
                mode = 'ab' if os.path.exists(self.temp_file) else 'wb'
                with open(self.temp_file, mode) as f:
                    # 下载循环
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancelled.is_set():
                            return
                            
                        if self.paused.is_set():
                            return
                            
                        if chunk:
                            f.write(chunk)
                            self.downloaded_bytes += len(chunk)
                            self.current_position += len(chunk)
                            
                            # 更新进度
                            if self.progress_callback:
                                self.progress_callback(self.chunk_id, len(chunk))
            
            # 下载完成
            self.completed.set()
                
        except requests.RequestException as e:
            self.error = e
            
        except Exception as e:
            self.error = e

    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.completed.is_set()
    
    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self.paused.is_set()
    
    def is_cancelled(self) -> bool:
        """检查是否取消"""
        return self.cancelled.is_set()
    
    def get_progress(self) -> float:
        """获取下载进度百分比"""
        if self.total_bytes == 0:
            return 0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    def get_error(self):
        """获取错误信息"""
        return self.error 