import os
import sys
import threading
import subprocess
import time

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
        
        def clear_status():
            package_status_label.config(text="")
            
        current_version = get_pip_version(config_path)
        if current_version is None:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text="Error: Failed to get current pip version")
            
            package_entry.config(state="normal")
            install_button.config(state="normal")
            upgrade_button.config(state="normal")
            uninstall_button.config(state="normal")
            
            # 显示重试按钮
            if pip_retry_button:
                pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
                
            root.after(5000, clear_status)
            return

        latest_version = get_latest_pip_version()
        if latest_version is None:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text="Error: Failed to get latest pip version")
            
            package_entry.config(state="normal")
            install_button.config(state="normal")
            upgrade_button.config(state="normal")
            uninstall_button.config(state="normal")
            
            # 显示重试按钮
            if pip_retry_button:
                pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
                
            root.after(5000, clear_status)
            return
            
        # 隐藏重试按钮
        if pip_retry_button:
            pip_retry_button.grid_forget()

        if current_version != latest_version:
            message = f"Current pip version: {current_version}\nLatest pip version: {latest_version}\nUpdating pip..."
            package_status_label.config(text=message)
            if update_pip(config_path):
                pip_progress_bar.stop()
                pip_progress_bar.grid_forget()
                package_status_label.config(text=f"pip has been updated! {current_version}-->{latest_version}")
                
                # Set flag to check pip version again
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                    fw.write("True")
                    fw.write("\n")
                    
                package_entry.config(state="normal")
                upgrade_button.config(state="normal")
                install_button.config(state="normal")
                uninstall_button.config(state="normal")
                
                root.after(5000, clear_status)
            else:
                pip_progress_bar.stop()
                pip_progress_bar.grid_forget()
                package_status_label.config(text="Error: Failed to update pip")
                
                package_entry.config(state="normal")
                install_button.config(state="normal")
                upgrade_button.config(state="normal")
                uninstall_button.config(state="normal")
                
                # 显示重试按钮
                if pip_retry_button:
                    pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
                    
                root.after(5000, clear_status)
        else:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text=f"pip is up to date: {current_version}")
            
            package_entry.config(state="normal")
            install_button.config(state="normal")
            upgrade_button.config(state="normal")
            uninstall_button.config(state="normal")
            root.after(5000, clear_status)

def upgrade_pip(pip_upgrade_button, package_entry, install_button, uninstall_button, 
               upgrade_button, pip_progress_bar, package_status_label, config_path, root):
    """Start pip version check thread"""
    try:
        pip_upgrade_button.config(state="disabled")
        package_entry.config(state="disabled")
        install_button.config(state="disabled")
        uninstall_button.config(state="disabled")
        upgrade_button.config(state="disabled")
        pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
        pip_progress_bar.start(10)
        
        # 获取重试按钮
        pip_retry_button = None
        for child in pip_progress_bar.master.winfo_children():
            if isinstance(child, type(pip_progress_bar)) and child.winfo_name().endswith('button') and 'retry' in str(child['text']).lower():
                pip_retry_button = child
                break
        
        # 隐藏重试按钮（如果有）
        if pip_retry_button:
            pip_retry_button.grid_forget()
        
        def clear_status():
            package_status_label.config(text="")
            
        subprocess.check_output(["python", "--version"], creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(
            target=check_pip_version, 
            args=(config_path, pip_upgrade_button, package_entry, install_button, 
                 uninstall_button, upgrade_button, pip_progress_bar, package_status_label, root, pip_retry_button),
            daemon=True
        ).start()
    except FileNotFoundError:
        package_status_label.config(text="Python is not installed.")
        root.after(5000, clear_status)
    except Exception as e:
        package_status_label.config(text=f"Error: {str(e)}")
        
        package_entry.config(state="normal")
        upgrade_button.config(state="normal")
        install_button.config(state="normal")
        uninstall_button.config(state="normal")
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        root.after(5000, clear_status)
