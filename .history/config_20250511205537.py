from log import app_logger
from save_path import create_folder
class Config:
    def __init__(self,version:str,json:dict):
        self.version=version
        self.json=json
        self.config={}
        self.config_path=create_folder.get_path("pyquick",version)
        self.json={"pre_load_python":bool}
    def get_pre_load_python() -> bool:
        try:
            with open(config_path, "r") as file: