"""
Python版本管理面板，用于管理多个Python安装和设置默认版本
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os
import subprocess
import sys
import platform
import json

from settings.ui.base_panel import BaseSettingsPanel

class PythonSettingsPanel(BaseSettingsPanel):
    """
    Python版本管理面板类，管理多个Python安装和设置默认版本
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化Python版本管理面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.installations = []  # 存储Python安装信息列表
        self.default_version_var = tk.StringVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置Python版本管理面板的用户界面"""
        # 已安装的Python版本
        installed_section, installed_content = self.create_section_frame("已安装的Python版本")
        
        # 创建版本列表框架
        list_frame = ttk.Frame(installed_content)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建版本列表
        columns = ("名称", "版本", "路径", "默认")
        self.version_tree = ttk.Treeview(list_frame, columns=columns, show="headings", 
                                       selectmode="browse", height=6)
        
        # 设置列标题
        for col in columns:
            self.version_tree.heading(col, text=col)
            
        # 设置列宽
        self.version_tree.column("名称", width=100)
        self.version_tree.column("版本", width=100)
        self.version_tree.column("路径", width=250)
        self.version_tree.column("默认", width=50)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置组件
        self.version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(installed_content)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 添加按钮
        add_button = ttk.Button(button_frame, text="添加", command=self._add_python)
        add_button.pack(side=tk.LEFT, padx=5)
        
        # 移除按钮
        remove_button = ttk.Button(button_frame, text="移除", command=self._remove_python)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        # 设为默认按钮
        default_button = ttk.Button(button_frame, text="设为默认", command=self._set_as_default)
        default_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(button_frame, text="刷新", command=self._refresh_python_list)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 系统Python版本信息框架
        system_section, system_content = self.create_section_frame("系统Python信息")
        
        # 当前Python版本信息
        info_text = f"当前Python版本: {platform.python_version()}\n"
        info_text += f"Python路径: {sys.executable}\n"
        info_text += f"平台: {platform.platform()}"
        
        info_label = ttk.Label(system_content, text=info_text)
        info_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # 添加一个按钮来自动检测系统中的Python版本
        detect_button = ttk.Button(system_content, text="自动检测系统中的Python版本", 
                                 command=self._detect_python_installations)
        detect_button.pack(anchor=tk.W, padx=5, pady=5)
    
    def _add_python(self):
        """添加Python安装"""
        if sys.platform == 'darwin':  # macOS
            filetypes = [("Python", "python*"), ("Python应用", "*.app"), ("所有文件", "*")]
        else:  # Windows或Linux
            filetypes = [("Python可执行文件", "python*"), ("所有文件", "*")]
        
        python_path = filedialog.askopenfilename(
            title="选择Python可执行文件",
            filetypes=filetypes
        )
        
        if not python_path:
            return
            
        # 验证所选路径是否为有效的Python可执行文件
        if not self._is_valid_python(python_path):
            messagebox.showerror("错误", "所选文件不是有效的Python可执行文件")
            return
        
        # 获取Python版本信息
        python_version = self._get_python_version(python_path)
        if not python_version:
            messagebox.showerror("错误", "无法获取Python版本信息")
            return
        
        # 创建一个对话框让用户输入此Python安装的名称
        name = self._prompt_installation_name(python_version)
        if not name:
            return
        
        # 检查是否已经添加过此路径
        for installation in self.installations:
            if installation["path"] == python_path:
                messagebox.showinfo("提示", "此Python安装已在列表中")
                return
        
        # 添加到安装列表
        new_installation = {
            "name": name,
            "version": python_version,
            "path": python_path,
            "default": len(self.installations) == 0  # 如果是第一个添加的，设为默认
        }
        
        self.installations.append(new_installation)
        
        # 更新UI
        self._update_python_list()
        
        # 如果这是第一个添加的Python，设置为默认版本
        if len(self.installations) == 1:
            self.default_version_var.set(name)
    
    def _remove_python(self):
        """移除所选的Python安装"""
        selected_item = self.version_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要移除的Python安装")
            return
        
        # 获取选中项的索引
        index = self.version_tree.index(selected_item[0])
        
        # 检查是否为默认安装
        if self.installations[index]["default"]:
            if len(self.installations) > 1:
                messagebox.showerror("错误", "无法移除默认Python安装，请先设置其他版本为默认")
                return
        
        # 从列表中移除
        del self.installations[index]
        
        # 更新UI
        self._update_python_list()
    
    def _set_as_default(self):
        """将所选Python安装设置为默认版本"""
        selected_item = self.version_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要设为默认的Python安装")
            return
        
        # 获取选中项的索引
        index = self.version_tree.index(selected_item[0])
        
        # 取消原默认设置
        for installation in self.installations:
            installation["default"] = False
        
        # 设置新的默认版本
        self.installations[index]["default"] = True
        self.default_version_var.set(self.installations[index]["name"])
        
        # 更新UI
        self._update_python_list()
    
    def _refresh_python_list(self):
        """刷新Python安装列表"""
        self._update_python_list()
    
    def _is_valid_python(self, path):
        """检查路径是否为有效的Python可执行文件"""
        try:
            result = subprocess.run(
                [path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return "Python" in result.stdout or "Python" in result.stderr
        except Exception as e:
            logging.error(f"验证Python路径时出错: {e}")
            return False
    
    def _get_python_version(self, path):
        """获取Python版本信息"""
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # 版本信息可能在stdout或stderr中
            version_str = result.stdout or result.stderr
            
            # 提取版本号 (通常格式为 "Python X.Y.Z")
            if "Python" in version_str:
                return version_str.strip().split(" ")[1]
            return None
        except Exception as e:
            logging.error(f"获取Python版本时出错: {e}")
            return None
    
    def _prompt_installation_name(self, version):
        """提示用户输入Python安装名称"""
        from tkinter import simpledialog
        
        default_name = f"Python {version}"
        
        # 检查名称是否已存在
        i = 1
        while any(inst["name"] == default_name for inst in self.installations):
            default_name = f"Python {version} ({i})"
            i += 1
        
        name = simpledialog.askstring(
            "Python安装名称", 
            "请为此Python安装输入一个名称:",
            initialvalue=default_name
        )
        
        return name
    
    def _update_python_list(self):
        """更新Python安装列表显示"""
        # 清空当前列表
        for item in self.version_tree.get_children():
            self.version_tree.delete(item)
        
        # 添加安装到列表
        for installation in self.installations:
            default_mark = "✓" if installation["default"] else ""
            self.version_tree.insert("", "end", values=(
                installation["name"],
                installation["version"],
                installation["path"],
                default_mark
            ))
    
    def _detect_python_installations(self):
        """自动检测系统中的Python安装"""
        detected = []
        
        # 在macOS上检测Python
        if sys.platform == 'darwin':
            # 检查常见的Python安装路径
            common_paths = [
                "/usr/bin/python3",
                "/usr/local/bin/python3",
                "/opt/homebrew/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/*/bin/python3"
            ]
            
            # 也检查pyenv安装
            home = os.path.expanduser("~")
            pyenv_path = os.path.join(home, ".pyenv/versions/*/bin/python")
            common_paths.append(pyenv_path)
            
            # 检查Anaconda/Miniconda安装
            conda_paths = [
                os.path.join(home, "anaconda3/bin/python"),
                os.path.join(home, "miniconda3/bin/python")
            ]
            common_paths.extend(conda_paths)
            
            # 使用which查找python和python3
            try:
                which_python = subprocess.check_output(["which", "python"], text=True).strip()
                which_python3 = subprocess.check_output(["which", "python3"], text=True).strip()
                common_paths.extend([which_python, which_python3])
            except Exception:
                pass
        
        # 在Windows上检测Python
        elif sys.platform == 'win32':
            # 检查常见的Python安装路径
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            common_paths = [
                os.path.join(program_files, "Python*\\python.exe"),
                os.path.join(program_files_x86, "Python*\\python.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs\\Python\\Python*\\python.exe")
            ]
            
            # 检查Anaconda/Miniconda安装
            user_profile = os.environ.get("USERPROFILE", "")
            conda_paths = [
                os.path.join(user_profile, "anaconda3\\python.exe"),
                os.path.join(user_profile, "miniconda3\\python.exe")
            ]
            common_paths.extend(conda_paths)
        
        # 在Linux上检测Python
        else:
            # 检查常见的Python安装路径
            common_paths = [
                "/usr/bin/python3",
                "/usr/local/bin/python3"
            ]
            
            # 检查可能的Python版本
            for i in range(5, 12):  # Python 3.5 到 3.11
                common_paths.append(f"/usr/bin/python3.{i}")
                common_paths.append(f"/usr/local/bin/python3.{i}")
            
            # 检查pyenv安装
            home = os.path.expanduser("~")
            pyenv_path = os.path.join(home, ".pyenv/versions/*/bin/python")
            common_paths.append(pyenv_path)
            
            # 检查Anaconda/Miniconda安装
            conda_paths = [
                os.path.join(home, "anaconda3/bin/python"),
                os.path.join(home, "miniconda3/bin/python")
            ]
            common_paths.extend(conda_paths)
            
            # 使用which查找python和python3
            try:
                which_python = subprocess.check_output(["which", "python"], text=True).strip()
                which_python3 = subprocess.check_output(["which", "python3"], text=True).strip()
                common_paths.extend([which_python, which_python3])
            except Exception:
                pass
        
        # 检查每个路径
        import glob
        for path_pattern in common_paths:
            for path in glob.glob(path_pattern):
                # 确保路径唯一
                if path in [d["path"] for d in detected]:
                    continue
                    
                # 验证Python路径并获取版本
                if self._is_valid_python(path):
                    version = self._get_python_version(path)
                    if version:
                        detected.append({
                            "path": path,
                            "version": version
                        })
        
        # 如果没有检测到任何Python安装
        if not detected:
            messagebox.showinfo("结果", "未检测到任何Python安装")
            return
        
        # 显示结果并询问用户要添加哪些安装
        self._show_detected_installations(detected)
    
    def _show_detected_installations(self, detected):
        """显示检测到的Python安装并让用户选择要添加的安装"""
        # 创建一个新的对话框
        dialog = tk.Toplevel(self)
        dialog.title("检测到的Python安装")
        dialog.transient(self)
        dialog.grab_set()
        
        # 设置对话框大小
        dialog.geometry("600x400")
        
        # 创建说明标签
        ttk.Label(dialog, text="选择要添加的Python安装:").pack(padx=10, pady=10, anchor=tk.W)
        
        # 创建一个框架来容纳复选框
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建一个可滚动的画布
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建复选框变量和标签
        checkboxes = []
        for i, installation in enumerate(detected):
            var = tk.BooleanVar(value=True)  # 默认选中
            cb = ttk.Checkbutton(scrollable_frame, variable=var)
            cb.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            path_label = ttk.Label(scrollable_frame, text=f"{installation['path']} (Python {installation['version']})")
            path_label.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            
            checkboxes.append((var, installation))
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 添加按钮
        add_button = ttk.Button(button_frame, text="添加所选",
                              command=lambda: self._add_selected_installations(checkboxes, dialog))
        add_button.pack(side=tk.RIGHT, padx=5)
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消",
                                 command=dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _add_selected_installations(self, checkboxes, dialog):
        """添加用户选择的Python安装"""
        for var, installation in checkboxes:
            if var.get():  # 如果复选框被选中
                path = installation["path"]
                version = installation["version"]
                
                # 检查是否已经添加过此路径
                if any(inst["path"] == path for inst in self.installations):
                    continue
                
                # 创建一个名称
                name = f"Python {version}"
                i = 1
                while any(inst["name"] == name for inst in self.installations):
                    name = f"Python {version} ({i})"
                    i += 1
                
                # 添加到安装列表
                new_installation = {
                    "name": name,
                    "version": version,
                    "path": path,
                    "default": len(self.installations) == 0  # 如果是第一个添加的，设为默认
                }
                
                self.installations.append(new_installation)
        
        # 更新UI
        self._update_python_list()
        
        # 关闭对话框
        dialog.destroy()
        
        # 如果添加了新的安装，显示提示
        if self.installations:
            messagebox.showinfo("成功", "已添加所选Python安装")
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 加载Python安装列表
            installations = self.settings_manager.get("python_versions.installations", [])
            
            # 确保是列表类型
            if isinstance(installations, str):
                try:
                    # 尝试将字符串解析为JSON
                    installations = json.loads(installations)
                except:
                    logging.error("Python安装信息格式错误，重置为空列表")
                    installations = []
            
            # 如果仍然不是列表，设置为空列表
            if not isinstance(installations, list):
                logging.error(f"Python安装信息类型错误: {type(installations)}，重置为空列表")
                installations = []
                
            self.installations = installations
            
            # 加载默认版本
            default_version = self.settings_manager.get("python_versions.default_version", "")
            self.default_version_var.set(default_version)
            
            # 更新UI
            self._update_python_list()
            
            logging.debug("Python版本设置加载成功")
        except Exception as e:
            logging.error(f"加载Python版本设置时出错: {e}")
            self.installations = []
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 保存Python安装列表
            self.settings_manager.set("python_versions.installations", self.installations)
            
            # 保存默认版本
            self.settings_manager.set("python_versions.default_version", self.default_version_var.get())
            
            logging.debug("Python版本设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存Python版本设置时出错: {e}")
            return False 