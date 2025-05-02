import requests
from bs4 import BeautifulSoup
import re
import gc
import threading,time
from crashes import *
config_path="/Users/liexe/.pyquick"
version="1965"
def show_name():
    while True:
        try:
            ver="3.11.4"
            if os.path.exists(os.path.join(config_path,version,"crashes","download","ver.txt")):
                ver1=edit.read_file(version,"download","ver.txt")
                if ver1==ver:
                    print("版本号相同")
                else:
                    ver2="3.11.4"
                    edit.edit_file(version,"download","ver.txt",ver2)
                    print("修改版本号")
            else:
                open.create_crashes_folder(version,"download")
                open.create_crashes_file(version,"download","ver.txt")
                print("创建版本号文件")
            
            time.sleep(0.5)
            gc.collect()
        except Exception as e:
            print(f"显示python包失败: {str(e)},")
show_name()
