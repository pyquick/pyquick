from pmath import randany
def generate_key():
    key="pyquick"
    num_range=randany.randint(100,9999)
    for i in range(num_range):
        key+=str(randany.randint(10,9999))
        key+="."
    num_range2=randany.randint(16,9999)
    for i in range(8):
        key+=str(randany.randchr("a","z"))
    for i in range(num_range2):
        key+=str(randany.randchr("b","y"))
    key+="..b"
    ba=randany.randint(1,3)
    if ba==1:
        key+="16"
    elif ba==2:
        key+="64"
    else:
        key+="85"
    return key
