from save_path import sav_path
import requests
def get_key_from_online(n:int|None):
    url="https://pyquick.github.io/info/key.json"
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response=requests.get(url,headers=headers)
    data=response.json()
    if n is None:
        return data
    key=data[f"{str(n)}"]
    return key

def get_key_from_local(path:str,filename:str, n:int | None):
    if n is None:
        key=sav_path.read_json(path,filename)
        return key
    key=sav_path.read_json(path,filename)[f"{str(n)}"]
    return key