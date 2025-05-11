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
        self.python_installations = []  # 存储Python安装信息列表(兼容旧代码)
        self.default_version_var = tk.StringVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
        self.setup_ui()
        self.load_settings()
    
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
        self.default_button = ttk.Button(button_frame, text="设为默认", command=self._set_as_default)
        self.default_button.pack(side=tk.LEFT, padx=5)
        
        # 为版本树添加选择事件
        self.version_tree.bind("<<TreeviewSelect>>", self._on_version_select)
        
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
        # 首先尝试自动添加系统Python
        system_python = sys.executable
        if system_python and system_python not in [i["path"] for i in self.installations]:
            if self._is_valid_python(system_python):
                python_version = self._get_python_version(system_python)
                if python_version:
                    name = f"系统Python {python_version}"
                    new_installation = {
                        "name": name,
                        "version": python_version,
                        "path": system_python,
                        "default": len(self.installations) == 0
                    }
                    self.installations.append(new_installation)
                    self._update_python_list()
                    if len(self.installations) == 1:
                        self.default_version_var.set(name)
                    return
        
        
        if sys.platform == 'darwin':  
            filetypes = [("Python", "python*"), ("Python应用", "*.app"), ("所有文件", "*")]
        else:  
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
    
    def _on_version_select(self, event):
        """当选择版本树中的项目时更新按钮文本"""
        selected_item = self.version_tree.selection()
        if not selected_item:
            return

        index = self.version_tree.index(selected_item[0])
        if not (0 <= index < len(self.installations)):
            return

        selected_installation = self.installations[index]
        
        # 根据选中项的默认状态更新按钮文本
        if selected_installation["default"]:
            self.default_button.config(text="解除默认")
        else:
            self.default_button.config(text="设为默认")
    
    def _set_as_default(self):
        """将所选Python安装设置为默认版本或取消默认"""
        selected_item = self.version_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择一个Python安装")
            return

        index = self.version_tree.index(selected_item[0])
        if not (0 <= index < len(self.installations)):
            messagebox.showerror("错误", "无效的Python安装索引")
            return

        selected_installation = self.installations[index]
        logging.info(f"开始设置Python版本为默认: {selected_installation['path']}")

        if selected_installation["default"]:
            # 如果当前选中的已经是默认，则取消默认
            logging.info(f"取消Python版本的默认状态: {selected_installation['path']}")
            selected_installation["default"] = False
            self.default_button.config(text="设为默认")
            # 更新所有版本的状态
            for inst in self.installations:
                if inst["path"] == selected_installation["path"]:
                    inst["default"] = False
                    logging.info(f"清除相同路径版本的默认标记: {inst['path']}")
            # 确保settings.json也被更新
            self.settings_manager.set("python.default", None)
        else:
            # 将其他所有版本设置为非默认
            logging.info("设置新默认Python版本，清除其他所有版本的默认标记")
            for inst in self.installations:
                inst["default"] = False
            # 将选定版本设置为默认
            selected_installation["default"] = True
            self.default_button.config(text="解除默认")
            # 更新settings.json
            self.settings_manager.set("python.default", selected_installation["path"])

        logging.info("更新Python列表并保存设置")
        self._update_python_list()
        self.save_settings()
        logging.info("设置保存完成")

    def _ensure_default_exists_or_set_system_default(self):
        """确保至少有一个默认Python版本，如果没有，则尝试设置系统Python或列表中的第一个。"""
        default_exists = any(inst.get("default", False) for inst in self.installations)

        if not default_exists:
            system_python_path = sys.executable
            system_python_in_list = None
            for inst in self.installations:
                if inst["path"] == system_python_path:
                    system_python_in_list = inst
                    break
            
            if system_python_in_list:
                system_python_in_list["default"] = True
                logging.info(f"没有默认Python，已将系统Python '{system_python_in_list['name']}' 设为默认。")
            elif self.installations: # 如果系统Python不在列表中，但列表不为空
                self.installations[0]["default"] = True # 将第一个设为默认
                logging.info(f"没有默认Python，已将列表中的第一个Python '{self.installations[0]['name']}' 设为默认。")
            # else: 列表为空，无需操作

        # 确保只有一个默认值，以防万一逻辑出错导致多个默认
        found_one_default = False
        for inst in self.installations:
            if inst.get("default", False):
                if found_one_default:
                    inst["default"] = False # 只保留第一个找到的默认
                else:
                    found_one_default = True

    def _remove_python(self):
        """移除所选的Python安装"""
        selected_item = self.version_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要移除的Python安装")
            return
        
        index = self.version_tree.index(selected_item[0])

        was_default = self.installations[index]["default"]
        del self.installations[index]
        
        if was_default:
            self._ensure_default_exists_or_set_system_default()
            
        self._update_python_list()
        self.save_settings()

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
            
        # 系统Python（如果需要显示）应该首先被添加到 self.installations 列表中（例如通过"添加"或"自动检测"功能），
        # 然后会通过上面的循环自动渲染到列表中。直接在此处向 version_tree 添加会导致UI与数据模型不一致。
        
        # 更新按钮文本
        selected_items = self.version_tree.selection()
        if selected_items:
            # 如果有选中项，根据其默认状态更新按钮文本
            index = self.version_tree.index(selected_items[0])
            if 0 <= index < len(self.installations):
                if self.installations[index]["default"]:
                    self.default_button.config(text="解除默认")
                else:
                    self.default_button.config(text="设为默认")
        else:
            # 如果没有选中项，默认显示"设为默认"
            self.default_button.config(text="设为默认")
    
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
        """从设置管理器加载设置，并确保数据完整性"""
        try:
            installations_data = self.settings_manager.get("python_versions.installations", [])
            default_version_name_from_settings = self.settings_manager.get("python_versions.default_version", "")

            if isinstance(installations_data, str):
                try:
                    installations_data = json.loads(installations_data)
                except json.JSONDecodeError:
                    logging.error("Python安装信息JSON格式错误，重置为空列表")
                    installations_data = []
            
            if not isinstance(installations_data, list):
                logging.error(f"Python安装信息类型错误 (应为列表): {type(installations_data)}，重置为空列表")
                installations_data = []

            self.installations = []  # 清空以重新填充
            processed_names = set() # 用于确保名称唯一性

            for i, inst_data in enumerate(installations_data):
                if not isinstance(inst_data, dict):
                    logging.warning(f"跳过无效的安装条目 (非字典类型): {inst_data}")
                    continue

                path = inst_data.get("path")
                version = inst_data.get("version") # 版本可能缺失
                name = inst_data.get("name")
                is_default_from_file = inst_data.get("default", False) # 保留原始default标记，稍后处理

                if not path: # 路径是必需的
                    logging.warning(f"跳过缺少路径的安装条目: {inst_data}")
                    continue

                if not name: # 如果名称不存在，则生成一个
                    if version:
                        base_name = f"Python {version}"
                    elif path: # 尝试从路径生成一个基础名称
                        # 尝试使用路径的最后两部分，或者只是文件名
                        dir_name = os.path.basename(os.path.dirname(path))
                        file_name = os.path.basename(path)
                        if dir_name and dir_name.lower() != "bin" and dir_name != file_name:
                            base_name = f"{dir_name} ({file_name})"
                        else:
                            base_name = f"{file_name}"
                    else: # 不应该发生，因为path是必需的
                        base_name = f"Python安装 {i+1}"
                    
                    # 确保生成的名称唯一
                    name = base_name
                    counter = 1
                    while name in processed_names:
                        name = f"{base_name} ({counter})"
                        counter += 1
                    logging.info(f"为路径 '{path}' 生成了名称 '{name}'")
                
                processed_names.add(name)
                self.installations.append({
                    "name": name,
                    "version": version,
                    "path": path,
                    "default": is_default_from_file # 初始时保留从文件读取的default值
                })
            
            # 统一处理默认版本逻辑
            found_default_by_name = False
            if default_version_name_from_settings:
                for inst in self.installations:
                    if inst["name"] == default_version_name_from_settings:
                        inst["default"] = True
                        found_default_by_name = True
                    else:
                        inst["default"] = False # 确保只有一个是默认
            
            if not found_default_by_name:
                # 如果按名称未找到默认，或名称为空，则检查是否有条目在文件中标记为default=True
                # 或者，如果都没有，则将第一个设为默认
                explicitly_marked_default = None
                for inst in self.installations:
                    if inst.get("default", False): # 检查原始的default标记
                        if explicitly_marked_default:
                            logging.warning(f"发现多个安装标记为默认，仅保留第一个: {explicitly_marked_default['name']}")
                            inst["default"] = False # 取消后续的
                        else:
                            explicitly_marked_default = inst
                            # 其他所有都设为非默认
                            for other_inst in self.installations:
                                if other_inst is not inst:
                                    other_inst["default"] = False
                        found_default_by_name = True # 标记已处理
                        break # 找到第一个就够了
                default_found = False
                if not found_default_by_name and self.installations: # 如果还没有默认，且列表不为空
                    if not default_found and self.python_installations:
                        self.python_installations[0]["is_default"] = False
                    for i in range(1, len(self.installations)):
                        self.installations[i]["default"] = False
                    logging.info(f"未找到明确的默认版本，将第一个安装 '{self.installations[0]['name']}' 设为默认。")
            
            # 更新 default_version_var 以反映当前的默认版本名称
            current_default_name = ""
            for inst in self.installations:
                if inst.get("default"):
                    current_default_name = inst["name"]
                    break
            self.default_version_var.set(current_default_name)

            self._update_python_list()
            logging.debug("Python版本设置加载成功，并已进行数据整理。")
        except Exception as e:
            logging.error(f"加载Python版本设置时发生严重错误: {e}", exc_info=True)
            self.installations = []
            self.default_version_var.set("") # 确保UI在出错时也更新
            self._update_python_list()
    
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