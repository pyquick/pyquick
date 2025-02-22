import re
from pmath import sort
import hashlib
from key import get_key
import base64
import sys
r=r'pyquick\d.+[a-z]+..b\d+'
sys.set_int_max_str_digits(9999999)
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
#对后面的字母进行检查,与第3,12,16,19,22,24,25,26位进行对照(前8位)(1->a,2->b,以此类推)如果没有字母(或有字母但<=16),就直接返回"",如果有,去掉a,z即可,前8位是校验字母,无实际意义
def get_letter(key):
    num=get_number(key)
    zm=str(str(key).split(".")[-3])
    if(len(zm)<16):
        return False
    if len(num)>26 and len(zm)>16:
        ch1=ord(zm[0])
        ch2=ord(zm[1])
        ch3=ord(zm[2])
        ch4=ord(zm[3])
        ch5=ord(zm[4])
        ch6=ord(zm[5])
        ch7=ord(zm[6])
        ch8=ord(zm[7])
        if int(num[2])!=ch1-97:
            return False
        if int(num[12-1])!=ch2-97:
            return False
        if int(num[16-1])!=ch3-97:
            return False
        if int(num[19-1])!=ch4-97:
            return False
        if int(num[22-1])!=ch5-97:
            return False
        if int(num[24-1])!=ch6-97:
            return False
        if int(num[25-1])!=ch7-97:
            return False
        if int(num[26-1])!=ch8-97:
            return False
        zm2=""
        for i in zm[8:]:
            if i=="a" or i=="z":
                continue
            else:
                zm2+=i
        return zm2
    else:
        return False
def get_base(key):
    bas=str(key).split(".")[-1].split("..b")[1]
    bas=int(bas)
    return bas
def check_key_available(key):
    keyy="pyquick"
    if check_key(key):
        if get_number(key)!=False:
            keyy+=get_number(key)[:14]
            if get_letter(key)!=False:
                bas=get_base(key)
                if bas==16:
                    decode_letter=base64.b16decode(get_letter(key)).decode('utf-8')
                if bas==64:
                    decode_letter=base64.b64decode(get_letter(key)).decode('utf-8')
                if bas==85:
                    decode_letter=base64.b85decode(get_letter(key)).decode('utf-8')
                keyy+=decode_letter
        #对keyy进行sha512加密
        kry=keyy
        keyy=hashlib.sha512(keyy.encode('utf-8')).hexdigest()
        return keyy
    else:
        return False