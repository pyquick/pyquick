#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络测试模块
用于测试网络连接状态、测速和延迟
"""

import os
import sys
import time
import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple, Callable
import json
import subprocess
import platform

logger = logging.getLogger(__name__)

class NetworkTest:
    """网络测试类，提供网络连通性和下载测速功能"""
    
    # 测试服务器列表
    DEFAULT_TEST_SERVERS = [
        {"name": "百度", "url": "https://www.baidu.com", "timeout": 5},
        {"name": "阿里云", "url": "https://www.aliyun.com", "timeout": 5},
        {"name": "腾讯云", "url": "https://cloud.tencent.com", "timeout": 5},
        {"name": "GitHub", "url": "https://github.com", "timeout": 10},
        {"name": "PyPI", "url": "https://pypi.org", "timeout": 10},
        {"name": "Google", "url": "https://www.google.com", "timeout": 10},
    ]
    
    # 下载测速文件
    SPEED_TEST_FILES = [
        {"name": "小文件(1MB)", "url": "https://speed.hetzner.de/1MB.bin", "size": 1},
        {"name": "中文件(10MB)", "url": "https://speed.hetzner.de/10MB.bin", "size": 10},
        {"name": "大文件(100MB)", "url": "https://speed.hetzner.de/100MB.bin", "size": 100},
    ]
    
    def __init__(self, parent=None):
        """
        初始化网络测试工具
        
        Args:
            parent: 父级窗口
        """
        self.parent = parent
        self.test_servers = self.DEFAULT_TEST_SERVERS.copy()
        self.speed_test_files = self.SPEED_TEST_FILES.copy()
        self._ping_results = {}
        self._speed_results = {}
        self._running_tests = {}
        self._test_lock = threading.Lock()
    
    def create_test_window(self):
        """创建网络测试窗口"""
        if not self.parent:
            root = tk.Tk()
            root.title("网络测试")
            root.geometry("600x500")
            self.parent = root
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("网络测试")
        self.window.geometry("600x500")
        self.window.minsize(500, 400)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 居中显示
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 添加连通性测试选项卡
        connectivity_frame = ttk.Frame(notebook, padding=10)
        notebook.add(connectivity_frame, text="连通性测试")
        self._create_connectivity_tab(connectivity_frame)
        
        # 添加下载测速选项卡
        speed_frame = ttk.Frame(notebook, padding=10)
        notebook.add(speed_frame, text="下载测速")
        self._create_speed_test_tab(speed_frame)
        
        # 添加Ping工具选项卡
        ping_frame = ttk.Frame(notebook, padding=10)
        notebook.add(ping_frame, text="Ping工具")
        self._create_ping_tool_tab(ping_frame)
        
        # 添加底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="关闭", command=self.window.destroy)
        close_button.pack(side=tk.RIGHT)
        
        return self.window
    
    def _create_connectivity_tab(self, parent):
        """创建连通性测试选项卡"""
        # 服务器列表框架
        list_frame = ttk.LabelFrame(parent, text="测试服务器")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ("服务器", "状态", "延迟", "详细信息")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 设置列标题和宽度
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("服务器", width=100, anchor=tk.W)
        tree.column("状态", width=80, anchor=tk.CENTER)
        tree.column("延迟", width=80, anchor=tk.CENTER)
        tree.column("详细信息", width=200, anchor=tk.W)
        
        # 填充服务器列表
        for server in self.test_servers:
            tree.insert("", tk.END, values=(server["name"], "未测试", "-", "-"))
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 添加按钮
        test_button = ttk.Button(button_frame, text="开始测试", command=lambda: self._run_connectivity_test(tree))
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.conn_progress = ttk.Progressbar(button_frame, mode="determinate", length=300)
        self.conn_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 保存树状图引用
        self.connectivity_tree = tree
    
    def _create_speed_test_tab(self, parent):
        """创建下载测速选项卡"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="测试文件")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 文件选择下拉框
        ttk.Label(file_frame, text="选择测试文件:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.speed_file_var = tk.StringVar()
        file_combo = ttk.Combobox(file_frame, textvariable=self.speed_file_var, state="readonly", width=30)
        file_combo["values"] = [f["name"] for f in self.speed_test_files]
        file_combo.current(0)
        file_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 结果框架
        result_frame = ttk.LabelFrame(parent, text="测速结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 结果表格
        result_text = tk.Text(result_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_text.configure(yscrollcommand=scrollbar.set)
        
        # 进度框架
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="下载进度:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.speed_progress = ttk.Progressbar(progress_frame, mode="determinate", length=300)
        self.speed_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.speed_label = ttk.Label(progress_frame, text="0.0 MB/s")
        self.speed_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 添加按钮
        self.speed_button = ttk.Button(button_frame, text="开始测速", 
            command=lambda: self._run_speed_test(result_text))
        self.speed_button.pack(side=tk.LEFT)
        
        # 保存文本控件引用
        self.speed_result_text = result_text
    
    def _create_ping_tool_tab(self, parent):
        """创建Ping工具选项卡"""
        # 输入框架
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="主机名/IP:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.ping_host_var = tk.StringVar()
        host_entry = ttk.Entry(input_frame, textvariable=self.ping_host_var, width=30)
        host_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(input_frame, text="请求次数:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.ping_count_var = tk.IntVar(value=4)
        count_spinner = ttk.Spinbox(input_frame, from_=1, to=100, textvariable=self.ping_count_var, width=10)
        count_spinner.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 结果框架
        result_frame = ttk.LabelFrame(parent, text="Ping结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 结果文本框
        ping_text = tk.Text(result_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        ping_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=ping_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ping_text.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 添加按钮
        self.ping_button = ttk.Button(button_frame, text="开始Ping", 
            command=lambda: self._run_ping_test(ping_text))
        self.ping_button.pack(side=tk.LEFT)
        
        # 保存文本控件引用
        self.ping_result_text = ping_text
    
    def _run_connectivity_test(self, tree):
        """运行连通性测试"""
        # 重置进度条
        self.conn_progress["value"] = 0
        total_servers = len(self.test_servers)
        
        # 清空之前的结果
        for i, server in enumerate(self.test_servers):
            item_id = tree.get_children()[i]
            tree.item(item_id, values=(server["name"], "测试中...", "-", "-"))
        
        # 更新UI
        self.window.update()
        
        # 启动测试线程
        threading.Thread(
            target=self._perform_connectivity_test,
            args=(tree, total_servers),
            daemon=True
        ).start()
    
    def _perform_connectivity_test(self, tree, total_servers):
        """执行连通性测试"""
        for i, server in enumerate(self.test_servers):
            item_id = tree.get_children()[i]
            
            try:
                start_time = time.time()
                response = requests.get(
                    server["url"], 
                    timeout=server["timeout"],
                    verify=True,
                    allow_redirects=True
                )
                end_time = time.time()
                
                # 计算延迟
                latency = round((end_time - start_time) * 1000, 2)
                
                # 检查响应状态
                if response.status_code == 200:
                    status = "✓ 正常"
                    details = f"状态码: {response.status_code}, 服务器: {response.headers.get('Server', '未知')}"
                else:
                    status = "! 异常"
                    details = f"状态码: {response.status_code}"
                
                # 更新UI
                def update_ui():
                    tree.item(item_id, values=(server["name"], status, f"{latency} ms", details))
                    self.conn_progress["value"] = ((i + 1) / total_servers) * 100
                
                # 在主线程中更新UI
                self.window.after(0, update_ui)
                
            except requests.RequestException as e:
                # 处理请求异常
                status = "✗ 失败"
                error_type = type(e).__name__
                
                if isinstance(e, requests.ConnectTimeout):
                    details = "连接超时"
                elif isinstance(e, requests.ReadTimeout):
                    details = "读取超时"
                elif isinstance(e, requests.ConnectionError):
                    details = "连接错误"
                else:
                    details = str(e)
                
                # 更新UI
                def update_error_ui():
                    tree.item(item_id, values=(server["name"], status, "-", f"{error_type}: {details}"))
                    self.conn_progress["value"] = ((i + 1) / total_servers) * 100
                
                # 在主线程中更新UI
                self.window.after(0, update_error_ui)
            
            # 短暂暂停，避免请求太快
            time.sleep(0.5)
    
    def _run_speed_test(self, result_text):
        """运行下载测速"""
        # 获取选择的文件
        selected_file_name = self.speed_file_var.get()
        selected_file = None
        
        for f in self.speed_test_files:
            if f["name"] == selected_file_name:
                selected_file = f
                break
        
        if not selected_file:
            messagebox.showerror("错误", "请选择测试文件")
            return
        
        # 禁用按钮
        self.speed_button.configure(state=tk.DISABLED)
        
        # 重置进度条
        self.speed_progress["value"] = 0
        self.speed_label.configure(text="0.0 MB/s")
        
        # 清空结果
        result_text.configure(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"开始测速: {selected_file['name']} ({selected_file['size']} MB)\n")
        result_text.configure(state=tk.DISABLED)
        
        # 更新UI
        self.window.update()
        
        # 启动测试线程
        threading.Thread(
            target=self._perform_speed_test,
            args=(selected_file, result_text),
            daemon=True
        ).start()
    
    def _perform_speed_test(self, file_info, result_text):
        """执行下载测速"""
        try:
            url = file_info["url"]
            expected_size_mb = file_info["size"]
            
            # 更新结果文本
            def update_text(text):
                result_text.configure(state=tk.NORMAL)
                result_text.insert(tk.END, text + "\n")
                result_text.see(tk.END)
                result_text.configure(state=tk.DISABLED)
            
            self.window.after(0, update_text, f"正在连接到: {url}")
            
            # 记录开始时间
            start_time = time.time()
            
            # 使用流式下载，实时更新进度
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取内容长度
            content_length = int(response.headers.get('content-length', 0))
            expected_size_bytes = expected_size_mb * 1024 * 1024
            
            if content_length == 0:
                self.window.after(0, update_text, "警告: 服务器未返回文件大小信息")
                content_length = expected_size_bytes
            
            # 初始化进度变量
            downloaded = 0
            chunk_size = 4096
            last_update_time = time.time()
            last_downloaded = 0
            
            # 临时存储数据
            temp_file = bytearray()
            
            # 下载数据
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    temp_file.extend(chunk)
                    downloaded += len(chunk)
                    
                    # 更新速度和进度（每0.5秒更新一次）
                    current_time = time.time()
                    if current_time - last_update_time >= 0.5:
                        # 计算下载速度
                        elapsed = current_time - last_update_time
                        bytes_since_last = downloaded - last_downloaded
                        speed_mbps = (bytes_since_last / elapsed) / (1024 * 1024)
                        
                        # 更新进度条
                        progress = (downloaded / content_length) * 100
                        
                        # 在主线程中更新UI
                        def update_progress():
                            self.speed_progress["value"] = progress
                            self.speed_label.configure(text=f"{speed_mbps:.2f} MB/s")
                        
                        self.window.after(0, update_progress)
                        
                        # 更新上次更新时间和下载量
                        last_update_time = current_time
                        last_downloaded = downloaded
            
            # 计算总时间和平均速度
            total_time = time.time() - start_time
            avg_speed_mbps = (downloaded / total_time) / (1024 * 1024)
            
            # 更新结果
            self.window.after(0, update_text, f"测速完成:")
            self.window.after(0, update_text, f"- 总下载: {downloaded/1024/1024:.2f} MB")
            self.window.after(0, update_text, f"- 总时间: {total_time:.2f} 秒")
            self.window.after(0, update_text, f"- 平均速度: {avg_speed_mbps:.2f} MB/s")
            
            # 更新最终进度
            def final_update():
                self.speed_progress["value"] = 100
                self.speed_label.configure(text=f"{avg_speed_mbps:.2f} MB/s")
                self.speed_button.configure(state=tk.NORMAL)
            
            self.window.after(0, final_update)
            
        except requests.RequestException as e:
            # 处理请求异常
            error_msg = f"测速失败: {type(e).__name__} - {str(e)}"
            self.window.after(0, update_text, error_msg)
            
            # 恢复按钮状态
            self.window.after(0, lambda: self.speed_button.configure(state=tk.NORMAL))
    
    def _run_ping_test(self, result_text):
        """运行Ping测试"""
        host = self.ping_host_var.get().strip()
        count = self.ping_count_var.get()
        
        if not host:
            messagebox.showerror("错误", "请输入主机名或IP地址")
            return
        
        # 禁用按钮
        self.ping_button.configure(state=tk.DISABLED)
        
        # 清空结果
        result_text.configure(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.configure(state=tk.DISABLED)
        
        # 启动Ping线程
        threading.Thread(
            target=self._perform_ping_test,
            args=(host, count, result_text),
            daemon=True
        ).start()
    
    def _perform_ping_test(self, host, count, result_text):
        """执行Ping测试"""
        try:
            # 更新结果文本
            def update_text(text):
                result_text.configure(state=tk.NORMAL)
                result_text.insert(tk.END, text + "\n")
                result_text.see(tk.END)
                result_text.configure(state=tk.DISABLED)
            
            self.window.after(0, update_text, f"正在Ping {host} [{count}次]...")
            
            # 根据操作系统选择ping命令
            system = platform.system().lower()
            
            if system == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:  # Linux, Darwin (macOS)
                cmd = ["ping", "-c", str(count), host]
            
            # 执行ping命令
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 实时获取输出
            for line in process.stdout:
                self.window.after(0, update_text, line.strip())
            
            # 等待命令完成
            process.wait()
            
            # 检查是否有错误
            if process.returncode != 0:
                stderr = process.stderr.read()
                if stderr:
                    self.window.after(0, update_text, f"错误: {stderr}")
            
            # 恢复按钮状态
            self.window.after(0, lambda: self.ping_button.configure(state=tk.NORMAL))
            
        except Exception as e:
            # 处理异常
            self.window.after(0, update_text, f"执行Ping测试失败: {str(e)}")
            self.window.after(0, lambda: self.ping_button.configure(state=tk.NORMAL))

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PyQuick")
    
    app = NetworkTest(root)
    test_window = app.create_test_window()
    
    root.mainloop() 