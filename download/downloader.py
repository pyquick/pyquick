# 导入os模块，用于操作系统相关功能
import os
# 导入requests库，用于发送HTTP请求
import requests
# 导入ThreadPoolExecutor和as_completed，用于多线程下载
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入Lock类，用于线程同步
from threading import Lock
# 导入download_chunk函数和MAX_THREADS常量
from download.chunk import download_chunk, MAX_THREADS
# 导入math模块，用于数学计算
import math
# 禁用requests库的SSL警告
requests.packages.urllib3.disable_warnings()

def get_file_info(url, verify_ssl=False):
    """
    获取文件信息和服务器能力
    :param url: 文件URL
    :param verify_ssl: SSL验证开关
    :return: (文件大小, 是否支持分块下载)
    """
    try:
        # 发送HTTP HEAD请求，获取文件信息
        response = requests.head(url, verify=False)
        # 检查HTTP响应状态码，如果不是200则抛出异常
        response.raise_for_status()

        # 获取文件大小
        file_size = int(response.headers.get('Content-Length', 0))
        # 如果文件大小小于等于0
        if file_size <= 0:
            # 发送HTTP GET请求，获取文件信息
            response = requests.get(url, stream=True, verify=False)
            # 获取文件大小
            file_size = int(response.headers.get('Content-Length', 0))
            # 关闭响应
            response.close()

        # 检查服务器是否支持分块下载
        supports_partial = 'bytes' in response.headers.get('Accept-Ranges', '')

        # 返回文件大小和是否支持分块下载
        return file_size, supports_partial
    except requests.RequestException as e:
        # 打印获取文件信息失败的错误信息
        print(f"获取文件信息失败: {e}")
        # 返回文件大小为0，不支持分块下载
        return 0, False

def singlethread_download(url, file_path, progress_callback=None, verify_ssl=False):
    """
    单线程下载实现
    :param url: 文件URL
    :param file_path: 保存路径
    :param progress_callback: 进度回调函数
    :param verify_ssl: SSL验证开关
    :return: 下载成功返回True，否则返回False
    """
    try:
        # 发送HTTP GET请求，stream=True表示流式下载
        with requests.get(url, stream=True, verify=False) as response:  # Disable SSL verification
            # 检查HTTP响应状态码，如果不是200则抛出异常
            response.raise_for_status()
            # 以写二进制模式打开文件
            with open(file_path, 'wb') as f:
                # 遍历响应内容，每次读取8192字节
                for chunk in response.iter_content(chunk_size=8192):
                    # 如果chunk不为空，则写入文件
                    if chunk:  # Filter out empty chunks
                        f.write(chunk)
                        # 如果提供了进度回调函数，则调用它
                        if progress_callback:
                            progress_callback(len(chunk))
        # 下载成功，返回True
        return True
    except Exception as e:
        # 打印下载失败的错误信息
        print(f"Download failed: {e}")
        # 下载失败，返回False
        return False

def multithread_download(url, file_path, file_size, num_threads=8, progress_callback=None, thread_status_callback=None, verify_ssl=False, speed_limit=None):
    """
    多线程下载实现
    :param url: 文件URL
    :param file_path: 保存路径
    :param file_size: 文件大小
    :param num_threads: 线程数
    :param progress_callback: 进度回调函数
    :param thread_status_callback: 线程状态回调函数
    :param verify_ssl: SSL验证开关
    :param speed_limit: 速度限制（字节/秒）
    :return: 下载成功返回True，否则返回False
    """
    # 动态调整线程数，不超过最大线程数
    num_threads = min(num_threads, MAX_THREADS)
    # 计算每个线程下载的字节范围
    chunk_size = file_size // num_threads
    # 初始化Future对象列表
    futures = []
    # 初始化已下载字节数
    downloaded = 0
    # 创建Lock对象，用于线程同步
    lock = Lock()
    # 初始化取消标志，初始为False
    is_cancelled = False

    try:
        # 预分配磁盘空间
        with open(file_path, 'wb') as f:
            f.truncate(file_size)

        # 创建线程池
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # 遍历线程数
            for i in range(num_threads):
                # 如果取消标志为True，则跳出循环
                if is_cancelled:
                    break
                # 计算当前线程的起始字节
                start = i * chunk_size
                # 计算当前线程的结束字节
                end = start + chunk_size - 1 if i != num_threads -1 else file_size - 1

                # 如果提供了线程状态回调函数，则调用它
                if thread_status_callback:
                    thread_status_callback(i, 'Downloading')

                # 提交下载任务到线程池
                future = executor.submit(
                    download_chunk,
                    url=url,
                    start_byte=start,
                    end_byte=end,
                    file_path=file_path,
                    verify_ssl=verify_ssl,
                    speed_limit=speed_limit
                )
                # 将Future对象添加到列表中
                futures.append(future)

            # 使用as_completed优化等待
            for future in as_completed(futures):
                # 如果取消标志为True，则跳出循环
                if is_cancelled:
                    break
                # 如果下载成功
                if future.result():
                    # 使用Lock对象进行线程同步
                    with lock:
                        # 更新已下载字节数
                        downloaded += chunk_size
                        # 如果提供了进度回调函数，则调用它
                        if progress_callback:
                            progress_callback(chunk_size)
        
        # 下载完成后验证文件大小
        if os.path.getsize(file_path) != file_size:
            # 打印文件大小不匹配的错误信息
            print("Downloaded file size does not match expected size.")
            # 返回False
            return False

        # 返回是否取消的标志
        return not is_cancelled
    except Exception as e:
        # 打印多线程下载失败的错误信息
        print(f"Multithread download failed: {e}")
        # 返回False
        return False

def download_manager(url, save_path, num_threads, progress_callback=None, thread_status_callback=None, verify_ssl=False):
    """
    下载主控制器
    :param url: 文件URL
    :param save_path: 保存路径
    :param num_threads: 线程数
    :param progress_callback: 进度回调函数
    :param thread_status_callback: 线程状态回调函数
    :param verify_ssl: SSL验证开关
    :return: 下载成功返回True，否则返回False
    """
    # 检查save_path是否为空
    if not save_path:
        raise ValueError("Save path cannot be empty")

    # 获取文件大小和是否支持分块下载
    file_size, supports_partial = get_file_info(url, verify_ssl)

    # 如果文件大小为0
    if file_size == 0:
        # 抛出异常
        raise ValueError("Invalid file URL or unavailable resource")

    # 创建保存目录
    parent_dir = os.path.dirname(save_path)
    if parent_dir:  # 如果父目录路径不为空
        os.makedirs(parent_dir, exist_ok=True)

    # 选择下载模式
    if supports_partial and num_threads > 1:
        # 使用多线程下载
        return multithread_download(
            url=url,
            file_path=save_path,
            file_size=file_size,
            num_threads=num_threads,
            progress_callback=progress_callback,
            thread_status_callback=thread_status_callback,
            verify_ssl=verify_ssl
        )
    else:
        # 使用单线程下载
        return singlethread_download(
            url=url,
            file_path=save_path,
            progress_callback=progress_callback,
            verify_ssl=verify_ssl
        )
