#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线程管理模块
提供安全的线程管理和UI更新功能
"""
import os
import sys
import time
import logging
import threading
import queue
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

# 尝试导入日志模块
try:
    from log import get_logger
    logger = get_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# 全局线程池
_thread_pool = None
# 全局任务队列
_task_queue = queue.Queue()
# 正在运行的任务字典 {thread_id: task_info}
_running_tasks = {}
# 线程池锁
_pool_lock = threading.RLock()
# 任务计数锁
_task_counter_lock = threading.RLock()
# 任务计数器
_task_counter = 0

def get_thread_pool(max_workers=None):
    """获取或创建线程池
    
    Args:
        max_workers: 最大工作线程数，默认为None（由系统决定）
    
    Returns:
        ThreadPoolExecutor: 线程池实例
    """
    global _thread_pool
    with _pool_lock:
        if _thread_pool is None or _thread_pool._shutdown:
            if max_workers is None:
                # 使用处理器数量的两倍作为默认线程数
                import multiprocessing
                max_workers = min(32, multiprocessing.cpu_count() * 2)
            
            logger.debug(f"创建线程池，最大线程数: {max_workers}")
            _thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        return _thread_pool

def shutdown_thread_pool(wait=True):
    """关闭线程池
    
    Args:
        wait: 是否等待所有线程完成
    """
    global _thread_pool
    with _pool_lock:
        if _thread_pool is not None and not _thread_pool._shutdown:
            logger.debug("关闭线程池")
            _thread_pool.shutdown(wait=wait)
            _thread_pool = None

def run_in_thread(func, *args, **kwargs):
    """在后台线程中运行函数
    
    Args:
        func: 要运行的函数
        *args, **kwargs: 传递给函数的参数
    
    Returns:
        future: Future对象，可用于获取结果
    """
    global _task_counter
    
    # 获取任务ID
    with _task_counter_lock:
        task_id = _task_counter
        _task_counter += 1
    
    # 任务信息
    task_info = {
        "id": task_id,
        "name": getattr(func, "__name__", "unknown"),
        "start_time": time.time(),
        "status": "pending"
    }
    
    # 包装函数，用于记录任务状态
    def wrapped_func(*args, **kwargs):
        thread_id = threading.get_ident()
        task_info["thread_id"] = thread_id
        task_info["status"] = "running"
        _running_tasks[thread_id] = task_info
        
        try:
            logger.debug(f"启动任务: {task_info['name']} (ID: {task_id})")
            result = func(*args, **kwargs)
            task_info["status"] = "completed"
            task_info["end_time"] = time.time()
            task_info["duration"] = task_info["end_time"] - task_info["start_time"]
            logger.debug(f"完成任务: {task_info['name']} (ID: {task_id}, 用时: {task_info['duration']:.2f}秒)")
            return result
        
        except Exception as e:
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            task_info["end_time"] = time.time()
            task_info["duration"] = task_info["end_time"] - task_info["start_time"]
            logger.error(f"任务失败: {task_info['name']} (ID: {task_id}, 错误: {e})")
            # 重新抛出异常，使调用者可以捕获
            raise
        
        finally:
            if thread_id in _running_tasks:
                del _running_tasks[thread_id]
    
    # 提交任务到线程池
    pool = get_thread_pool()
    future = pool.submit(wrapped_func, *args, **kwargs)
    task_info["future"] = future
    
    return future

def safe_update_ui(root, callback):
    """安全地在主线程中更新UI
    
    Args:
        root: Tkinter根窗口或其他Tkinter组件
        callback: 在主线程中执行的回调函数
    """
    if not isinstance(root, tk.Misc):
        raise TypeError("root必须是Tkinter组件")
    
    try:
        root.after(0, callback)
    except Exception as e:
        logger.error(f"UI更新失败: {e}")

def get_running_tasks():
    """获取当前正在运行的任务列表
    
    Returns:
        list: 任务信息字典的列表
    """
    return list(_running_tasks.values())

def cancel_all_tasks():
    """取消所有正在运行的任务"""
    tasks = list(_running_tasks.values())
    cancelled = 0
    
    for task in tasks:
        if "future" in task and not task["future"].done():
            task["future"].cancel()
            cancelled += 1
    
    logger.info(f"已取消 {cancelled}/{len(tasks)} 个任务")
    return cancelled

# 注册退出时的清理函数
import atexit
atexit.register(shutdown_thread_pool, wait=False) 