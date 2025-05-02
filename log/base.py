# Base functionalities for logging or file storage.
# This file can contain common classes, functions, or constants.

"""
提供文件处理和存储的基础功能，
支持文件读写、检查、安全删除等操作
"""

import os
import shutil
import json
import time
from datetime import datetime
import threading

class FileManager:
    """文件管理基础类，提供文件操作功能"""
    
    def __init__(self, base_dir=None):
        """
        初始化文件管理器
        
        Args:
            base_dir: 基础目录，如不指定则不使用
        """
        self.base_dir = base_dir
        self.lock = threading.RLock()
    
    def _get_full_path(self, file_path):
        """
        获取完整文件路径
        
        Args:
            file_path: 相对或绝对路径
            
        Returns:
            str: 完整文件路径
        """
        if self.base_dir and not os.path.isabs(file_path):
            return os.path.join(self.base_dir, file_path)
        return file_path
    
    def ensure_dir(self, dir_path):
        """
        确保目录存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            bool: 目录是否存在或创建成功
        """
        full_path = self._get_full_path(dir_path)
        
        with self.lock:
            if not os.path.exists(full_path):
                try:
                    os.makedirs(full_path)
                    return True
                except Exception:
                    return False
            return os.path.isdir(full_path)
    
    def write_file(self, file_path, content, mode='w', encoding='utf-8'):
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 写入模式
            encoding: 文件编码
            
        Returns:
            bool: 是否写入成功
        """
        full_path = self._get_full_path(file_path)
        
        # 确保目录存在
        dir_name = os.path.dirname(full_path)
        if dir_name and not self.ensure_dir(dir_name):
            return False
        
        with self.lock:
            try:
                with open(full_path, mode, encoding=encoding) as f:
                    f.write(content)
                return True
            except Exception:
                return False
    
    def read_file(self, file_path, mode='r', encoding='utf-8'):
        """
        读取文件
        
        Args:
            file_path: 文件路径
            mode: 读取模式
            encoding: 文件编码
            
        Returns:
            str: 文件内容，失败返回None
        """
        full_path = self._get_full_path(file_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with open(full_path, mode, encoding=encoding) as f:
                return f.read()
        except Exception:
            return None
    
    def append_file(self, file_path, content, encoding='utf-8'):
        """
        追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 追加内容
            encoding: 文件编码
            
        Returns:
            bool: 是否追加成功
        """
        return self.write_file(file_path, content, mode='a', encoding=encoding)
    
    def delete_file(self, file_path, secure=False):
        """
        删除文件
        
        Args:
            file_path: 文件路径
            secure: 是否安全删除（覆盖文件内容）
            
        Returns:
            bool: 是否删除成功
        """
        full_path = self._get_full_path(file_path)
        
        if not os.path.exists(full_path) or os.path.isdir(full_path):
            return False
        
        with self.lock:
            try:
                if secure:
                    # 安全删除，先用随机数据覆盖
                    file_size = os.path.getsize(full_path)
                    with open(full_path, 'wb') as f:
                        f.write(os.urandom(min(file_size, 1024 * 1024)))
                        f.flush()
                
                os.remove(full_path)
                return True
            except Exception:
                return False
    
    def check_file(self, file_path):
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否存在
        """
        full_path = self._get_full_path(file_path)
        return os.path.exists(full_path) and os.path.isfile(full_path)
    
    def get_file_size(self, file_path):
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节），不存在返回-1
        """
        full_path = self._get_full_path(file_path)
        
        if not self.check_file(full_path):
            return -1
        
        try:
            return os.path.getsize(full_path)
        except Exception:
            return -1
    
    def get_file_info(self, file_path):
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 文件信息字典，包含大小、修改时间等
        """
        full_path = self._get_full_path(file_path)
        
        if not self.check_file(full_path):
            return None
        
        try:
            stat = os.stat(full_path)
            return {
                'path': full_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'accessed': datetime.fromtimestamp(stat.st_atime)
            }
        except Exception:
            return None
    
    def move_file(self, src_path, dst_path):
        """
        移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            bool: 是否移动成功
        """
        src_full = self._get_full_path(src_path)
        dst_full = self._get_full_path(dst_path)
        
        if not self.check_file(src_full):
            return False
        
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst_full)
        if dst_dir and not self.ensure_dir(dst_dir):
            return False
        
        with self.lock:
            try:
                shutil.move(src_full, dst_full)
                return True
            except Exception:
                return False
    
    def copy_file(self, src_path, dst_path):
        """
        复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            bool: 是否复制成功
        """
        src_full = self._get_full_path(src_path)
        dst_full = self._get_full_path(dst_path)
        
        if not self.check_file(src_full):
            return False
        
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst_full)
        if dst_dir and not self.ensure_dir(dst_dir):
            return False
        
        with self.lock:
            try:
                shutil.copy2(src_full, dst_full)
                return True
            except Exception:
                return False

# JSON文件操作类
class JsonFileManager(FileManager):
    """JSON文件操作类，提供读写JSON文件的功能"""
    
    def read_json(self, file_path, default=None):
        """
        读取JSON文件
        
        Args:
            file_path: 文件路径
            default: 默认返回值，文件不存在或读取失败时返回
            
        Returns:
            dict/list: JSON数据，失败返回default
        """
        content = self.read_file(file_path)
        if content is None:
            return default
        
        try:
            return json.loads(content)
        except Exception:
            return default
    
    def write_json(self, file_path, data, indent=2):
        """
        写入JSON文件
        
        Args:
            file_path: 文件路径
            data: JSON数据
            indent: 缩进空格数
            
        Returns:
            bool: 是否写入成功
        """
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=indent)
            return self.write_file(file_path, json_str)
        except Exception:
            return False
    
    def update_json(self, file_path, data, indent=2):
        """
        更新JSON文件
        
        Args:
            file_path: 文件路径
            data: 要更新的数据（字典）
            indent: 缩进空格数
            
        Returns:
            bool: 是否更新成功
        """
        current = self.read_json(file_path, {})
        if not isinstance(current, dict) or not isinstance(data, dict):
            return False
        
        # 更新数据
        current.update(data)
        return self.write_json(file_path, current, indent)

# 创建全局文件管理器实例
file_manager = FileManager()
json_manager = JsonFileManager()

def configure_file_managers(base_dir=None):
    """
    配置文件管理器
    
    Args:
        base_dir: 基础目录
    """
    global file_manager, json_manager
    
    file_manager = FileManager(base_dir)
    json_manager = JsonFileManager(base_dir)
