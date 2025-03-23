# 新增编码处理
from urllib.parse import quote
# 增加加密存储
from cryptography.fernet import Fernet
password = "admin"
key = Fernet.generate_key()
cipher_suite = Fernet(key)
a = cipher_suite.encrypt(password.encode())
b= cipher_suite.decrypt(a).decode()
print(key)
print(b)