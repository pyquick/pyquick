from config import Config
from settings.save import SettingsManager
from save_path import create_folder
config_path = create_folder.get_path("pyquick", "2050")
try:
    from config import Config
    if not Config("2050").get_pre_load_python():
        a=SettingsManager(config_path)
        b=a.load_settings()
        d=a.scan_system_python_installations()
        e=a.set_setting("python_versions.installations",d)["installations"]
        f=a._merge_user_settings(e,b,"python_versions.installations")
        a.save_settings(f)
        print("已自动扫描并更新系统Python版本信息。")
    else:
        print("无需预加载Python功能。")
except:
    print("预加载Python功能失败，请检查配置文件。")