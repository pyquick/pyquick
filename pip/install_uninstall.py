import os
import sys
import threading
import subprocess

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger, LogPerformance, log_exception

logger = get_logger()

def get_pip_command_version(config_path):
    """Get pip command version based on Python version"""
    try:
        # 从配置文件读取版本信息
        with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
            version_str = f.readlines()[-1].strip("\n")
            
        if not version_str or not version_str.startswith("Pip"):
            logger.warning("无效的版本字符串格式")
            return None
            
        version_num = version_str[3:]  # 提取数字部分
        if len(version_num) < 2:  # 确保至少有两位数字
            logger.warning("版本号格式不正确")
            return None
            
        # 格式化版本号（例如：将"310"转换为"3.10"）
        major = version_num[0]
        minor = version_num[1:]
        version = f"{major}.{minor}"
        
        # 构造pip命令名称
        pip_cmd = f"pip{version}"
        
        # 检验命令是否可用
        try:
            result = subprocess.run(
                [pip_cmd, "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                logger.info(f"找到可用的pip命令: {pip_cmd}")
                return f"{pip_cmd}.exe"
        except Exception as e:
            logger.debug(f"pip命令 {pip_cmd} 不可用: {e}")
            
        # 如果特定版本不可用，尝试使用通用pip命令
        try:
            result = subprocess.run(
                ["pip", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                logger.info("使用通用pip命令")
                return "pip.exe"
        except Exception as e:
            logger.warning(f"通用pip命令也不可用: {e}")
            
    except Exception as e:
        logger.error(f"获取pip命令版本失败: {e}")
        
    return None

def install_package(package_name, config_path, package_status_label, pip_progress_bar, 
                   install_button, pip_upgrade_button, package_entry, uninstall_button, 
                   upgrade_button, root):
    """Install specified Python package"""
    def clear_status():
        package_status_label.config(text="")
    
    if "=" in package_name or package_name == "" or package_name is None or " " in package_name or package_name == "pip":
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        package_status_label.config(text=f"Invalid package name: {package_name}")
        logger.warning(f"Invalid package name: {package_name}")
        uninstall_button.config(state="normal")
        upgrade_button.config(state="normal")
        package_entry.config(state="normal")
        install_button.config(state="normal")
        root.after(5000, clear_status)
        return
    
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        package_status_label.config(text="Failed to determine pip command version")
        uninstall_button.config(state="normal")
        upgrade_button.config(state="normal")
        package_entry.config(state="normal")
        install_button.config(state="normal")
        root.after(5000, clear_status)
        return
    
    def install_package_thread():
        try:
            with LogPerformance(logger, f"Installing package {package_name}"):
                # Check if package is already installed
                find_packages = subprocess.run(
                    [pip_cmd, "show", package_name], 
                    text=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if f"Name: " in find_packages.stdout:
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    package_status_label.config(text=f"Package '{package_name}' is already installed.")
                    logger.info(f"Package '{package_name}' is already installed")
                    install_button.config(state="normal")
                    upgrade_button.config(state="normal")
                    package_entry.config(state="normal")
                    uninstall_button.config(state="normal")
                    root.after(5000, clear_status)
                    return
                else:
                    logger.info(f"Starting installation of package: {package_name}")
                    result = subprocess.run(
                        [pip_cmd, "install", package_name], 
                        capture_output=True,
                        text=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if "Successfully installed" in result.stdout:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Package '{package_name}' has been installed successfully!")
                        logger.info(f"Package '{package_name}' installed successfully")
                        install_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        uninstall_button.config(state="normal")                    
                        root.after(5000, clear_status)
                    elif f"ERROR: No matching distribution found for {package_name}" in result.stderr:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"{package_name} is not found from the Internet.")
                        logger.error(f"Package '{package_name}' not found")
                        install_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        uninstall_button.config(state="normal")          
                        root.after(5000, clear_status)
                    elif "Invalid requirement" in result.stderr:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Invalid package name: {package_name}")
                        logger.warning(f"Invalid package name: {package_name}")
                        uninstall_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        install_button.config(state="normal")
                        root.after(5000, clear_status)
                    else:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Error installing package '{package_name}': {result.stderr}")
                        logger.error(f"Error installing package '{package_name}': {result.stderr}")
                        install_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        uninstall_button.config(state="normal")
                        root.after(5000, clear_status)
        except Exception as e:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text=f"Error installing package '{package_name}': {str(e)}")
            log_exception(logger, f"Exception installing package '{package_name}'")
            install_button.config(state="normal")
            upgrade_button.config(state="normal")
            package_entry.config(state="normal")
            uninstall_button.config(state="normal")
            root.after(5000, clear_status)

    threading.Thread(target=install_package_thread, daemon=True).start()

def uninstall_package(package_name, config_path, package_status_label, pip_progress_bar, 
                     uninstall_button, upgrade_button, pip_upgrade_button, package_entry, 
                     install_button, root):
    """Uninstall specified Python package"""
    def clear_status():
        package_status_label.config(text="")
    
    if "=" in package_name or package_name == "" or package_name is None or " " in package_name or package_name == "pip":
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        package_status_label.config(text=f"Invalid package name: {package_name}")
        logger.warning(f"Invalid package name: {package_name}")
        uninstall_button.config(state="normal")
        upgrade_button.config(state="normal")
        package_entry.config(state="normal")
        install_button.config(state="normal")
        root.after(5000, clear_status)
        return
    
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        package_status_label.config(text="Failed to determine pip command version")
        uninstall_button.config(state="normal")
        upgrade_button.config(state="normal")
        package_entry.config(state="normal")
        install_button.config(state="normal")
        root.after(5000, clear_status)
        return
    
    def uninstall_package_thread():
        try:
            with LogPerformance(logger, f"Uninstalling package {package_name}"):
                # Check if package is installed
                find_packages = subprocess.run(
                    [pip_cmd, "show", package_name], 
                    text=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if f"WARNING: Package(s) not found: {package_name}" in find_packages.stderr:
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    package_status_label.config(text=f"Package '{package_name}' is not installed.")
                    logger.info(f"Package '{package_name}' is not installed")
                    upgrade_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    package_entry.config(state="normal")
                    install_button.config(state="normal")
                    root.after(5000, clear_status)
                else:
                    result = subprocess.run(
                        [pip_cmd, "uninstall", "-y", package_name], 
                        capture_output=True,
                        text=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if "Successfully uninstalled" in result.stdout:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                        logger.info(f"Package '{package_name}' uninstalled successfully")
                        uninstall_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        install_button.config(state="normal")
                        root.after(5000, clear_status) 
                    elif "Invalid requirement" in result.stderr:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Invalid package name: {package_name}")
                        logger.warning(f"Invalid package name: {package_name}")
                        uninstall_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        install_button.config(state="normal")
                        root.after(5000, clear_status)
                    else:
                        pip_progress_bar.stop()
                        pip_progress_bar.grid_forget()
                        package_status_label.config(text=f"Error uninstalling package '{package_name}': {result.stderr}")
                        logger.error(f"Error uninstalling package '{package_name}': {result.stderr}")
                        uninstall_button.config(state="normal")
                        upgrade_button.config(state="normal")
                        package_entry.config(state="normal")
                        install_button.config(state="normal")
                        root.after(5000, clear_status)
        except Exception as e:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
            log_exception(logger, f"Exception uninstalling package '{package_name}'")
            uninstall_button.config(state="normal")
            upgrade_button.config(state="normal")
            package_entry.config(state="normal")
            install_button.config(state="normal")           
            root.after(5000, clear_status)
    
    threading.Thread(target=uninstall_package_thread, daemon=True).start()