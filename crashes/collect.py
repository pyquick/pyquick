import os,getpass,shutil
import gc
def delete_crashes_file(version,folder,filename):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}/{filename}"
    if  not os.path.exists(path):
        gc.collect()
        raise FileNotFoundError
    else:
        os.remove(path)
        gc.collect()
        return
def delete_crashes_folder(version,folder):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}"
    if  not os.path.exists(path):
        gc.collect()
        raise FileNotFoundError
    else:
        shutil.rmtree(path)
        gc.collect()
        return
def delete_crashes_folder_all(version):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes"
    if  not os.path.exists(path):
        gc.collect()
        raise FileNotFoundError
    else:
        shutil.rmtree(path)