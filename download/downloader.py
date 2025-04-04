# 导入os模块，用于操作系统相关功能
import os
# 导入requests库，用于发送HTTP请求
import requests
from tqdm import tqdm
# 导入ThreadPoolExecutor和as_completed，用于多线程下载
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入Lock类，用于线程同步
from threading import Lock
# 导入math模块，用于数学计算
import math
# 导入time模块，用于时间相关操作
import time
# 禁用requests库的SSL警告
requests.packages.urllib3.disable_warnings()

# 动态设置最大线程数，基于CPU核心数计算，最大不超过32
MAX_THREADS = min(32, (os.cpu_count() or 1) * 4)
# 全局下载状态标志
is_downloading = True

def download_chunk(url, start_byte, end_byte, file_path, headers=None, retries=3, verify_ssl=False, speed_limit=None, progress_queue=None):
    """
    下载文件的指定字节范围
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
                        bytes_written = 0
                        for chunk in response.iter_content(chunk_size=65536):
                            if not is_downloading:
                                return False
                            while not is_downloading:  # 优化暂停逻辑
                                time.sleep(0.1)
                                if not is_downloading:
                                    return False
                            if chunk:
                                # 计算允许写入的最大字节数
                                allowed_bytes = end_byte - start_byte + 1 - bytes_written
                                if allowed_bytes <= 0:
                                    break  # 达到分块末尾，停止写入
                                # 截断chunk以确保不超过范围
                                chunk = chunk[:allowed_bytes]
                                f.write(chunk)
                                f.flush()
                                bytes_written += len(chunk)
                                if progress_queue:
                                    progress_queue.put(len(chunk))
                        # 强制刷新文件系统缓存
                        os.fsync(f.fileno())
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

def get_file_info(url):
    """
    获取文件信息和服务器能力
    :param url: 文件URL
    :param verify_ssl: SSL验证开关
    :return: (文件大小, 是否支持分块下载, 文件名)
    """
    try:
        # 发送HTTP HEAD请求，获取文件信息
        response = requests.head(url, verify=False, allow_redirects=True)
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

        # 从Content-Disposition中获取文件名
        content_disposition = response.headers.get('Content-Disposition', '')

        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"\'').split(';')[0]
            file_name = filename
        else:
            from urllib.parse import urlparse
            # 若未找到，尝试从 URL 路径或参数推断
            parsed_url = urlparse(url)
            path_segment = parsed_url.path.split('/')[-1]  # 路径的最后一段
            os_param = parsed_url.query.split('os=')[-1].split('&')[0]  # 提取 os 参数
            file_name = f"{path_segment}-{os_param}"


        # 如果从Content-Disposition中未获取到文件名，则从URL路径中提取
        if not file_name:
            from urllib.parse import urlparse, unquote

            parsed_url = urlparse(url)
            # 从路径中提取文件名
            file_name = os.path.basename(unquote(parsed_url.path))
            # 如果路径中没有文件名，则从查询参数中提取
            if not file_name:
                query_params = parsed_url.query.split('&')
                # 优先查找包含常见文件名参数的值
                for param in query_params:
                    if '=' in param:
                        key, value = param.split('=')
                        if key.lower() in ['file', 'name', 'filename']:
                            # 解码URL编码的值并去除可能的路径
                            file_name = os.path.basename(unquote(value))
                            if file_name:  # 确保提取到有效文件名
                                break
            # 如果仍未获取到文件名，则使用默认文件名
            if not file_name:
                # 从URL中提取最后一个非空路径段作为文件名
                path_segments = [s for s in parsed_url.path.split('/') if s]
                if path_segments:
                    file_name = path_segments[-1]
                else:
                    file_name = "downloaded_file"

        # 确保文件名不包含非法字符
        #file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-'))

        # 返回文件大小、是否支持分块下载和文件名
        return file_size, supports_partial, file_name
    except requests.RequestException as e:
        # 打印获取文件信息失败的错误信息
        print(f"获取文件信息失败: {e}")
        # 返回文件大小为0，不支持分块下载，文件名为None
        return 0, False, None

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
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            # 使用tqdm显示进度条
            from tqdm import tqdm
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc=file_path)
            # 以写二进制模式打开文件
            with open(file_path, 'wb') as f:
                # 遍历响应内容，每次读取8192字节
                for chunk in response.iter_content(chunk_size=8192):
                    # 如果chunk不为空，则写入文件
                    if chunk:  # Filter out empty chunks
                        f.write(chunk)
                        # 更新进度条
                        progress_bar.update(len(chunk))
                        # 如果提供了进度回调函数，则调用它
                        if progress_callback:
                            progress_callback(len(chunk))
            # 关闭进度条
            progress_bar.close()
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
    from multiprocessing import Process, Queue, Lock, freeze_support

    def _download(num_threads):  # 将num_threads作为参数传入
        freeze_support()  # 添加freeze_support()以支持多进程
        num_threads = min(num_threads, MAX_THREADS)  # 使用传入的num_threads
        chunk_size = file_size // num_threads
        processes = []
        progress_queue = Queue()
        lock = Lock()
        is_cancelled = False

        try:
            # 预先创建文件并设置大小
            with open(file_path, 'wb') as f:
                f.truncate(file_size)

            # 只在主进程中初始化进度条
            from tqdm import tqdm
            progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc=file_path)

            for i in range(num_threads):
                if is_cancelled:
                    break
                start = i * chunk_size
                end = start + chunk_size - 1 if i != num_threads -1 else file_size - 1

                if thread_status_callback:
                    thread_status_callback(i, 'Downloading')

                p = Process(target=download_chunk, args=(url, start, end, file_path, None, 3, verify_ssl, speed_limit, progress_queue))
                p.start()
                processes.append(p)

            while any(p.is_alive() for p in processes):
                while not progress_queue.empty():
                    chunk_size = progress_queue.get()
                    with lock:
                        progress_bar.update(chunk_size)
                        if progress_callback:
                            progress_callback(chunk_size)
                time.sleep(0.1)

            progress_bar.close()

            for p in processes:
                p.join()

            # 检查文件大小是否与预期一致
            if os.path.getsize(file_path) != file_size:
                print("Downloaded file size does not match expected size.")
                return False

            return not is_cancelled
        except Exception as e:
            print(f"Multithread download failed: {e}")
            return False

    if __name__ == '__main__':
        return _download(num_threads)  # 传入num_threads参数
    else:
        return _download(num_threads)  # 传入num_threads参数

def download_manager(url, save_path, num_threads, progress_callback=None, thread_status_callback=None, verify_ssl=False, speed_limit=None):
    """
    下载主控制器
    :param url: 文件URL
    :param save_path: 保存路径
    :param num_threads: 线程数
    :param progress_callback: 进度回调函数
    :param thread_status_callback: 线程状态回调函数
    :param verify_ssl: SSL验证开关
    :param speed_limit: 速度限制（字节/秒）
    :return: 下载成功返回True，否则返回False
    """
    # 检查save_path是否为空
    if not save_path:
        raise ValueError("Save path cannot be empty")

    # 获取文件大小、是否支持分块下载和文件名
    file_size, supports_partial, file_name = get_file_info(url)

    # 如果文件大小为0
    if file_size == 0:
        # 抛出异常
        raise ValueError("Invalid file URL or unavailable resource")

    # 创建保存目录
    parent_dir = os.path.dirname(save_path)
    if parent_dir:  # 如果父目录路径不为空
        os.makedirs(parent_dir, exist_ok=True)

    # 如果从Content-Disposition中获取到了文件名，则使用该文件名
    if not file_name:
        # 改进文件名提取逻辑
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(url)
        file_name = os.path.basename(unquote(parsed_url.path))
        if not file_name:
            # 如果路径中没有文件名，尝试从查询参数中获取
            file_name = parsed_url.query.split('=')[-1] if '=' in parsed_url.query else "downloaded_file"
        # 如果文件名仍然为空，使用默认文件名
        if not file_name:
            file_name = "downloaded_file"
    # 确保文件名不包含非法字符
    file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-'))
    full_save_path = os.path.join(save_path, file_name)

    # 选择下载模式
    if supports_partial and num_threads > 1:
        # 使用多线程下载
        return multithread_download(
            url=url,
            file_path=full_save_path,
            file_size=file_size,
            num_threads=num_threads,
            progress_callback=progress_callback,
            thread_status_callback=thread_status_callback,
            verify_ssl=verify_ssl,
            speed_limit=speed_limit
        )
    else:
        # 使用单线程下载
        return singlethread_download(
            url=url,
            file_path=full_save_path,
            progress_callback=progress_callback,
            verify_ssl=verify_ssl
        )
