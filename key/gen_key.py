from pmath import randany
from key import rule
import base64
def generate_key():
    num_range=randany.randint(100,999)
    key=""
    for i in range(num_range):
        key+=str(randany.randint(10,99999))
        key+="."
    num_range2=randany.randint(16,999)
    for i in range(8):
        key+=str(randany.randchr("a","i"))
    for i in range(num_range2):
        key+=str(randany.randchr("b","y"))
    #key+="..b"
    ba=randany.randint(1,3)
    if ba==1:
        key=base64.b16encode(key.encode())
        c="16"
    elif ba==2:
        c="64"
        key=base64.b64encode(key.encode())
    else:
        c="85"
        key=base64.b85encode(key.encode())
    keyz="pyquick"+key.decode()+"..b"+c
    return keyz
def generate_true_key():#表示获得一个正确的密钥,但并不确保和网络上的哈希匹配
    while True:
        a=generate_key()
        a=str(rule.decode_key(a))
        b=rule.key_hash(a)
        if(b!=False):
            return a
