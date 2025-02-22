import random
def randint(a, b):
    a, b = sorted((a, b))  # 确保 a <= b
    return random.randint(a, b)

def randchr(a, b):
    return chr(randint(ord(a), ord(b)))