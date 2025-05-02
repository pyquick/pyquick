import os,getpass,gc
def repair_path(version):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes"
    if os.path.exists(path):
        gc.collect()
        return
    else:
        
        gc.collect()
        os.makedirs(path)
        return
def create_crashes_folder(version,folder):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}"
    if os.path.exists(path):
        gc.collect()
        return
    else:
        try:
            os.mkdir(path)
            gc.collect()
            return
        except Exception as e:
            print(e)
            gc.collect()
            raise e
def create_crashes_file(version,folder,filename):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}"
    if  not os.path.exists(path):
        gc.collect()
        raise FileNotFoundError
    else:
        try:
            with open(os.path.join(path,filename),'w') as f:
                f.write("")
                gc.collect()
                return
        except Exception as e:
            print(e)
            gc.collect()
            raise e

