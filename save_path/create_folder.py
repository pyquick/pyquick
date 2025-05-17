import os
def folder_create(appname,buildver):
    config_pathb = os.path.join(os.path.expanduser("~"), f".{appname}")
    config_path = os.path.join(os.path.expanduser("~"), f".{appname}",f"{buildver}")
    if not os.path.exists(config_pathb):
        os.mkdir(config_pathb)
    if not os.path.exists(config_path):
        os.mkdir(config_path)
def get_path(appname,buildver):
    try:
        if os.name == 'nt':  # Windows系统
            appdata_path = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(appdata_path, f".{appname}", f"{buildver}")
        else:  # 非Windows系统
            return os.path.join(os.path.expanduser("~"), f".{appname}", f"{buildver}")
    except Exception as e:
        import logging
        logging.error(f"获取应用数据路径失败: {e}")
        return os.path.join(os.path.expanduser("~"), f".{appname}", f"{buildver}")