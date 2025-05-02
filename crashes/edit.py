import os,getpass
def edit_file(version,folder,filename,content):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}/{filename}"
    if  not os.path.exists(path):
        raise FileNotFoundError
    else:
        with open(path,'w') as f:
            f.write(content)
def read_file(version,folder,filename):
    path=f"/Users/{getpass.getuser()}/.pyquick/{version}/crashes/{folder}/{filename}"
    if  not os.path.exists(path):
        raise FileNotFoundError
    else:
        with open(path,'r') as f:
            return f.read()