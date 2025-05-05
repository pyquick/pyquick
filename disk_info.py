#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
磁盘信息监控模块
负责收集和记录系统磁盘使用情况
"""

import os
import psutil
import logging
import threading
import time
from typing import Dict, List

class DiskInfoMonitor:
    """磁盘信息监控类"""
    
    def __init__(self, interval: int = 60):
        """
        初始化磁盘监控器
        
        Args:
            interval: 监控间隔时间(秒)
        """
        self.interval = interval
        self.logger = logging.getLogger("disk")
        self._stop_event = threading.Event()
        
    def get_disk_info(self) -> Dict[str, Dict[str, float]]:
        """
        获取磁盘使用信息
        
        Returns:
            包含各磁盘分区使用情况的字典
        """
        disk_info = {}
        try:
            partitions = psutil.disk_partitions(all=False)
            for partition in partitions:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.device] = {
                    'total': usage.total / (1024**3),  # GB
                    'used': usage.used / (1024**3),
                    'free': usage.free / (1024**3),
                    'percent': usage.percent
                }
        except Exception as e:
            self.logger.error(f"获取磁盘信息失败: {str(e)}")
        return disk_info
    
    def log_disk_info(self):
        """记录磁盘信息到日志"""
        disk_info = self.get_disk_info()
        for device, info in disk_info.items():
            self.logger.info(
                f"磁盘 {device}: 总量 {info['total']:.2f}GB, "
                f"已用 {info['used']:.2f}GB({info['percent']}%), "
                f"可用 {info['free']:.2f}GB"
            )
    
    def start_monitoring(self):
        """启动磁盘监控线程"""
        self.logger.info("启动磁盘信息监控")
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        monitor_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            self.logger.debug("开始收集磁盘信息")
            self.log_disk_info()
            self._stop_event.wait(self.interval)
    
    def stop_monitoring(self):
        """停止磁盘监控"""
        self.logger.info("停止磁盘信息监控")
        self._stop_event.set()