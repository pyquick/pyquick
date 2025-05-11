from log import app_logger
from save_path import create_folder
config_path=create_folder.get_path("pyquick",version)
json={"pre_load_python":bool}
def get_pre_load_python() -> bool:
    try:
        with open