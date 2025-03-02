import random
def randint(a, b):
    a, b = sorted((a, b))  # 确保 a <= b
    return random.randint(a, b)

def randchr(a:int|str, b:int|str):
    #检测a,b是否为数字
    if isinstance(a, int) and isinstance(b, int):
        return chr(randint(a, b))
    else:
        return chr(randint(ord(a), ord(b)))
def randspassword(length):
    
    b=''
    for i in range(length):
        
        a=random.randint(33,127)
        if a!=32 and a!=10:
            b+=chr(a)
    return b
