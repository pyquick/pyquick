import platform
#darwin 23-20 对应macOS Sequoia 15.3 --macOS Big Sur 11.7.10 
def get_system_release_build_version():
    return platform.release()
def get_system_name():
    return platform.system()
def get_mac_machine():
    if (platform.machine()=="x86_64"):
        return "Intel"
    else:
        return "Apple Silicon" 
