"""
Python设置面板，管理Python环境和版本
"""
import tkinter as tk
from tkinter import ttk, filedialog
import os
import logging
import sys
import subprocess

from settings.ui.base_panel import BaseSettingsPanel

class PythonSettingsPanel(BaseSettingsPanel):
    """
    Python设置面板类，管理Python版本和环境配置
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化Python设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.python_path_var = tk.StringVar()
        self.use_virtual_env_var = tk.BooleanVar()
        self.virtual_env_path_var = tk.StringVar()
        self.auto_activate_var = tk.BooleanVar()
        self.default_version_var = tk.StringVar()
        self.system_version_var = tk.StringVar(value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        self.custom_path_var = tk.BooleanVar()
        self.pip_mirror_var = tk.StringVar()
        self.use_pip_mirror_var = tk.BooleanVar()
        
        # 可用的Python版本列表
        self.available_versions = []
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置Python设置面板的用户界面"""
        # 当前Python信息
        info_frame = ttk.LabelFrame(self.main_container, text="当前Python信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 系统Python版本
        system_frame = ttk.Frame(info_frame)
        system_frame.pack(fill=tk.X, pady=5)
        
        system_label = ttk.Label(system_frame, text="系统Python版本:")
        system_label.pack(side=tk.LEFT, padx=5)
        
        system_value = ttk.Label(system_frame, textvariable=self.system_version_var)
        system_value.pack(side=tk.LEFT, padx=5)
        
        # 已安装的Python路径
        path_section, path_content = self.create_section_frame("Python路径设置")
        
        # 自定义Python路径
        custom_path_check = ttk.Checkbutton(path_content, text="使用自定义Python解释器", 
                                           variable=self.custom_path_var,
                                           command=self._toggle_path_fields)
        custom_path_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Python路径选择
        path_frame = ttk.Frame(path_content)
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = ttk.Label(path_frame, text="Python路径:")
        path_label.pack(side=tk.LEFT, padx=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.python_path_var)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(path_frame, text="浏览...", 
                                  command=self._browse_python_path)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # 验证按钮
        verify_frame = ttk.Frame(path_content)
        verify_frame.pack(fill=tk.X, pady=5)
        
        verify_button = ttk.Button(verify_frame, text="验证Python路径", 
                                  command=self._verify_python_path)
        verify_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新可用Python版本
        refresh_button = ttk.Button(verify_frame, text="刷新可用版本", 
                                   command=self._refresh_python_versions)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 虚拟环境设置
        venv_section, venv_content = self.create_section_frame("虚拟环境设置")
        
        # 使用虚拟环境
        venv_check = ttk.Checkbutton(venv_content, text="使用虚拟环境", 
                                    variable=self.use_virtual_env_var,
                                    command=self._toggle_venv_fields)
        venv_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 虚拟环境路径
        venv_frame = ttk.Frame(venv_content)
        venv_frame.pack(fill=tk.X, pady=5)
        
        venv_label = ttk.Label(venv_frame, text="虚拟环境路径:")
        venv_label.pack(side=tk.LEFT, padx=5)
        
        venv_entry = ttk.Entry(venv_frame, textvariable=self.virtual_env_path_var)
        venv_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        venv_browse = ttk.Button(venv_frame, text="浏览...", 
                                command=self._browse_venv_path)
        venv_browse.pack(side=tk.LEFT, padx=5)
        
        # 自动激活虚拟环境
        auto_activate_check = ttk.Checkbutton(venv_content, text="启动时自动激活虚拟环境", 
                                             variable=self.auto_activate_var)
        auto_activate_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 创建虚拟环境按钮
        create_venv_button = ttk.Button(venv_content, text="创建新虚拟环境", 
                                       command=self._create_virtual_env)
        create_venv_button.pack(anchor=tk.W, padx=5, pady=5)
        
        # pip设置
        pip_section, pip_content = self.create_section_frame("pip设置")
        
        # 使用镜像
        mirror_check = ttk.Checkbutton(pip_content, text="使用pip镜像源", 
                                      variable=self.use_pip_mirror_var,
                                      command=self._toggle_mirror_field)
        mirror_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 镜像URL
        mirror_frame = ttk.Frame(pip_content)
        mirror_frame.pack(fill=tk.X, pady=5)
        
        mirror_label = ttk.Label(mirror_frame, text="镜像URL:")
        mirror_label.pack(side=tk.LEFT, padx=5)
        
        # 常用镜像列表
        mirrors = [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.aliyun.com/pypi/simple",
            "https://pypi.doubanio.com/simple",
            "https://pypi.mirrors.ustc.edu.cn/simple"
        ]
        
        mirror_combo = ttk.Combobox(mirror_frame, textvariable=self.pip_mirror_var, 
                                   values=mirrors)
        mirror_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # Python路径设置
            self.custom_path_var.set(self.settings_manager.get("python.use_custom_path", False))
            self.python_path_var.set(self.settings_manager.get("python.path", sys.executable))
            
            # 虚拟环境设置
            self.use_virtual_env_var.set(self.settings_manager.get("python.use_virtual_env", False))
            
            venv_path = self.settings_manager.get("python.virtual_env_path", "")
            if not venv_path and "VIRTUAL_ENV" in os.environ:
                venv_path = os.environ["VIRTUAL_ENV"]
            self.virtual_env_path_var.set(venv_path)
            
            self.auto_activate_var.set(self.settings_manager.get("python.auto_activate_venv", True))
            
            # pip设置
            self.use_pip_mirror_var.set(self.settings_manager.get("python.use_pip_mirror", False))
            self.pip_mirror_var.set(self.settings_manager.get("python.pip_mirror", 
                                                           "https://pypi.tuna.tsinghua.edu.cn/simple"))
            
            # 更新界面状态
            self._toggle_path_fields()
            self._toggle_venv_fields()
            self._toggle_mirror_field()
            
            # 获取可用Python版本
            self._refresh_python_versions(silent=True)
            
            logging.debug("Python设置加载成功")
        except Exception as e:
            logging.error(f"加载Python设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # Python路径设置
            self.settings_manager.set("python.use_custom_path", self.custom_path_var.get())
            
            # 如果启用了自定义路径，验证Python路径
            if self.custom_path_var.get():
                python_path = self.python_path_var.get().strip()
                if not python_path or not os.path.exists(python_path):
                    logging.error("Python路径无效")
                    return False
                self.settings_manager.set("python.path", python_path)
            
            # 虚拟环境设置
            self.settings_manager.set("python.use_virtual_env", self.use_virtual_env_var.get())
            
            # 如果启用了虚拟环境，验证虚拟环境路径
            if self.use_virtual_env_var.get():
                venv_path = self.virtual_env_path_var.get().strip()
                if not venv_path or not os.path.exists(venv_path):
                    logging.error("虚拟环境路径无效")
                    return False
                self.settings_manager.set("python.virtual_env_path", venv_path)
            
            self.settings_manager.set("python.auto_activate_venv", self.auto_activate_var.get())
            
            # pip设置
            self.settings_manager.set("python.use_pip_mirror", self.use_pip_mirror_var.get())
            self.settings_manager.set("python.pip_mirror", self.pip_mirror_var.get())
            
            logging.debug("Python设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存Python设置时出错: {e}")
            return False
    
    def _toggle_path_fields(self):
        """根据自定义路径选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "Python路径设置" in child.cget("text"):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame):
                            for widget in frame.winfo_children():
                                if isinstance(widget, (ttk.Entry, ttk.Button)):
                                    if self.custom_path_var.get():
                                        widget.configure(state="normal")
                                    else:
                                        widget.configure(state="disabled")
    
    def _toggle_venv_fields(self):
        """根据虚拟环境选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "虚拟环境设置" in child.cget("text"):
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for w in widget.winfo_children():
                                if isinstance(w, (ttk.Entry, ttk.Button)):
                                    if self.use_virtual_env_var.get():
                                        w.configure(state="normal")
                                    else:
                                        w.configure(state="disabled")
                        elif isinstance(widget, ttk.Checkbutton) and "自动激活" in widget.cget("text"):
                            if self.use_virtual_env_var.get():
                                widget.configure(state="normal")
                            else:
                                widget.configure(state="disabled")
    
    def _toggle_mirror_field(self):
        """根据镜像选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "pip设置" in child.cget("text"):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame):
                            for widget in frame.winfo_children():
                                if isinstance(widget, ttk.Combobox):
                                    if self.use_pip_mirror_var.get():
                                        widget.configure(state="normal")
                                    else:
                                        widget.configure(state="disabled")
    
    def _browse_python_path(self):
        """选择Python解释器路径"""
        from tkinter import filedialog
        
        # 获取初始目录
        initial_dir = os.path.dirname(self.python_path_var.get())
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.dirname(sys.executable)
            
        # 打开文件对话框
        file_types = [("Python解释器", "python*.exe" if sys.platform == "win32" else "python*")]
        path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="选择Python解释器",
            filetypes=file_types
        )
        
        if path:
            self.python_path_var.set(path)
            # 自动验证
            self._verify_python_path()
    
    def _browse_venv_path(self):
        """选择虚拟环境路径"""
        from tkinter import filedialog
        
        # 获取初始目录
        initial_dir = self.virtual_env_path_var.get()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
            
        # 打开目录对话框
        path = filedialog.askdirectory(
            initialdir=initial_dir,
            title="选择虚拟环境目录"
        )
        
        if path:
            self.virtual_env_path_var.set(path)
            # 验证路径
            self._verify_venv_path(path)
    
    def _verify_python_path(self):
        """验证Python解释器路径"""
        from tkinter import messagebox
        
        path = self.python_path_var.get().strip()
        if not path:
            messagebox.showerror("验证失败", "Python路径不能为空")
            return
            
        if not os.path.exists(path):
            messagebox.showerror("验证失败", f"路径不存在: {path}")
            return
            
        try:
            # 尝试运行Python并获取版本
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            version_output = result.stdout.strip() or result.stderr.strip()
            messagebox.showinfo("验证成功", f"Python解释器有效\n{version_output}")
            logging.info(f"验证Python路径成功: {path}, 版本: {version_output}")
        except Exception as e:
            messagebox.showerror("验证失败", f"无法执行Python解释器: {e}")
            logging.error(f"验证Python路径失败: {e}")
    
    def _verify_venv_path(self, path=None):
        """验证虚拟环境路径"""
        from tkinter import messagebox
        
        if path is None:
            path = self.virtual_env_path_var.get().strip()
            
        if not path:
            return False
            
        if not os.path.exists(path):
            messagebox.showerror("验证失败", f"虚拟环境路径不存在: {path}")
            return False
            
        # 检查是否是有效的虚拟环境
        activate_script = os.path.join(
            path, 
            "Scripts" if sys.platform == "win32" else "bin",
            "activate"
        )
        
        python_exec = os.path.join(
            path, 
            "Scripts" if sys.platform == "win32" else "bin",
            "python" + (".exe" if sys.platform == "win32" else "")
        )
        
        if not os.path.exists(activate_script) or not os.path.exists(python_exec):
            messagebox.showerror("验证失败", f"无效的虚拟环境: {path}\n找不到激活脚本或Python解释器")
            return False
            
        return True
    
    def _create_virtual_env(self):
        """创建新的虚拟环境"""
        from tkinter import simpledialog, messagebox
        
        # 询问虚拟环境名称和路径
        venv_name = simpledialog.askstring("创建虚拟环境", "请输入虚拟环境名称:")
        if not venv_name:
            return
            
        # 询问路径
        default_path = os.path.join(os.path.expanduser("~"), "venvs")
        if not os.path.exists(default_path):
            try:
                os.makedirs(default_path)
            except:
                pass
                
        venv_dir = filedialog.askdirectory(
            initialdir=default_path,
            title="选择虚拟环境保存目录"
        )
        
        if not venv_dir:
            return
            
        venv_path = os.path.join(venv_dir, venv_name)
        
        # 检查路径是否已存在
        if os.path.exists(venv_path):
            messagebox.showerror("错误", f"目录已存在: {venv_path}")
            return
            
        # 创建虚拟环境
        try:
            # 确定使用哪个Python来创建虚拟环境
            python_path = sys.executable
            if self.custom_path_var.get():
                custom_path = self.python_path_var.get().strip()
                if custom_path and os.path.exists(custom_path):
                    python_path = custom_path
            
            # 弹出进度窗口
            progress = tk.Toplevel(self)
            progress.title("创建虚拟环境")
            progress.geometry("400x150")
            progress.transient(self.winfo_toplevel())
            progress.grab_set()
            
            # 进度提示
            message_label = ttk.Label(progress, text=f"正在创建虚拟环境: {venv_path}\n请稍候...")
            message_label.pack(pady=20)
            
            progress_bar = ttk.Progressbar(progress, mode="indeterminate")
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            # 使用线程创建虚拟环境
            import threading
            
            def create_venv_thread():
                try:
                    logging.info(f"开始创建虚拟环境: {venv_path}")
                    cmd = [python_path, "-m", "venv", venv_path]
                    logging.info(f"执行命令: {cmd}")
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        error = result.stderr or "未知错误"
                        logging.error(f"创建虚拟环境失败: {error}")
                        messagebox.showerror("创建失败", f"创建虚拟环境失败:\n{error}")
                    else:
                        logging.info(f"创建虚拟环境成功: {venv_path}")
                        messagebox.showinfo("创建成功", f"虚拟环境已创建: {venv_path}")
                        # 更新虚拟环境路径
                        self.virtual_env_path_var.set(venv_path)
                        # 自动勾选使用虚拟环境
                        self.use_virtual_env_var.set(True)
                        self._toggle_venv_fields()
                except Exception as e:
                    logging.error(f"创建虚拟环境时出错: {e}")
                    messagebox.showerror("创建失败", f"创建虚拟环境时出错:\n{str(e)}")
                finally:
                    # 关闭进度窗口
                    progress.destroy()
            
            # 启动线程
            thread = threading.Thread(target=create_venv_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logging.error(f"创建虚拟环境时出错: {e}")
            messagebox.showerror("创建失败", f"创建虚拟环境时出错:\n{str(e)}")
    
    def _refresh_python_versions(self, silent=False):
        """刷新系统中可用的Python版本"""
        from tkinter import messagebox
        import re
        
        self.available_versions = []
        
        try:
            search_paths = []
            
            # 获取PATH环境变量中的路径
            if "PATH" in os.environ:
                search_paths.extend(os.environ["PATH"].split(os.pathsep))
                
            # 在Windows上检查Python安装目录
            if sys.platform == "win32":
                program_files = [
                    os.environ.get("ProgramFiles", "C:\\Program Files"),
                    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                    os.environ.get("LocalAppData", "") + "\\Programs"
                ]
                
                for pf in program_files:
                    if os.path.exists(pf):
                        python_dirs = [os.path.join(pf, d) for d in os.listdir(pf) 
                                      if d.startswith("Python")]
                        search_paths.extend(python_dirs)
            
            # 在类Unix系统上检查常见Python位置
            else:
                search_paths.extend([
                    "/usr/bin",
                    "/usr/local/bin",
                    os.path.expanduser("~/.local/bin")
                ])
                
            # 查找Python可执行文件
            python_execs = []
            pattern = re.compile(r"python(\d+(\.\d+)*)?(.exe)?$", re.IGNORECASE)
            
            for path in search_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    for file in os.listdir(path):
                        if pattern.match(file):
                            python_path = os.path.join(path, file)
                            if python_path not in python_execs and os.path.isfile(python_path):
                                python_execs.append(python_path)
            
            # 检查每个Python版本
            found_versions = []
            for python_exec in python_execs:
                try:
                    result = subprocess.run(
                        [python_exec, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    version_output = result.stdout.strip() or result.stderr.strip()
                    if version_output and "Python" in version_output:
                        found_versions.append({
                            "path": python_exec,
                            "version": version_output
                        })
                except:
                    pass
            
            # 保存找到的版本
            self.available_versions = found_versions
            
            if not silent:
                if found_versions:
                    # 创建版本选择对话框
                    version_window = tk.Toplevel(self)
                    version_window.title("可用Python版本")
                    version_window.geometry("500x300")
                    version_window.transient(self.winfo_toplevel())
                    version_window.grab_set()
                    
                    # 说明标签
                    info_label = ttk.Label(version_window, 
                                         text="以下是系统中找到的Python版本，双击选择要使用的版本:")
                    info_label.pack(padx=10, pady=10, anchor=tk.W)
                    
                    # 版本列表
                    list_frame = ttk.Frame(version_window)
                    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                    
                    # 创建Treeview
                    columns = ("version", "path")
                    tree = ttk.Treeview(list_frame, columns=columns, show="headings")
                    tree.heading("version", text="Python版本")
                    tree.heading("path", text="路径")
                    
                    tree.column("version", width=150)
                    tree.column("path", width=350)
                    
                    for i, v in enumerate(found_versions):
                        tree.insert("", "end", values=(v["version"], v["path"]))
                    
                    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    
                    # 滚动条
                    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    tree.configure(yscrollcommand=scrollbar.set)
                    
                    # 双击选择
                    def on_tree_double_click(event):
                        selected_item = tree.selection()[0]
                        path = tree.item(selected_item, "values")[1]
                        self.python_path_var.set(path)
                        self.custom_path_var.set(True)
                        self._toggle_path_fields()
                        version_window.destroy()
                    
                    tree.bind("<Double-1>", on_tree_double_click)
                    
                    # 关闭按钮
                    close_button = ttk.Button(version_window, text="关闭", 
                                            command=version_window.destroy)
                    close_button.pack(pady=10)
                    
                else:
                    messagebox.showinfo("刷新版本", "未找到其他Python版本")
            
        except Exception as e:
            logging.error(f"刷新Python版本时出错: {e}")
            if not silent:
                messagebox.showerror("刷新失败", f"刷新Python版本列表时出错:\n{str(e)}") 