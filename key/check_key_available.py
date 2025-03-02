from key import rule,get_key
from save_path import sav_path

def check_key_available_local(key,filepath:str,filename:str):
    key=rule.decode_key(key)
    key=rule.key_hash(key)
    if key==False:
        return False
    soc=sav_path.read_json(filepath,filename)
    for i in range(1,100):
        if key in soc[str(i)]:
            return True
    return False
def check_key_available_online(key):
    key=rule.decode_key(key)
    key=rule.key_hash(key)
    if key==False:
        return False
    soc=get_key.get_key_from_online(None)
    for i in soc:
        if key in soc[i]:
            return True
    return False
