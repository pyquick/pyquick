import re
from pmath import sort
import base64
import sys
import hashlib
r=r'pyquick\d.+[a-z]+..b\d+'
sys.set_int_max_str_digits(999999999)
def decode_key(key:str):
    try:
        key2=key.split("pyquick")[-1]
        key3=key2.split("..b")[0].encode()
        base=key2.split("..b")[1]
        
        if(int(base)==16):
            key4=base64.b16decode(key3).decode()
        elif(int(base)==64):
            key4=base64.b64decode(key3).decode()
        elif(int(base)==85):
            key4=base64.b85decode(key3).decode()
        keyz="pyquick"+key4+"..b"+base
        return str(keyz)
    except:
        return key
def check_key(key):
    if re.match(r,key)!=None:
        return True
    else:
        return False
def sort_key(key):
    if check_key(key):
        key_num=str(key).split("pyquick")[1]
        key_num=key_num.split(".")
        key_num.remove(key_num[-1])
        key_num.remove(key_num[-1])
        key_num.remove(key_num[-1])

        for i in range(len(key_num)):
            key_num[i]=int(key_num[i])
        key_num=sort.quicksort(key_num)
        return key_num
    else:
        return []
#将其拆分a,b两组,两组数个数相同.
def get_number(key):
    
    nums=sort_key(key)
    if len(nums)>0:
        if(len(nums)%2==1):
            nums.pop(len(nums)//2+1)
        a=nums[:len(nums)//2+1]
        b=nums[len(nums)//2+1:]
        aa=[]
        bb=[]
        for i in a:
            #密钥要求
            if int(i)>0: aa.append(int(i)) 
            else: return False
        for i in b:
            if int(i)>0: bb.append(int(i))
            else: return False
        #将它们进行互相相乘
        result1=1
        result2=1
        for i in aa:
            result1*=i
        for i in bb:
            result2*=i
        #对这两个数(相加,相乘,相减)取绝对值
        result3=abs(abs(result1-result2)+abs(result1+result2))*abs(result1+result2)        
        return str(result3)
    else:
        return False
#对后面的字母进行检查,与第3,12,16位进行对照(前4位)(1->a,2->b,以此类推)如果没有字母(或有字母但<=16),就直接返回"",如果有,去掉a,z即可,前8位是校验字母,无实际意义
def get_letter(key):
    
    num=get_number(key)
    zm=str(str(key).split(".")[-3])
    #print(zm)
    if(len(zm)<16):
        return False
    if len(num)>26 and len(zm)>16:
        ch1=ord(zm[0])
        ch2=ord(zm[1])
        ch3=ord(zm[2])
        #ch4=ord(zm[3])
        if int(num[2])!=ch1-97:
            return False
        if int(num[12-1])!=ch2-97:
            return False
        if int(num[16-1])!=ch3-97:
            return False
        #if int(num[19-1])!=ch4-97:
            #return False
        zm2=""
        for i in zm[3:]:
            if i=="a" or i=="z":
                continue
            else:
                zm2+=i
        return zm2
    else:
        return False
def key_hash(key):
    if check_key(key):
        if get_number(key)!=False:
            num=get_number(key)
        else:
            return False
        if get_letter(key)!=False:
            letter=get_letter(key)
        else:
            return False
        result="pyquick"+str(num)+letter
        result=result.encode()
        result=hashlib.sha512(result).hexdigest()
        return result
    else:
        return False