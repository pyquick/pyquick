from log import app_logger
config_path=create_folder.get_path("pyquick",version)
json={"pre_load_python":bool}
def get_pre_load_python() -> bool:
    try:
        with open