import platform
def get_system_build():
    """获取系统版本"""
    system_build=(str(platform.platform().split("-")))
    return system_build
print(get_system_build())