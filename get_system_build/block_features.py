from get_system_build import system_build
#如果是macOS High Sierra 10.13(darwin17)以下,则拒绝运行
def block_start():
    if system_build.get_system_name() == 'Darwin' and int(system_build.get_system_release_build_version().split('.')[0]) < 17:
        return False
    else:
        return True
def block_theme():
    if system_build.get_system_name() == 'Darwin'and int(system_build.get_system_release_build_version().split('.')[0]) < 21:
        return False
    else:
        return True
def block_python2():
    if system_build.get_system_name() == 'Darwin' and int(system_build.get_system_release_build_version().split('.')[0]) >=21:
        return False
    else:
        return True