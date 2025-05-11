#import antigravity
import sys,os,json
from settings.save import SettingsManager
from save_path import create_folder
from typing import Dict, Any, Optional, List, Tuple, Union

version="1965"

config_path=create_folder.get_path("pyquick",version)
a=SettingsManager(config_path)
b=a.load_settings()
c=a.get_setting("python_versions.installations")
d=a.scan_system_python_installations()
base={"installations":d,}
e=a.set_setting("python_versions.installations",d)
f=a._merge_user_settings(e,b,"python_versions.installations")
print(f)
if  b==f:
    print("1")
# print(e)b
#print(f)
