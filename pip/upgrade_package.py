import os
import sys
import threading
import subprocess
import time

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger, LogPerformance

logger = get_logger()

def check_package_upgradeable(package_name, config_path):
    """
    Check if a package can be upgraded
    
    Returns:
        tuple: (can_upgrade, current_version, latest_version, package_name) or None if error
    """
    from pip.install_uninstall import get_pip_command_version
    
    if not package_name or package_name == "":
        return None
        
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        logger.error("Failed to determine pip command")
        return None
        
    try:
        # Check if package is installed
        find_packages = subprocess.run(
            [pip_cmd, "show", package_name], 
            text=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if f"WARNING: Package(s) not found: {package_name}" in find_packages.stderr:
            return None
            
        # Get current version
        try:
            current_version = find_packages.stdout.split("\n")[1].split(": ")[1]
        except (IndexError, KeyError):
            logger.error(f"Error parsing current version for {package_name}")
            return None
            
        # Check if upgrade is available
        check_upgradeable = subprocess.run(
            [pip_cmd, "install", "--upgrade", "--dry-run", package_name], 
            text=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if "Would install" not in check_upgradeable.stdout:
            return (False, current_version, current_version, package_name)
            
        try:
            # Get package name and latest version from output
            latest_version = check_upgradeable.stdout.split("\n")[-2].split("-")[1]
            package_true_name = check_upgradeable.stdout.split("\n")[-2].split("-")[0].split(" ")[-1]
            
            if current_version == latest_version:
                return (False, current_version, latest_version, package_true_name)
            else:
                return (True, current_version, latest_version, package_true_name)
                
        except (IndexError, KeyError):
            logger.error(f"Error parsing latest version for {package_name}")
            return None
    except Exception as e:
        logger.error(f"Error checking upgradeable status: {e}")
        return None

def upgrade_package(package_name, config_path, package_status_label, pip_progress_bar, 
                   upgrade_button, pip_upgrade_button, package_entry, install_button, 
                   uninstall_button, root):
    """Upgrade specified Python package"""
    from pip.install_uninstall import get_pip_command_version
    
    def clear_status():
        package_status_label.config(text="")
        
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        pip_progress_bar.stop()
        pip_progress_bar.grid_forget()
        package_status_label.config(text="Failed to determine pip command version")
        package_entry.config(state="normal")
        install_button.config(state="normal")
        uninstall_button.config(state="normal")
        upgrade_button.grid_forget()
        root.after(5000, clear_status)
        return
    
    def upgrade_package_thread():
        try:
            with LogPerformance(logger, f"Upgrading package {package_name}"):
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
                    upgrade_button.grid_forget()
                    package_entry.config(state="normal")
                    install_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    root.after(5000, clear_status)
                    return
                
                # Perform upgrade
                result = subprocess.run(
                    [pip_cmd, "install", "--upgrade", package_name], 
                    capture_output=True,
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if "Successfully installed" in result.stdout:
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    package_status_label.config(text=f"Package '{package_name}' has been upgraded successfully!")
                    logger.info(f"Package '{package_name}' upgraded successfully")
                    upgrade_button.grid_forget()
                    package_entry.config(state="normal")
                    install_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    root.after(5000, clear_status)
                elif f"Requirement already satisfied: {package_name}" in result.stdout:
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    package_status_label.config(text=f"Package '{package_name}' is already up to date.")
                    logger.info(f"Package '{package_name}' is already up to date")
                    upgrade_button.grid_forget()
                    package_entry.config(state="normal")
                    install_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    root.after(5000, clear_status)
                else:
                    pip_progress_bar.stop()
                    pip_progress_bar.grid_forget()
                    package_status_label.config(text=f"Error upgrading package '{package_name}': {result.stderr}")
                    logger.error(f"Error upgrading package '{package_name}': {result.stderr}")
                    upgrade_button.grid_forget()
                    package_entry.config(state="normal")
                    install_button.config(state="normal")
                    uninstall_button.config(state="normal")
                    root.after(5000, clear_status)
        except Exception as e:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text=f"Error upgrading package '{package_name}': {str(e)}")
            logger.error(f"Exception upgrading package '{package_name}': {e}")
            upgrade_button.grid_forget()
            package_entry.config(state="normal")
            install_button.config(state="normal")
            uninstall_button.config(state="normal")
            root.after(5000, clear_status)
    
    threading.Thread(target=upgrade_package_thread, daemon=True).start()
    
def monitor_package_version(package_entry, upgrade_button, install_button, 
                          uninstall_button, config_path):
    """Monitor package entry field for upgradeable packages"""
    def check_upgradeable_thread():
        while True:
            package_name = package_entry.get()
            if not package_name:
                upgrade_button.grid_forget()
                time.sleep(0.3)
                continue
                
            # Store current package name to detect changes
            current_package = package_name
            
            # Check if package is upgradeable
            upgrade_info = check_package_upgradeable(package_name, config_path)
            
            # If package name changed during check, ignore results
            if current_package != package_entry.get():
                upgrade_button.grid_forget()
                continue
                
            if upgrade_info and upgrade_info[0]:  # Can upgrade
                current_version, latest_version, package_true_name = upgrade_info[1], upgrade_info[2], upgrade_info[3]
                upgrade_button.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
                upgrade_button.config(
                    state="normal",
                    text=f"Upgrade Package: {package_true_name} ({current_version} -> {latest_version})"
                )
                
                # Wait for package name to change or a reasonable timeout
                for _ in range(10):  # Check for 3 seconds (10 * 0.3)
                    if current_package != package_entry.get():
                        upgrade_button.grid_forget()
                        break
                    time.sleep(0.3)
            else:
                upgrade_button.grid_forget()
                
            time.sleep(0.2)
    
    thread = threading.Thread(target=check_upgradeable_thread, daemon=True)
    thread.start()
    return thread
