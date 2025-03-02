# 这是什么?

这是deepdev的激活密钥插件,大部分可给个人调用测试.(用这个模块破解非常费时)

# 函数

## gen_key
1. gengerate_key() 生成一个随机(部分加密)的密钥,正确与否不知道

2. gengerate_true_key() 生成一个正确的密钥(格式合法,可以通过所有步骤,但不知道是否与网上匹配)

## get_key

1. get_key_from_local(path:str,filename:str, n:int | None) 从文件中获取密钥,文件格式为json

2. get_key_from_url(n:int|None) 从url中获取密钥,  [url is here](https://pyquick.github.io/info/key_hash.json)

## rule

1. decode_key(key) 解密密钥(自动),rule的其他操作都基于这个

2. check_key(key) 检查密钥格式是否正确,正确返回True,错误返回False(正则表达式:'pyquick\d.+[a-z]+..b\d+')

3. sort_key(key) 将密钥数字部分进行排序,调用quicksort算法,返回排序后的密钥('\d.+'部分)

4. get_number(key) 对密钥数字部分进行切割,最终得到一个数字(这个数字非常大,大约有100位)

5. get_letter(key) 对密钥字母部分进行操作/校验,最终返回false/字符串

6. key_hash(key) 对密钥进行hash,返回hash后的密钥(sha512)

>[!NOTE]
>这些可以分开调用,也可以只调用1和6查看密钥状态

## check_key_available