#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复的pyquick函数
用于解决线程安全问题和pip版本检查功能
"""

def upgrade_package_ui():
    """升级包UI处理函数"""
    package_name = package_entry.get()
    if not package_name:
        messagebox.showwarning("警告", "请输入包名称")
        return
    
    pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
    pip_progress_bar.start(10)
    
    package_entry.config(state="disabled")
    install_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    upgrade_button.config(state="disabled")
    
    upgrade_package(package_name, config_path, package_status_label, pip_progress_bar, 
                  upgrade_button, pip_upgrade_button, package_entry, install_button, 
                  uninstall_button, root)

def show_pip_version():
    """显示pip版本，安全地避免线程问题"""
    global pip_upgrade_button, pip_retry_button
    
    # 在UI开始检查前先更新按钮文本
    pip_upgrade_button.config(text=get_text("pip_checking"), state="disabled")
    
    # 在主线程中安全地更新UI的函数
    def update_pip_ui_safely(action, button_text, button_state):
        try:
            pip_upgrade_button.config(text=button_text, state=button_state)
            pip_retry_button.grid_forget()  # 隐藏重试按钮
        except Exception as e:
            logger.error(f"更新pip UI失败: {e}")
    
    # 在主线程中安全地显示错误消息
    def update_pip_ui_error():
        try:
            pip_upgrade_button.config(text=get_text("failed_to_get_pip_version"), state="disabled")
            pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
        except Exception as e:
            logger.error(f"更新pip错误UI失败: {e}")
    
    # 定义线程函数
    def check_pip_version_thread():
        try:
            # 获取pip版本信息
            version_pip = get_pip_version(config_path)
            with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
                b = f.readlines()
                python_name = "Python" + b[-1].strip("\n").strip("Pip")
            
            latest_version = get_latest_pip_version()
            
            # 准备更新UI的数据
            if version_pip == latest_version:
                action = "up_to_date"
                button_text = get_text("pip_up_to_date").format(python_name, version_pip)
                button_state = "disabled"
                update_flag = "False"
            else:
                action = "update_available"
                button_text = get_text("pip_new_version_available").format(
                    python_name, version_pip, latest_version
                )
                button_state = "normal"
                # 检查其他按钮状态
                if "disabled" in install_button.state() and "disabled" in uninstall_button.state():
                    button_state = "disabled"
                update_flag = "True"
            
            # 保存pip检查结果
            with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                fw.write(update_flag + "\n")
                fw.write(version_pip if version_pip else "")
            
            # 安全地在主线程中更新UI
            root.after(0, lambda: update_pip_ui_safely(action, button_text, button_state))
            
        except Exception as e:
            logger.error(f"Failed to get pip version: {e}")
            # 安全地在主线程中更新错误UI
            root.after(0, lambda: update_pip_ui_error())
    
    # 启动后台线程检查pip版本
    threading.Thread(target=check_pip_version_thread, daemon=True).start()

def save_path():
    """后台定期检查pip版本的函数"""
    last_check_version = None
    
    while True:
        try:
            # 检查是否需要检查pip版本
            check_needed = False
            current_version = None
            
            try:
                # 读取当前设置的pip版本
                with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
                    current_version = f.read().strip()
                
                # 读取是否需要自动检查pip版本
                auto_check_enabled = True  # 默认启用
                with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as f:
                    lines = f.readlines()
                    if lines and lines[0].strip().lower() == "false":
                        auto_check_enabled = False
                
                # 如果版本发生变化或允许自动检查，则进行检查
                if current_version != last_check_version or auto_check_enabled:
                    check_needed = True
            except Exception as e:
                logger.error(f"读取pip版本检查设置失败: {e}")
                # 出错时默认需要检查
                check_needed = True
            
            # 如果需要检查，调用show_pip_version函数
            if check_needed:
                last_check_version = current_version
                # 使用主线程中的单次调用更新UI，而不是启动新线程
                root.after(0, show_pip_version)
            
            # 较长时间睡眠，减少资源消耗
            time.sleep(5.0)
        except Exception as e:
            logger.error(f"后台检查pip版本出错: {e}")
            time.sleep(3.0)  # 出错后等待更长时间再重试

def retry_pip_ui():
    """重试检查pip版本"""
    # 直接调用show_pip_version()函数
    show_pip_version() 