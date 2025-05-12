from log import app_logger
from save_path import create_folder,sav_path
class Config:
    def __init__(self,version:str):
        self.version=version
        self.config={}
        self.config_path=create_folder.get_path("pyquick",version)
    def get_pre_load_python(self) -> bool:
        try:
            a=sav_path.read_json(self.config_path,"config.json")
            if a["pre_load_python"]==True:
                return True
            else:
                return False
        except FileNotFoundError:
            app_logger.error("配置文件不存在")
            return False