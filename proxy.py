#这里管理pyquick的proxy设置
from save_path import sav_path
import getpass
import os
from cryptography.fernet import Fernet
#http://username:password@proxy_ip:proxy_port
def proxy_address(proxy_ip,proxy_port,username:str|None,password:str|None,python_version:int)->dict:
    key=read_proxy(python_version)["key"].encode()
    cipher_suite = Fernet(key)
    if username!=None:
        username=cipher_suite.decrypt(username.encode()).decode()
    if password!=None:
        password=cipher_suite.decrypt(password.encode()).decode()
    if username==None or password==None or username=="" or password=="":
        proxies={
            "http": f"http://{proxy_ip}:{proxy_port}","https": f"https://{proxy_ip}:{proxy_port}"
        }
        return proxies
        #return {"http": f"http://{proxy_ip}:{proxy_port}","https": f"https://{proxy_ip}:{proxy_port}"}
    proxies = {
        "http": f"http://{username}:{password}@{proxy_ip}:{proxy_port}",
        "https": f"http://{username}:{password}@{proxy_ip}:{proxy_port}",
    }
    return proxies

def save_proxy(proxy_ip,proxy_port,username:str|None,password:str|None,python_version:int):
    path_b=f"/Users/{getpass.getuser()}/.pyquick/{python_version}"
    path=f"{path_b}/proxy"
    if not os.path.exists(path_b):
        os.mkdir(path_b)
        os.mkdir(f"{path_b}/proxy")
    else:
        try:
            os.mkdir(f"{path_b}/proxy")
        except:
            pass
    filename="proxy.json"
    proxy={"address":proxy_ip,"port":proxy_port,"username":None,"password":None,"key":None}
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    if username!=None or password!=None or username!="" or password!="":
        username=cipher_suite.encrypt(username.encode()).decode()
        password=cipher_suite.encrypt(password.encode()).decode()
        proxy["username"]=username
        proxy["password"]=password
    proxy["key"]=key.decode()
    sav_path.save_json(path,filename,"w",proxy)
def read_proxy(python_version:int)->dict|None:
    #用sav_path
    path=f"/Users/{getpass.getuser()}/.pyquick/{python_version}/proxy"
    filename="proxy.json"
    _results=sav_path.read_json(path,filename)
    key=_results["key"].encode()
    cipher_suite = Fernet(key)
    if _results["username"]!=None:
        _results["username"]=cipher_suite.decrypt(_results["username"].encode()).decode()
    if _results["password"]!=None:
        _results["password"]=cipher_suite.decrypt(_results["password"].encode()).decode()

    #return proxy_address(_results["address"],_results["port"],_results["username"],_results["password"])
    return _results
def proxy_set_status(enable,python_version:int):
    a=enable
    path_b = f"/Users/{getpass.getuser()}/.pyquick/{python_version}"
    path = f"{path_b}/proxy"
    if not os.path.exists(path_b):
        os.mkdir(path_b)
        os.mkdir(path)
    else:
        try:
            os.mkdir(path)
        except:
            pass
    sav_path.save_path(path,"check.txt","w",str(a))
def proxy_check_status(python_version:int)->bool:
    try:
        path=f"/Users/{getpass.getuser()}/.pyquick/{python_version}/proxy"
        filename="check.txt"
        _results=sav_path.read_path(path,filename,"readline")
        if _results=="True":
            return True
        else :
            return False
    except:
        return False
def password_set_status(enable,python_version:int):
    a=enable
    path_b = f"/Users/{getpass.getuser()}/.pyquick/{python_version}"
    path = f"{path_b}/proxy"
    if not os.path.exists(path_b):
        os.mkdir(path_b)
        os.mkdir(path)
    else:
        try:
            os.mkdir(path)
        except:
            pass
    sav_path.save_path(path,"check_password.txt","w",str(a))
def password_check_status(python_version:int)->bool:
    try:
        path=f"/Users/{getpass.getuser()}/.pyquick/{python_version}/proxy"
        filename="check_password.txt"
        _results=sav_path.read_path(path,filename,"readline")
        if _results=="True":
            return True
        else :
            return False
    except:
        return False