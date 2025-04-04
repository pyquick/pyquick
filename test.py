from download import downloader

if __name__ == "__main__":
    downloader.download_manager(
        url="https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal",
        save_path="/Users/liexe/Desktop",
        num_threads=32,
        progress_callback=None,
        thread_status_callback=None,
        verify_ssl=False,
        speed_limit=1024 # 1MB/s
    )