import os
import sys
import threading
import subprocess
import time
import tkinter as tk

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger, LogPerformance

logger = get_logger()

def update_pip(config_path):
    """Update pip to the latest version"""
    try:
        # 直接使用当前 Python 环境升级 pip
        logger.info("尝试升级当前环境的 pip")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            text=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            logger.error(f"Pip upgrade failed: {result.stderr}")
            return False
        
        logger.info(f"Pip upgraded successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error during pip upgrade: {e}")
        return False
    except PermissionError as e:
        logger.error(f"Permission error during pip upgrade: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during pip upgrade: {e}")
        return False

def check_pip_version(config_path, pip_upgrade_button, package_entry, install_button, 
                     uninstall_button, upgrade_button, pip_progress_bar, package_status_label, root, pip_retry_button=None):
    """Check and update pip version if needed"""
    from pip.check_ver import get_pip_version, get_latest_pip_version
    
    with LogPerformance(logger, "Checking pip version"):
        # 检查根窗口
        if not root or not root.winfo_exists():
            logger.error("检查pip版本时无法获取有效的根窗口")
            return
            
        # 开始检查前更新GUI状态 - 使用root.after确保在主线程中
        def update_gui_start():
            try:
                pip_upgrade_button.config(state="disabled")
                package_entry.config(state="disabled")
                install_button.config(state="disabled")
                uninstall_button.config(state="disabled")
                upgrade_button.config(state="disabled")
                pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
                pip_progress_bar.start(10)
                
                # 隐藏重试按钮（如果有）
                if pip_retry_button:
                    pip_retry_button.grid_forget()
            except Exception as e:
                logger.error(f"更新UI初始状态失败: {e}")
        
        # 使用root.after确保在主线程中执行
        root.after(0, update_gui_start)
        
        # 用于清除状态的通用函数
        def clear_status():
            try:
                package_status_label.config(text="")
            except Exception as e:
                logger.error(f"清除状态标签失败: {e}")
        
        # 工作线程函数
        def check_version_thread():
            current_version = None
            latest_version = None
            error_message = None
            update_success = False
            
            try:
                current_version = get_pip_version(config_path)
                if current_version is None:
                    error_message = "Error: Failed to get current pip version"
                    return
                    
                latest_version = get_latest_pip_version()
                if latest_version is None:
                    error_message = "Error: Failed to get latest pip version"
                    return
                    
                if current_version != latest_version:
                    # 在主线程中更新GUI显示正在更新
                    if root and root.winfo_exists():
                        message = f"Current pip version: {current_version}\nLatest pip version: {latest_version}\nUpdating pip..."
                        root.after(0, lambda msg=message: update_status_message(msg))
                    
                    # 执行更新 - 这是一个阻塞操作，但在线程中执行
                    update_success = update_pip(config_path)
                    
                    # 默认为显示错误消息
                    error_message = "Error: Failed to update pip"
            except Exception as e:
                logger.error(f"检查pip版本时出错: {e}")
                error_message = f"Error: {str(e)}"
            
            # 在主线程中更新UI
            if root and root.winfo_exists():
                root.after(0, lambda: update_ui_after_check(current_version, latest_version, error_message, update_success))
        
        # 辅助函数用于更新状态消息
        def update_status_message(message):
            try:
                package_status_label.config(text=message)
            except Exception as e:
                logger.error(f"更新状态消息失败: {e}")
        
        # 辅助函数用于更新检查完成后的UI
        def update_ui_after_check(current_version, latest_version, error_message, update_success):
            try:
                # 停止进度条
                pip_progress_bar.stop()
                pip_progress_bar.grid_forget()
                
                # 恢复按钮状态
                package_entry.config(state="normal")
                install_button.config(state="normal")
                upgrade_button.config(state="normal")
                uninstall_button.config(state="normal")
                
                if error_message:
                    # 显示错误
                    package_status_label.config(text=error_message)
                    
                    # 如果有错误且有重试按钮，显示它
                    if pip_retry_button:
                        pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
                elif current_version == latest_version:
                    # 已是最新版本
                    package_status_label.config(text=f"pip is up to date: {current_version}")
                elif update_success:
                    # 更新成功
                    package_status_label.config(text=f"pip has been updated! {current_version}-->{latest_version}")
                    
                    # 设置标志以再次检查pip版本
                    with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                        fw.write("True\n")
                        fw.write(current_version)
                else:
                    # 更新失败
                    package_status_label.config(text="Error: Failed to update pip")
                    
                    # 显示重试按钮
                    if pip_retry_button:
                        pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
                
                # 5秒后清除状态
                root.after(5000, clear_status)
            except Exception as e:
                logger.error(f"更新检查后UI失败: {e}")
        
        # 启动检查线程
        threading.Thread(target=check_version_thread, daemon=True).start()

def upgrade_pip(pip_upgrade_button, package_entry, install_button, uninstall_button, 
               upgrade_button, pip_progress_bar, package_status_label, config_path, root):
    """Start pip version check thread"""
    try:
        # 检查根窗口
        if not root or not root.winfo_exists():
            logger.error("升级pip时无法获取有效的根窗口")
            return
            
        # 更新UI状态
        def update_ui_start():
            try:
                pip_upgrade_button.config(state="disabled")
                package_entry.config(state="disabled")
                install_button.config(state="disabled")
                uninstall_button.config(state="disabled")
                upgrade_button.config(state="disabled")
                pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
                pip_progress_bar.start(10)
            except Exception as e:
                logger.error(f"更新UI初始状态失败: {e}")
        
        # 在主线程中更新UI
        root.after(0, update_ui_start)
        
        # 获取重试按钮
        pip_retry_button = None
        def find_retry_button():
            nonlocal pip_retry_button
            try:
                for child in pip_progress_bar.master.winfo_children():
                    if isinstance(child, type(pip_progress_bar)) and child.winfo_name().endswith('button') and 'retry' in str(child['text']).lower():
                        pip_retry_button = child
                        pip_retry_button.grid_forget()
                        break
            except Exception as e:
                logger.error(f"查找重试按钮失败: {e}")
        
        # 在主线程中查找重试按钮
        root.after(0, find_retry_button)
        
        def clear_status():
            try:
                package_status_label.config(text="")
            except Exception as e:
                logger.error(f"清除状态标签失败: {e}")
        
        # 检查Python是否安装
        try:
            subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # 启动检查线程
            threading.Thread(
                target=check_pip_version, 
                args=(config_path, pip_upgrade_button, package_entry, install_button, 
                     uninstall_button, upgrade_button, pip_progress_bar, package_status_label, root, pip_retry_button),
                daemon=True
            ).start()
        except FileNotFoundError:
            # 在主线程中显示错误
            def show_python_not_found():
                try:
                    package_status_label.config(text="Python is not installed.")
                    
                    # 恢复按钮状态
                    package_entry.config(state="normal")
                    upgrade_button.config(state="normal")
                    install_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    
                    # 5秒后清除状态
                    root.after(5000, clear_status)
                except Exception as e:
                    logger.error(f"显示Python未安装错误失败: {e}")
            
            # 在主线程中显示错误
            root.after(0, show_python_not_found)
    except Exception as e:
        # 在主线程中显示错误
        def show_error():
            try:
                package_status_label.config(text=f"Error: {str(e)}")
                
                # 恢复按钮状态
                package_entry.config(state="normal")
                upgrade_button.config(state="normal")
                install_button.config(state="normal")
                uninstall_button.config(state="normal")
                pip_progress_bar.stop()
                pip_progress_bar.grid_forget()
                
                # 5秒后清除状态
                root.after(5000, clear_status)
            except Exception as e2:
                logger.error(f"显示错误信息失败: {e2}")
        
        # 在主线程中显示错误
        root.after(0, show_error)
        logger.error(f"启动pip版本检查线程失败: {e}")
