# 导入requests库，用于发送HTTP请求
import requests
# 导入Lock类，用于线程同步
from threading import Lock
# 导入time模块，用于时间相关操作
import time
# 导入os模块，用于操作系统相关功能
import os
# 禁用requests库的SSL警告
requests.packages.urllib3.disable_warnings()

# 动态设置最大线程数，基于CPU核心数计算，最大不超过32
MAX_THREADS = min(32, (os.cpu_count() or 1) * 4)
# 全局下载状态标志
is_downloading = True

def download_chunk(url, start_byte, end_byte, file_path, headers=None, retries=3, verify_ssl=False, speed_limit=None):
    """
    下载文件的指定字节范围
    :param url: 文件URL地址
    :param start_byte: 起始字节位置
    :param end_byte: 结束字节位置
    :param file_path: 文件保存路径
    :param headers: 自定义请求头
    :param retries: 重试次数
    :param verify_ssl: SSL验证开关
    :param speed_limit: 速度限制（字节/秒）
    :return: 下载成功返回True，否则返回False
    """
    headers = headers or {}
    headers['Range'] = f'bytes={start_byte}-{end_byte}'
    lock = Lock()

    for attempt in range(retries):
        try:
            if not is_downloading:
                return False
            with requests.get(url, headers=headers, stream=True, verify=False) as response:
                response.raise_for_status()
                with lock:
                    with open(file_path, 'r+b') as f:
                        f.seek(start_byte)
                        start_time = time.time()
                        bytes_downloaded = 0
                        for chunk in response.iter_content(chunk_size=65536):
                            if not is_downloading:
                                return False
                            while not is_downloading:  # 优化暂停逻辑
                                time.sleep(0.1)
                                if not is_downloading:
                                    return False
                            if chunk:
                                if speed_limit:
                                    elapsed = time.time() - start_time
                                    expected_time = bytes_downloaded / speed_limit
                                    if elapsed < expected_time:
                                        time.sleep(expected_time - elapsed)
                                f.write(chunk)
                                f.flush()
                                bytes_downloaded += len(chunk)
                                if len(chunk) != f.write(chunk):
                                    raise IOError("写入数据失败")
                return True
        except Exception as e:
            print(f"分块下载失败: {e}")
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return False

def pause_download():
    """暂停下载"""
    # 使用global关键字修改全局变量is_downloading
    global is_downloading
    # 将全局下载状态标志设置为False
    is_downloading = False

def resume_download():
    """恢复下载"""
    # 使用global关键字修改全局变量is_downloading
    global is_downloading
    # 将全局下载状态标志设置为True
    is_downloading = True