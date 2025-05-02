"""
pip镜像测试UI模块

提供测试pip镜像源速度的图形界面，帮助用户选择最佳的pip包管理镜像源。
"""

import os
import json
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

# 导入本地模块
try:
    from test_net.base import test_http_connection, test_multiple_urls, find_best_mirror
except ImportError:
    # 开发环境中可能需要相对导入
    from base import test_http_connection, test_multiple_urls, find_best_mirror

# 设置日志
logger = logging.getLogger("test_net.pip_mirror")

# 默认pip镜像列表
DEFAULT_PIP_MIRRORS = {
    "PyPI官方": "https://pypi.org/simple/",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple/",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
    "TUNA清华": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "豆瓣": "https://pypi.douban.com/simple/",
    "网易": "https://mirrors.163.com/pypi/simple/",
    "USTC中科大": "https://pypi.mirrors.ustc.edu.cn/simple/"
}

class PipMirrorTester:
    """pip镜像测试工具类，提供图形界面测试不同pip镜像源的速度"""
    
    def __init__(self, root=None, callback=None):
        """
        初始化pip镜像测试器
        
        Args:
            root: tkinter根窗口，如果为None则创建新窗口
            callback: 测试完成后的回调函数，接收选定的镜像URL作为参数
        """
        self.mirrors = DEFAULT_PIP_MIRRORS.copy()
        self.callback = callback
        self.test_running = False
        self.test_thread = None
        self.result_data = {}
        
        # 加载自定义镜像
        self.load_custom_mirrors()
        
        # 创建UI
        self.create_window(root)
        self.create_widgets()
        
    def create_window(self, root):
        """创建窗口"""
        if root is None:
            self.root = tk.Toplevel()
            self.root.title("pip镜像测试")
            self.root.geometry("700x500")
            self.root.minsize(600, 400)
            self.is_toplevel = True
        else:
            self.root = root
            self.is_toplevel = False
            
        # 窗口关闭处理
        if self.is_toplevel:
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            
        
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部控制区域
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加镜像区域
        add_frame = ttk.LabelFrame(control_frame, text="添加自定义镜像")
        add_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 名称输入
        name_frame = ttk.Frame(add_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="名称:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # URL输入
        url_frame = ttk.Frame(add_frame)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.url_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 按钮区
        btn_frame = ttk.Frame(add_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="添加", command=self.add_mirror).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除选中", command=self.delete_mirror).pack(side=tk.LEFT)
        
        # 测试控制区域
        test_frame = ttk.LabelFrame(control_frame, text="测试控制")
        test_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 测试按钮行
        test_btn_frame = ttk.Frame(test_frame)
        test_btn_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(test_btn_frame, text="开始测试", command=self.start_test)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(test_btn_frame, text="停止测试", command=self.stop_test, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # 选择和应用行
        apply_frame = ttk.Frame(test_frame)
        apply_frame.pack(fill=tk.X, pady=5)
        
        self.use_best_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(apply_frame, text="使用最佳镜像", variable=self.use_best_var).pack(side=tk.LEFT)
        
        ttk.Button(apply_frame, text="应用选中", command=self.apply_selected).pack(side=tk.RIGHT)
        
        # 状态标签
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(status_frame, variable=self.progress_var, mode="determinate")
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 创建Treeview显示镜像列表和测试结果
        columns = ("name", "url", "status", "time", "result")
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.tree.heading("name", text="镜像名称")
        self.tree.heading("url", text="镜像URL")
        self.tree.heading("status", text="状态")
        self.tree.heading("time", text="响应时间(ms)")
        self.tree.heading("result", text="测试结果")
        
        # 设置列宽
        self.tree.column("name", width=100, minwidth=80)
        self.tree.column("url", width=250, minwidth=150)
        self.tree.column("status", width=80, minwidth=60)
        self.tree.column("time", width=100, minwidth=80)
        self.tree.column("result", width=150, minwidth=100)
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置Treeview和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # 填充镜像数据
        self.refresh_mirror_list()
        
    def refresh_mirror_list(self):
        """刷新镜像列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加镜像
        for name, url in self.mirrors.items():
            self.tree.insert("", tk.END, values=(name, url, "-", "-", "-"))
    
    def load_custom_mirrors(self):
        """加载自定义镜像"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings", "pip_mirrors.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    custom_mirrors = json.load(f)
                    if isinstance(custom_mirrors, dict):
                        # 更新镜像列表，保留默认镜像
                        for name, url in custom_mirrors.items():
                            self.mirrors[name] = url
                        logger.info(f"已加载{len(custom_mirrors)}个自定义pip镜像")
        except Exception as e:
            logger.error(f"加载自定义pip镜像失败: {str(e)}")
    
    def save_custom_mirrors(self):
        """保存自定义镜像"""
        try:
            # 仅保存非默认镜像
            custom_mirrors = {}
            for name, url in self.mirrors.items():
                if name not in DEFAULT_PIP_MIRRORS or url != DEFAULT_PIP_MIRRORS[name]:
                    custom_mirrors[name] = url
            
            # 创建settings目录（如果不存在）
            settings_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings")
            os.makedirs(settings_dir, exist_ok=True)
            
            # 保存到文件
            config_path = os.path.join(settings_dir, "pip_mirrors.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(custom_mirrors, f, ensure_ascii=False, indent=4)
                
            logger.info(f"已保存{len(custom_mirrors)}个自定义pip镜像")
        except Exception as e:
            logger.error(f"保存自定义pip镜像失败: {str(e)}")
            messagebox.showerror("错误", f"保存自定义镜像失败: {str(e)}")
    
    def add_mirror(self):
        """添加自定义镜像"""
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        
        if not name or not url:
            messagebox.showwarning("警告", "镜像名称和URL不能为空")
            return
        
        # 确保URL以斜杠结尾
        if not url.endswith("/"):
            url += "/"
        
        # 确保URL以http或https开头
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # 添加到列表
        self.mirrors[name] = url
        
        # 刷新列表
        self.refresh_mirror_list()
        
        # 清空输入框
        self.name_var.set("")
        self.url_var.set("")
        
        # 保存自定义镜像
        self.save_custom_mirrors()
    
    def delete_mirror(self):
        """删除选中的镜像"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的镜像")
            return
        
        # 获取镜像名称
        name = self.tree.item(selected[0])["values"][0]
        
        # 检查是否为默认镜像
        if name in DEFAULT_PIP_MIRRORS and self.mirrors[name] == DEFAULT_PIP_MIRRORS[name]:
            messagebox.showinfo("提示", "默认镜像不可删除")
            return
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除镜像 {name} 吗？"):
            # 从列表中删除
            if name in self.mirrors:
                del self.mirrors[name]
            
            # 刷新列表
            self.refresh_mirror_list()
            
            # 保存自定义镜像
            self.save_custom_mirrors()
    
    def start_test(self):
        """开始测试镜像"""
        if self.test_running:
            return
        
        self.test_running = True
        self.result_data = {}
        
        # 更新UI状态
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("正在测试镜像...")
        self.progress_var.set(0)
        
        # 重置测试结果
        for item in self.tree.get_children():
            self.tree.item(item, values=(
                self.tree.item(item)["values"][0],  # 名称
                self.tree.item(item)["values"][1],  # URL
                "等待中",                           # 状态
                "-",                                # 响应时间
                "-"                                 # 测试结果
            ))
        
        # 启动测试线程
        self.test_thread = threading.Thread(target=self.run_test, daemon=True)
        self.test_thread.start()
    
    def stop_test(self):
        """停止测试"""
        if not self.test_running:
            return
        
        self.test_running = False
        self.status_var.set("测试已停止")
        
        # 更新UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def run_test(self):
        """运行测试线程"""
        total = len(self.mirrors)
        count = 0
        
        # 测试每个镜像
        for item in self.tree.get_children():
            if not self.test_running:
                break
                
            # 获取镜像信息
            values = self.tree.item(item)["values"]
            name, url = values[0], values[1]
            
            # 更新状态
            self.update_mirror_status(item, "测试中", "-", "-")
            
            try:
                # 测试连接
                result = test_http_connection(url)
                
                if result["success"]:
                    status = "可用"
                    time_ms = f"{result['time']:.1f}"
                    result_text = f"状态码: {result['status_code']}"
                    
                    # 对于pip镜像，测试一个特定包以确认是否真正可用
                    # 选择requests包作为测试对象，因为它很流行
                    pkg_url = f"{url.rstrip('/')}/requests/"
                    pkg_result = test_http_connection(pkg_url)
                    
                    if pkg_result["success"]:
                        result_text += ", 包测试通过"
                    else:
                        status = "部分可用"
                        result_text += ", 包测试失败"
                else:
                    status = "不可用"
                    time_ms = "-"
                    result_text = result.get("error", "测试失败")
                
                # 保存结果
                self.result_data[name] = {
                    "url": url,
                    "success": result["success"],
                    "time": result.get("time", 0),
                    "status_code": result.get("status_code", 0),
                    "error": result.get("error", "")
                }
                
            except Exception as e:
                logger.error(f"测试镜像 {name} 时出错: {str(e)}")
                status = "错误"
                time_ms = "-"
                result_text = str(e)
                
                # 保存结果
                self.result_data[name] = {
                    "url": url,
                    "success": False,
                    "time": 0,
                    "error": str(e)
                }
            
            # 更新UI
            self.update_mirror_status(item, status, time_ms, result_text)
            
            # 更新进度
            count += 1
            self.progress_var.set(count / total * 100)
            
            # 暂停一下，避免请求过快
            time.sleep(0.5)
        
        # 测试完成
        self.test_running = False
        self.status_var.set("测试完成")
        
        # 根据响应时间排序
        self.sort_by_response_time()
        
        # 更新UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 选中最佳镜像
        self.select_best_mirror()
    
    def update_mirror_status(self, item, status, time_ms, result_text):
        """更新镜像状态（线程安全）"""
        # 需要在主线程中更新UI
        if self.root.winfo_exists():
            self.root.after(0, lambda: self.tree.item(item, values=(
                self.tree.item(item)["values"][0],  # 名称
                self.tree.item(item)["values"][1],  # URL
                status,                            # 状态
                time_ms,                           # 响应时间
                result_text                        # 测试结果
            )))
    
    def sort_by_response_time(self):
        """根据响应时间排序镜像"""
        items = [(item, self.tree.item(item)["values"]) for item in self.tree.get_children()]
        
        # 按响应时间排序，不可用的排在最后
        def get_time(item_values):
            status = item_values[2]
            if status not in ("可用", "部分可用"):
                return float('inf')
            
            try:
                return float(item_values[3])
            except (ValueError, TypeError):
                return float('inf')
        
        items.sort(key=lambda x: get_time(x[1]))
        
        # 重新插入排序后的项
        for item, _ in items:
            self.tree.move(item, "", tk.END)
    
    def select_best_mirror(self):
        """选择最佳镜像"""
        if not self.use_best_var.get():
            return
            
        # 找出最快的可用镜像
        best_item = None
        best_time = float('inf')
        
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            status = values[2]
            if status in ("可用", "部分可用"):
                try:
                    time_ms = float(values[3])
                    if time_ms < best_time:
                        best_time = time_ms
                        best_item = item
                except (ValueError, TypeError):
                    continue
        
        # 选中最佳镜像
        if best_item:
            self.tree.selection_set(best_item)
            self.tree.see(best_item)
    
    def apply_selected(self):
        """应用选中的镜像"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要应用的镜像")
            return
        
        # 获取镜像信息
        values = self.tree.item(selected[0])["values"]
        name, url = values[0], values[1]
        
        # 调用回调函数
        if self.callback:
            self.callback(name, url)
            
            if self.is_toplevel:
                messagebox.showinfo("成功", f"已选择镜像: {name}")
                self.root.destroy()
    
    def on_tree_double_click(self, event):
        """处理树形控件的双击事件"""
        # 获取点击的项
        item = self.tree.identify_row(event.y)
        if item:
            # 应用选中的镜像
            self.apply_selected()
    
    def on_close(self):
        """处理窗口关闭事件"""
        # 停止测试
        self.stop_test()
        
        # 关闭窗口
        if self.is_toplevel:
            self.root.destroy()

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("pip镜像测试")
    
    def on_mirror_selected(name, url):
        print(f"选择的镜像: {name}, URL: {url}")
    
    app = PipMirrorTester(root, callback=on_mirror_selected)
    
    root.mainloop()
