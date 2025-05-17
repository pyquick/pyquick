from log import app_logger
from save_path import create_folder,sav_path

class Config:
    def __init__(self,version:str):
        self.version=version
        self.config={}
        self.config_path=create_folder.get_path("pyquick",self.version)
    def get_pre_load_python(self,count) -> bool:
        if count>10:
            app_logger.error("无法获取预加载配置")
            return False
        try:
            self.a=sav_path.read_json(self.config_path,"config.json")
            
            if self.a["pre_load_python"]==True:
                return True
            else:
                return False
        except FileNotFoundError:
            sav_path.save_json(self.config_path,"config.json","w",self.get_model())
            self.get_pre_load_python(count+1)
            return False
    def get_model(self)  -> dict[str,bool]:
        self.model={
            "pre_load_python":False
        }
        return self.model
    def write_config