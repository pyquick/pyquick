import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sv_ttk
import darkdetect
from save_path import create_folder, sav_path
import proxy
from get_system_build import block_features
import json
import requests
import base64

# 全局变量，用于UI引用
root = None
config_path = None
window = None

def init_settings_manager(root_window, config_dir):
    """初始化设置管理器"""
    global root, config_path
    root = root_window
    config_path = config_dir

def load_theme():
    """加载主题设置"""
    if block_features.block_theme():
        try:
            theme = sav_path.read_path(config_path, "theme.txt", "readline")
            if theme == "light":
                sv_ttk.set_theme("light")
            elif theme == "dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme(darkdetect.theme())
        except FileNotFoundError:
            sv_ttk.set_theme(darkdetect.theme())
        except Exception as e:
            sv_ttk.set_theme(darkdetect.theme())
    else:
        try:
            sav_path.remove_file(config_path, "theme.txt")
        except:
            pass

def save_theme():
    """保存主题设置"""
    if block_features.block_theme():
        theme = sv_ttk.get_theme()
        sav_path.save_path(config_path, "theme.txt", "w", theme)

def is_window_valid():
    """检查设置窗口是否有效"""
    global window
    if window is None:
        return False
    try:
        return window.winfo_exists()
    except:
        return False

def delayed_label_clear(label, delay=3.0):
    """安全地延迟清除标签文本"""
    def clear_text():
        try:
            if is_window_valid() and label.winfo_exists():
                label.config(text="")
        except:
            pass
    timer = threading.Timer(delay, clear_text)
    timer.daemon = True
    timer.start()

def open_settings():
    """打开设置窗口"""
    global window
    
    if window is not None:
        try:
            if window.winfo_exists():
                window.focus_set()
                return
            else:
                window = None
        except:
            window = None
    
    window = tk.Toplevel(root)
    window.title("Settings")
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", lambda: window.destroy())
    
    # 创建标签页控件
    control = ttk.Notebook(window)
    control.grid(row=0, padx=5, pady=5)
    
    # 创建主题设置选项卡
    if block_features.block_theme():
        ftheme = ttk.Frame(window, padding="20")
        control.add(ftheme, text="Theme")
        theme_tab = ttk.Frame(ftheme)
        theme_tab.grid(row=0, column=0, padx=5, pady=5)
        
        # 添加主题切换开关
        switch = tk.BooleanVar()
        sw_theme = ttk.Checkbutton(
            theme_tab, 
            text="Dark Theme", 
            variable=switch, 
            command=lambda: switch_theme(switch),
            style="Switch.TCheckbutton"
        )
        sw_theme.grid(row=0, column=0, padx=20, pady=20)
        
        # 设置开关初始状态
        current_theme = sv_ttk.get_theme()
        if current_theme == "dark":
            switch.set(1)
        else:
            switch.set(0)
    
    # 创建代理设置选项卡
    proxy_frame = ttk.Frame(window, padding="20")
    control.add(proxy_frame, text="Proxy Settings")
    create_proxy_tab(proxy_frame)

    # 创建关于选项卡
    about_frame = ttk.Frame(window, padding="20")
    control.add(about_frame, text="About")
    
    about_label = ttk.Label(
        about_frame, 
        text="Pyquick - Python Package Manager\nVersion: 1.0.0\nAuthor: Pyquick Team",
        justify=tk.CENTER
    )
    about_label.grid(row=0, column=0, padx=20, pady=20)

def switch_theme(switch_var):
    """切换主题"""
    if block_features.block_theme():
        if switch_var.get():
            sv_ttk.set_theme("dark")
            sav_path.save_path(config_path, "theme.txt", "w", "dark")
        else:
            sv_ttk.set_theme("light")
            sav_path.save_path(config_path, "theme.txt", "w", "light")

def create_proxy_tab(parent_frame):
    """创建代理设置选项卡"""
    # 全局定义布局位置常量
    PROXY_SWITCH_ROW = 0
    AUTH_SWITCH_ROW = 1
    PROXY_HOST_ROW = 2
    PROXY_PORT_ROW = 3
    USERNAME_ROW = 4
    PASSWORD_ROW = 5
    BUTTON_ROW = 6
    STATUS_ROW = 7
    
    proxy_tab = ttk.Frame(parent_frame)
    proxy_tab.grid(row=0, column=0, sticky='nsew')
    parent_frame.grid_rowconfigure(0, weight=1)
    parent_frame.grid_columnconfigure(0, weight=1)
    
    # 代理开关
    enabled = tk.BooleanVar()
    
    # 用户认证选项
    user = tk.BooleanVar()
    checkuser = ttk.Checkbutton(
        proxy_tab, 
        text="Proxy requires username and password", 
        variable=user, 
        style="Switch.TCheckbutton",
        command=lambda: toggle_auth_fields(user, enabled, {
            "username_entry": username_entry,
            "password_entry": password_entry,
            "username_label": username_label,
            "password_label": password_label
        })
    )
    
    # 创建代理开关，并将认证开关作为依赖组件传入
    check = ttk.Checkbutton(
        proxy_tab, 
        text="Enable Proxy", 
        variable=enabled, 
        style="Switch.TCheckbutton",
        command=lambda: toggle_proxy_status(enabled, proxy_tab, {
            "proxy_entry": proxy_entry,
            "port_entry": port_entry,
            "username_entry": username_entry,
            "password_entry": password_entry,
            "username_label": username_label,
            "password_label": password_label,
            "proxy_label": proxy_label,
            "port_label": port_label,
            "user": user,
            "checkuser": checkuser,
            "auth_switch_row": AUTH_SWITCH_ROW
        })
    )
    check.grid(row=PROXY_SWITCH_ROW, column=0, columnspan=2, padx=20, pady=20, sticky="w")
    
    # 初始隐藏认证开关，会根据代理状态在load_proxy_settings中决定是否显示
    
    # 代理地址和端口（初始隐藏）
    proxy_label = ttk.Label(proxy_tab, text="HTTP(S) Proxy:")
    proxy_entry = ttk.Entry(proxy_tab, width=30)
    
    port_label = ttk.Label(proxy_tab, text="Port:")
    port_entry = ttk.Entry(proxy_tab, width=10)
    
    # 用户名密码字段（初始隐藏）
    username_label = ttk.Label(proxy_tab, text="Username:")
    username_entry = ttk.Entry(proxy_tab, width=30)
    
    password_label = ttk.Label(proxy_tab, text="Password:")
    password_entry = ttk.Entry(proxy_tab, width=30, show="*")
    
    # 测试连接和保存按钮
    button_frame = ttk.Frame(proxy_tab)
    button_frame.grid(row=BUTTON_ROW, column=0, columnspan=2, padx=20, pady=10, sticky="w")
    
    test_button = ttk.Button(
        button_frame, 
        text="Test Connection", 
        command=lambda: test_proxy_connection(proxy_entry, port_entry, user, username_entry, password_entry, status_label)
    )
    test_button.grid(row=0, column=0, padx=10)
    
    save_button = ttk.Button(
        button_frame, 
        text="Save Settings", 
        command=lambda: save_proxy_settings(proxy_entry, port_entry, user, username_entry, password_entry, enabled, status_label)
    )
    save_button.grid(row=0, column=1, padx=10)
    
    # 状态标签 - 放在按钮下方并确保其可见性
    status_frame = ttk.Frame(proxy_tab)
    status_frame.grid(row=STATUS_ROW, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
    
    status_label = ttk.Label(status_frame, text="", foreground="red", font=("", 10, ""))
    status_label.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
    
    # 构建UI元素字典
    ui_elements = {
        "proxy_entry": proxy_entry,
        "port_entry": port_entry,
        "username_entry": username_entry,
        "password_entry": password_entry,
        "enabled": enabled,
        "user": user,
        "status_label": status_label,
        "username_label": username_label,
        "password_label": password_label,
        "proxy_label": proxy_label,
        "port_label": port_label,
        "checkuser": checkuser,
        "auth_switch_row": AUTH_SWITCH_ROW
    }
    
    # 初始化代理设置
    threading.Thread(
        target=lambda: load_proxy_settings(ui_elements),
        daemon=True
    ).start()
    
    return ui_elements

def toggle_proxy_status(enabled, proxy_tab, ui_elements):
    """切换代理状态"""
    checkuser = ui_elements["checkuser"]
    auth_switch_row = ui_elements.get("auth_switch_row", 1)
    
    # 设置代理状态
    proxy.proxy_set_status(enabled.get(), 1965)
    
    # 立即管理认证开关的显示/隐藏
    if enabled.get():
        # 启用代理 - 显示认证选项
        checkuser.grid(row=auth_switch_row, column=0, columnspan=2, padx=20, pady=10, sticky="w")
    else:
        # 禁用代理 - 隐藏认证选项和认证相关字段
        checkuser.grid_forget()
        # 同时禁用认证选项
        ui_elements["user"].set(False)
        proxy.password_set_status(False, 1965)
    
    # 更新UI显示
    update_proxy_ui(enabled.get(), ui_elements)

def toggle_auth_fields(user, enabled, ui_elements):
    """切换认证字段显示"""
    # 在单独线程中执行以避免UI阻塞
    def toggle_thread():
    # 设置密码认证状态
        if enabled.get():
            proxy.password_set_status(user.get(), 1965)
            
            # 根据状态显示或隐藏认证字段
            root.after(0, lambda: update_auth_ui(user.get(), ui_elements))
    
    # 启动线程
    threading.Thread(target=toggle_thread, daemon=True).start()

def update_auth_ui(use_auth, ui_elements):
    """更新认证UI状态"""
    username_entry = ui_elements["username_entry"]
    password_entry = ui_elements["password_entry"]
    username_label = ui_elements["username_label"]
    password_label = ui_elements["password_label"]
    
    if use_auth:
        # 显示认证字段
        if username_label:
            username_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        if username_entry:
            username_entry.grid(row=4, column=1, padx=20, pady=10, sticky="w")
        if password_label:
            password_label.grid(row=5, column=0, padx=20, pady=10, sticky="w")
        if password_entry:
            password_entry.grid(row=5, column=1, padx=20, pady=10, sticky="w")
        else:
        # 隐藏认证字段
            if username_label:
                username_label.grid_forget()
            if username_entry:
                username_entry.grid_forget()
            if password_label:
                password_label.grid_forget()
            if password_entry:
                password_entry.grid_forget()

def update_proxy_ui(enabled, ui_elements):
    """更新代理UI状态"""
    username_entry = ui_elements["username_entry"]
    password_entry = ui_elements["password_entry"]
    username_label = ui_elements["username_label"]
    password_label = ui_elements["password_label"]
    proxy_entry = ui_elements["proxy_entry"]
    port_entry = ui_elements["port_entry"]
    proxy_label = ui_elements["proxy_label"]
    port_label = ui_elements["port_label"]
    user = ui_elements["user"]
    
    if enabled:
        # 显示代理设置字段
        if proxy_label:
            proxy_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        if proxy_entry:
            proxy_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        if port_label:
            port_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        if port_entry:
            port_entry.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        
        # 根据认证状态更新认证字段
        update_auth_ui(user.get(), ui_elements)
    else:
        # 隐藏所有设置字段
        if proxy_label:
            proxy_label.grid_forget()
        if proxy_entry:
            proxy_entry.grid_forget()
        if port_label:
            port_label.grid_forget()
        if port_entry:
            port_entry.grid_forget()
        if username_label:
            username_label.grid_forget()
        if username_entry:
            username_entry.grid_forget()
        if password_label:
            password_label.grid_forget()
        if password_entry:
            password_entry.grid_forget()

def load_proxy_settings(ui_elements):
    """加载代理设置"""
    proxy_entry = ui_elements["proxy_entry"]
    port_entry = ui_elements["port_entry"]
    username_entry = ui_elements["username_entry"]
    password_entry = ui_elements["password_entry"]
    enabled = ui_elements["enabled"]
    user = ui_elements["user"]
    checkuser = ui_elements["checkuser"]
    auth_switch_row = ui_elements.get("auth_switch_row", 1)
    
    try:
        # 首先尝试从proxy.json读取配置
        try:
            config_json = sav_path.read_path(config_path, "proxy.json", "read")
            if config_json:
                config = json.loads(config_json)
                
                # 在UI线程中更新UI组件
                def update_ui():
                    # 清空原有内容
                    proxy_entry.delete(0, tk.END)
                    port_entry.delete(0, tk.END)
                    username_entry.delete(0, tk.END)
                    password_entry.delete(0, tk.END)
                    
                    # 设置状态
                    enabled.set(config.get('enabled', False))
                    user.set(config.get('use_auth', False))
                    
                    # 填充内容
                    if config.get('proxy'):
                        proxy_entry.insert(0, config.get('proxy'))
                    if config.get('port'):
                        port_entry.insert(0, config.get('port'))
                    if config.get('username'):
                        username_entry.insert(0, config.get('username'))
                    if config.get('password'):
                        password_entry.insert(0, config.get('password'))
                    
                    # 根据代理状态决定是否显示认证开关
                    if config.get('enabled', False):
                        checkuser.grid(row=auth_switch_row, column=0, columnspan=2, padx=20, pady=10, sticky="w")
                    else:
                        checkuser.grid_forget()
                    
                    # 更新UI显示
                    update_proxy_ui(enabled.get(), ui_elements)
                
                # 在UI线程中执行更新
                if root:
                    root.after(0, update_ui)
                
                # 设置proxy模块状态
                proxy.proxy_set_status(config.get('enabled', False), 1965)
                proxy.password_set_status(config.get('use_auth', False), 1965)
                return
        except:
            pass
            
        # 如果从proxy.json读取失败，使用proxy模块读取
        # 代理状态
        proxy_status = proxy.proxy_check_status(1965)
        auth_status = proxy.password_check_status(1965)
        result = proxy.read_proxy(1965)
        
        # 在UI线程中更新UI组件
        def update_ui():
            # 清空原有内容
            proxy_entry.delete(0, tk.END)
            port_entry.delete(0, tk.END)
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            
            # 设置状态
            enabled.set(proxy_status)
            user.set(auth_status)
        
        # 填充内容
        if result["address"]:
            proxy_entry.insert(0, result["address"])
        if result["port"]:
            port_entry.insert(0, result["port"])
        if result["username"]:
            username_entry.insert(0, result["username"])
        if result["password"]:
            password_entry.insert(0, result["password"])
            
            # 根据代理状态决定是否显示认证开关
            if proxy_status:
                checkuser.grid(row=auth_switch_row, column=0, columnspan=2, padx=20, pady=10, sticky="w")
            else:
                checkuser.grid_forget()
            
            # 更新UI显示
            update_proxy_ui(enabled.get(), ui_elements)
        
        # 在UI线程中执行更新
        if root:
            root.after(0, update_ui)
            
    except Exception as e:
        print(f"加载代理设置失败: {e}")

def save_proxy_settings(proxy_entry, port_entry, user, username_entry, password_entry, enabled, status_label):
    """保存代理设置"""
    # 在单独线程中执行以避免UI阻塞
    def save_thread():
        try:
            # 检查必填字段
            if enabled.get() and (not proxy_entry.get() or not port_entry.get()):
                update_status_label("Please fill in proxy server and port information", "red", 5.0)
                return False
                
            # 设置代理状态
            proxy.proxy_set_status(enabled.get(), 1965)
            
            # 设置认证状态
            proxy.password_set_status(user.get(), 1965)
                
            # 确保用户名和密码不为None
            username = username_entry.get() if user.get() and username_entry.get() else ""
            password = password_entry.get() if user.get() and password_entry.get() else ""
            
            # 保存代理设置到proxy模块
            proxy.save_proxy(
                    proxy_entry.get() or "",
                    port_entry.get() or "",
                    username,
                    password,
                1965
            )
            
            # 同时保存完整配置到proxy.json
            proxy_config = {
                'enabled': enabled.get(),
                    'proxy': proxy_entry.get() or "",
                    'port': port_entry.get() or "",
                'use_auth': user.get(),
                    'username': username,
                    'password': password
            }
            sav_path.save_path(config_path, "proxy.json", "w", json.dumps(proxy_config))
            
            # 更新状态标签
            update_status_label("Proxy settings saved", "green", 3.0)
        
            # 显示消息框
            root.after(0, lambda: messagebox.showinfo("Save Success", "Proxy settings saved successfully"))
            return True
            
        except Exception as e:
            error_msg = f"Failed to save proxy settings: {e}"
            print(error_msg)
            
            # 更新状态标签
            update_status_label(error_msg, "red", 5.0)
            
            # 显示错误消息框
            root.after(0, lambda: messagebox.showerror("Save Failed", error_msg))
            return False
    
    # 辅助函数：更新状态标签
    def update_status_label(message, color, delay):
        if is_window_valid() and status_label.winfo_exists():
            root.after(0, lambda: status_label.config(text=message, foreground=color))
            root.after(0, lambda: status_label.update_idletasks())
            # 安全地延迟清除文本
            delayed_label_clear(status_label, delay)
    
    # 启动保存线程
    threading.Thread(target=save_thread, daemon=True).start()

def test_proxy_connection(proxy_entry, port_entry, user, username_entry, password_entry, status_label):
    """测试代理连接是否有效"""
    # 检查UI组件是否有效
    if not is_window_valid() or not status_label.winfo_exists():
        return False
    
    # 在单独线程中执行以避免UI阻塞
    def test_thread():
        try:
            # 清空现有状态
            root.after(0, lambda: status_label.config(text=""))
            root.after(0, lambda: status_label.update_idletasks())
        
            # 检查必填字段
            if not proxy_entry.get() or not port_entry.get():
                update_status("Please fill in proxy server and port information", "red")
                return False
        
            # 构建代理URL
            proxy_url = f"http://{proxy_entry.get()}:{port_entry.get()}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            # 添加认证信息
            if user.get() and username_entry.get() and password_entry.get():
                auth = f"{username_entry.get()}:{password_entry.get()}"
                encoded_auth = base64.b64encode(auth.encode()).decode()
                headers = {"Proxy-Authorization": f"Basic {encoded_auth}"}
            else:
                headers = {}
            
            # 测试URL
            test_url = "https://www.google.com"
            
            # 显示测试中状态
            update_status("Testing connection...", "blue")
            
            try:
                # 执行请求
                response = requests.get(
                    test_url, 
                    proxies=proxies, 
                    headers=headers, 
                    timeout=10,
                    verify=True
                )
                
                # 更新结果到UI
                if response.status_code == 200:
                    update_status("Proxy connection test successful!", "green")
                    return True
                else:
                    update_status(f"Connection failed: Status code {response.status_code}", "red")
                    return False
            
            except requests.exceptions.ProxyError:
                update_status("Proxy server connection error, please check proxy settings", "red")
                return False
            except requests.exceptions.ConnectTimeout:
                update_status("Connection timeout, please check proxy settings or network conditions", "red")
                return False
            except requests.exceptions.SSLError:
                update_status("SSL certificate verification failed", "red")
                return False
            except Exception as e:
                update_status(f"Connection failed: {str(e)}", "red")
                return False
                
        except Exception as e:
            update_status(f"Test error: {str(e)}", "red")
            return False
    
    # 辅助函数：更新状态标签
    def update_status(message, color):
        if is_window_valid() and status_label.winfo_exists():
            root.after(0, lambda: status_label.config(text=message, foreground=color))
            root.after(0, lambda: status_label.update_idletasks())
            # 设置一个定时器在5秒后清除消息
            delayed_label_clear(status_label, 5.0)
    
    # 显示图片中的错误信息
    update_status("Connecting to proxy server and related parameters", "red")
    
    # 启动测试线程
    threading.Thread(target=test_thread, daemon=True).start()
    
    return True  # 返回测试启动成功