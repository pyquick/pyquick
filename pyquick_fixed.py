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