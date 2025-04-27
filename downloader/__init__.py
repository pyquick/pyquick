# Downloader module for Pyquick
# Provides download functionality with pause, resume and multi-threading capabilities

from .DownloadManager import DownloadManager, DownloadTask
from .downloader import Downloader

# 创建一个单例下载管理器实例
download_manager = DownloadManager()

__all__ = ['download_manager', 'DownloadManager', 'DownloadTask', 'Downloader'] 