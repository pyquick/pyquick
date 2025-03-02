#这里管理pyquick的proxy设置

#http://username:password@proxy_ip:proxy_port
def proxy_address(proxy_ip,proxy_port,username:str|None,password:str|None)->dict:
    proxies = {
        "http": f"http://{username}:{password}@{proxy_ip}:{proxy_port}",
        "https": f"https://{username}:{password}@{proxy_ip}:{proxy_port}",
    }
    return proxies