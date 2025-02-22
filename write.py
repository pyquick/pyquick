from key import gen_key,check_if_available,get_key
import hashlib
keys=[]

for i in range(10000):
    key=gen_key.generate_key()