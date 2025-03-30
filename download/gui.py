# 导入sys模块，用于系统相关操作
import sys
# 导入time模块，用于时间相关操作
import time
# 导入logging模块，用于日志记录
import logging
# 导入PyQt6相关模块，用于GUI开发
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QProgressBar, QListWidget, QLineEdit, QHBoxLayout,
                             QTabWidget,
                             QLabel, QPushButton, QScrollArea, QMessageBox, QTableWidgetItem, QTableWidget, QSpinBox)
# 导入PyQt6相关模块，用于多线程和信号槽机制
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QMutex, QMutexLocker, QWaitCondition
# 导入下载管理器模块
from download.downloader import download_manager
# 导入下载模块
from download import downloader

# 配置日志系统
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)

class DownloadThread(QThread):
    """
    下载线程类，继承自QThread
    负责管理下载过程，包括进度更新、状态管理、错误处理等
    """
    # 定义信号，用于更新下载进度
    progress_updated = pyqtSignal(int, float, str)  # 已下载字节数，进度百分比，下载速度
    # 定义信号，用于更新下载状态
    status_changed = pyqtSignal(str)
    # 定义信号，用于更新线程状态
    thread_status_updated = pyqtSignal(int, str)
    # 定义信号，用于处理下载错误
    error_occurred = pyqtSignal(str)
    # 定义信号，用于下载完成
    finished = pyqtSignal(bool)
    # 新增信号，用于更新文件大小
    file_size_updated = pyqtSignal(int)

    def __init__(self, url, save_path, num_threads):
        """
        初始化下载线程
        :param url: 下载URL
        :param save_path: 保存路径
        :param num_threads: 线程数
        """
        # 调用父类的初始化方法
        super().__init__()
        # 设置下载URL
        self.url = url
        # 设置保存路径
        self.save_path = save_path
        # 设置线程数
        self.num_threads = num_threads
        # 创建QMutex对象，用于线程同步
        self.mutex = QMutex()
        # 设置停止标志，初始为False
        self.should_stop = False
        # 设置暂停标志，初始为False
        self.paused = False
        # 设置文件大小，初始为0
        self.file_size = 0
        # 设置已下载字节数，初始为0
        self.downloaded_bytes = 0
        # 设置下载开始时间，初始为0
        self.start_time = 0
        # 设置上次更新时间，初始为0
        self.last_update = 0
        # 设置更新间隔，初始为0.1秒
        self.update_interval = 0.1
        self.supports_partial = False
        # 添加多线程支持状态
        self.multi_thread_supported = False
        self.condition = QWaitCondition()  # 添加条件变量

        try:
            self._get_file_info()
        except Exception as e:
            self._update_status("Failed to get file info")
            self.error_occurred.emit(f"Initialization failed: {str(e)}")
            self.file_size = 0

    def _get_file_info(self):
        try:
            self.file_size, self.supports_partial = downloader.get_file_info(self.url)
            if self.file_size <= 0:
                raise ValueError("Server returned invalid file size")
            self.multi_thread_supported = self.supports_partial
            logging.debug(f"File info acquired - Size: {self.file_size}, Partial: {self.supports_partial}")
            self.file_size_updated.emit(self.file_size)  # 先发送文件大小信号
            self.status_changed.emit(f"File size: {self._format_size(self.file_size)} | Multi-thread: {'Supported' if self.multi_thread_supported else 'Not supported'}")
        except Exception as e:
            logging.error(f"File info error: {str(e)}")
            self._update_status("Failed to get file info")
            raise

    def _format_size(self, size):
        """Format file size for display"""
        # 根据文件大小选择合适的单位
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def run(self):
        """Main download logic"""
        try:
            # 使用QMutexLocker进行线程同步
            with QMutexLocker(self.mutex):
                # 设置停止标志为False
                self.should_stop = False
                # 设置暂停标志为False
                self.paused = False
                # 记录下载开始时间
                self.start_time = time.time()
                # 设置已下载字节数为0
                self.downloaded_bytes = 0

            # 发送信号，更新状态为开始下载
            self._update_status("Starting download...")
            # 调用开始下载的方法
            self._start_download(self.supports_partial)

        except Exception as e:
            # 记录下载错误日志
            logging.error(f"Download error: {str(e)}")
            # 发送信号，处理下载错误
            self.error_occurred.emit(str(e))
            # 发送信号，下载完成，结果为False
            self.finished.emit(False)
        finally:
            # 调用清理资源的方法
            self._cleanup()

    def _start_download(self, supports_partial):
        """Start the download process"""
        def progress_callback(chunk):
            # 调用处理进度更新的方法
            self._handle_progress_update(chunk)

        try:
            # 调用下载管理器进行下载
            success = download_manager(
                self.url,
                self.save_path,
                self.num_threads,
                progress_callback=progress_callback,
                thread_status_callback=self._handle_thread_status,
                verify_ssl=False
            )
            # 调用处理下载结果的方法
            self._handle_download_result(success)
        except Exception as e:
            # 记录下载管理器错误日志
            logging.error(f"Download manager error: {str(e)}")
            # 抛出异常
            raise

    def _handle_progress_update(self, chunk_size):
        """Handle progress update (thread-safe)"""
        with QMutexLocker(self.mutex):
            if self.should_stop:
                return

            while self.paused and not self.should_stop:
                self.condition.wait(self.mutex, 100)  # 使用带超时的等待

            current_time = time.time()
            self.downloaded_bytes += chunk_size

            elapsed = current_time - self.start_time
            speed = (self.downloaded_bytes / elapsed) if elapsed > 0 else 0

            if self.file_size > 0:
                progress = (self.downloaded_bytes / self.file_size * 100)
            else:
                progress = 0

            self.last_update = current_time

            self.progress_updated.emit(
                self.downloaded_bytes,
                progress,
                self._format_speed(speed)
            )

    def _calculate_update_interval(self, speed):
        """Dynamically adjust UI update frequency based on download speed"""
        # 根据下载速度动态调整更新间隔
        if speed < 1024 * 512:  # < 512KB/s
            return 0.5
        elif speed < 1024 * 1024 * 2:  # < 2MB/s
            return 0.2
        else:
            return 0.1

    def _format_speed(self, speed):
        """Format speed display"""
        # 定义速度单位
        units = ['B/s', 'KB/s', 'MB/s']
        # 初始化单位索引
        unit_index = 0
        # 根据速度大小选择合适的单位
        while speed >= 1024 and unit_index < 2:
            speed /= 1024
            unit_index += 1
        # 返回格式化后的速度字符串
        return f"{speed:.2f} {units[unit_index]}"

    def _handle_thread_status(self, thread_id, status):
        """Handle thread status update"""
        # 发送信号，更新线程状态
        self.thread_status_updated.emit(thread_id, status)

    def _handle_download_result(self, success):
        """Handle final download result"""
        # 如果下载成功
        if success:
            # 发送信号，更新状态为下载完成
            self._update_status("Download complete")
            # 发送信号，下载完成，结果为True
            self.finished.emit(True)
        else:
            # 使用QMutexLocker进行线程同步
            with QMutexLocker(self.mutex):
                # 如果已下载字节数大于0
                if self.downloaded_bytes > 0:
                    # 发送信号，更新状态为部分下载完成
                    self._update_status("Partial download complete")
                else:
                    # 发送信号，更新状态为下载失败
                    self._update_status("Download failed")
                # 发送信号，下载完成，结果为False
                self.finished.emit(False)

    def _cleanup(self):
        """Clean up resources"""
        # 使用QMutexLocker进行线程同步
        with QMutexLocker(self.mutex):
            # 设置停止标志为True
            self.should_stop = True

    def request_stop(self):
        """Request to stop the download"""
        # 使用QMutexLocker进行线程同步
        with QMutexLocker(self.mutex):
            # 设置停止标志为True
            self.should_stop = True
            # 发送信号，更新状态为正在停止下载
            self._update_status("Stopping download...")

    def toggle_pause(self):
        """Pause/resume the download"""
        with QMutexLocker(self.mutex):
            self.paused = not self.paused
            self.condition.wakeAll() if not self.paused else None  # 唤醒等待的线程
            # 根据暂停状态设置状态信息
            status = "Paused" if self.paused else "Resumed"
            # 发送信号，更新状态信息
            self._update_status(status)
            # 记录状态信息日志
            logging.info(status)

    def _update_status(self, message):
        """更新下载状态"""
        # 发送信号，更新下载状态
        self.status_changed.emit(message)


class ThreadStatusWindow(QWidget):
    """
    线程状态监控窗口
    使用表格显示每个下载线程的实时状态
    """
    def __init__(self, num_threads):
        """
        初始化线程状态窗口
        :param num_threads: 线程数量
        """
        super().__init__()
        self.num_threads = num_threads
        self._init_ui()
        self.thread_states = ["Waiting"] * num_threads

    def _init_ui(self):
        """Initialize thread status window with table view"""
        self.setWindowTitle("Thread Status Monitor")
        self.setGeometry(300, 300, 600, 400)  # 调整窗口大小以适应表格

        layout = QVBoxLayout()
        
        # 创建表格控件
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)  # 设置4列：线程ID、状态、进度、速度
        self.table.setHorizontalHeaderLabels(["Thread ID", "Status", "Progress", "Speed"])
        self.table.setRowCount(self.num_threads)
        
        # 初始化表格内容
        for i in range(self.num_threads):
            self.table.setItem(i, 0, QTableWidgetItem(f"Thread {i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem("Waiting"))
            self.table.setItem(i, 2, QTableWidgetItem("0%"))
            self.table.setItem(i, 3, QTableWidgetItem("0 B/s"))
        
        # 设置表格样式
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_status(self, thread_id, status):
        """Update the status of a specific thread in the table"""
        if 0 <= thread_id < self.num_threads:
            # 更新状态列
            self.table.item(thread_id, 1).setText(status)
            # 更新时间戳
            self.table.item(thread_id, 1).setToolTip(time.strftime('%H:%M:%S'))
            self.thread_states[thread_id] = status

    def update_progress(self, thread_id, progress):
        """Update the progress of a specific thread in the table"""
        if 0 <= thread_id < self.num_threads:
            self.table.item(thread_id, 2).setText(f"{progress}%")

    def update_speed(self, thread_id, speed):
        """Update the speed of a specific thread in the table"""
        if 0 <= thread_id < self.num_threads:
            self.table.item(thread_id, 3).setText(speed)


class DownloadApp(QWidget):
    """
    主应用程序窗口
    管理下载的GUI界面和用户交互
    """
    def __init__(self, url, save_path, num_threads):
        """
        初始化下载应用程序
        :param url: 下载URL
        :param save_path: 保存路径
        :param num_threads: 线程数
        """
        # 调用父类的初始化方法
        super().__init__()
        # 设置下载URL
        self.url = url
        # 设置保存路径
        self.save_path = save_path
        # 设置线程数
        self.num_threads = num_threads
        # 初始化线程状态窗口
        self.thread_window = ThreadStatusWindow(num_threads)
        # 调用初始化UI的方法
        self._init_ui()
        # 调用设置下载线程的方法
        self._setup_thread()
        # 添加文件总大小变量
        self.total_size = 0
        self.last_update = 0  # 添加最后更新时间戳
        # 程序启动时直接开始下载
        QTimer.singleShot(100, self.start_download)

    def _init_ui(self):
        """Initialize the main interface"""
        self.setWindowTitle("Download Manager")
        self.setGeometry(100, 100, 600, 400)

        # Main layout
        main_layout = QVBoxLayout()

        # Progress bar and thread count
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.thread_label = QLabel(f"Threads: {self.num_threads}")
        main_layout.addWidget(self.thread_label)
        main_layout.addWidget(self.progress)

        # Add pause and stop buttons
        self.btn_pause = QPushButton("Pause Download")
        self.btn_stop = QPushButton("Stop Download")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_stop.clicked.connect(self.stop_download)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_pause)
        button_layout.addWidget(self.btn_stop)
        main_layout.addLayout(button_layout)

        # Tab widget
        self.tabs = QTabWidget()
        self.download_tab = self._create_download_tab()
        self.options_tab = self._create_options_tab()
        self.connections_tab = self._create_connections_tab()
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.options_tab, "Options")
        self.tabs.addTab(self.connections_tab, "Connections")
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def _create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.url_label = QLabel(f"URL: {self.url}")
        self.status_label = QLabel("Status: Getting...")
        self.size_label = QLabel("File Size: Calculating...")
        self.downloaded_label = QLabel("Downloaded: 0%")
        self.speed_label = QLabel("Speed: 0 B/s")
        self.remaining_time_label = QLabel("Remaining Time: < 1 sec")

        layout.addWidget(self.url_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.size_label)
        layout.addWidget(self.downloaded_label)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.remaining_time_label)

        tab.setLayout(layout)
        return tab

    def _create_options_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.current_speed_label = QLabel("Current Speed: 0 KB/s")
        self.speed_limit_input = QLineEdit()
        self.speed_limit_input.setPlaceholderText("Enter speed limit in KB/s")
        self.apply_speed_limit_btn = QPushButton("Apply")

        speed_limit_layout = QHBoxLayout()
        speed_limit_layout.addWidget(QLabel("Limit Speed to:"))
        speed_limit_layout.addWidget(self.speed_limit_input)
        speed_limit_layout.addWidget(self.apply_speed_limit_btn)

        layout.addWidget(self.current_speed_label)
        layout.addLayout(speed_limit_layout)

        tab.setLayout(layout)
        return tab

    def _create_connections_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        # Thread status list
        self.thread_status_list = QListWidget()
        layout.addWidget(self.thread_status_list)

        # Thread controls
        control_layout = QVBoxLayout()
        self.max_threads_input = QSpinBox()
        self.max_threads_input.setRange(1, 64)
        self.max_threads_input.setValue(self.num_threads)
        self.apply_threads_btn = QPushButton("Apply")
        control_layout.addWidget(QLabel("Max Threads:"))
        control_layout.addWidget(self.max_threads_input)
        control_layout.addWidget(self.apply_threads_btn)
        layout.addLayout(control_layout)

        tab.setLayout(layout)
        return tab

    def _setup_thread(self):
        self.download_thread = DownloadThread(
            self.url,
            self.save_path,
            self.num_threads
        )
        # 调整信号连接顺序
        self.download_thread.file_size_updated.connect(self.update_file_size)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.status_changed.connect(self.update_status)
        self.download_thread.thread_status_updated.connect(self.thread_window.update_status)
        self.download_thread.error_occurred.connect(self.show_error)
        self.download_thread.finished.connect(self.handle_finish)

    def start_download(self):
        """Start the download"""
        # 启用暂停下载按钮
        self.btn_pause.setEnabled(True)
        # 启用停止下载按钮
        self.btn_stop.setEnabled(True)
        # 设置进度条初始值为0
        self.progress.setValue(0)
        # 启动下载线程
        self.download_thread.start()

    def toggle_pause(self):
        """Toggle pause/resume state"""
        # 切换暂停/恢复状态
        self.download_thread.toggle_pause()
        # 根据暂停状态设置按钮文本
        self.btn_pause.setText("Resume Download" if self.download_thread.paused else "Pause Download")

    def stop_download(self):
        """Stop the download"""
        # 请求停止下载
        self.download_thread.request_stop()
        # 禁用停止下载按钮
        self.btn_stop.setEnabled(False)

    def update_file_size(self, file_size):
        if file_size <= 0:  # 添加数据校验
            return
        self.total_size = file_size
        formatted_size = self._format_size(file_size)
        self.size_label.setText(f"File size: {formatted_size}")

    def update_progress(self, downloaded, percent, speed):
        current_time = time.time()
        if current_time - self.last_update < 0.1:  # 节流控制，限制刷新频率
            return
        self.last_update = current_time

        self.progress.setValue(int(percent))  # 直接使用线程传递的百分比
        self.downloaded_label.setText(f"Downloaded: {percent:.2f}%")
        self.speed_label.setText(f"Speed: {speed}")

        if self.total_size > 0 and float(speed.split()[0]) > 0:
            remaining_bytes = self.total_size - downloaded
            speed_value = float(speed.split()[0])
            speed_unit = speed.split()[1]
            
            if speed_unit == "KB/s":
                speed_bytes = speed_value * 1024
            elif speed_unit == "MB/s":
                speed_bytes = speed_value * 1024 * 1024
            else:
                speed_bytes = speed_value

            remaining_seconds = remaining_bytes / speed_bytes
            self._update_remaining_time(remaining_seconds)

    def _update_remaining_time(self, seconds):
        """修正剩余时间显示逻辑"""
        if seconds < 1:
            self.remaining_time_label.setText("Remaining Time: < 1 sec")
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            
            time_str = ""
            if hours > 0:
                time_str += f"{hours} h "
            if minutes > 0 or hours > 0:
                time_str += f"{minutes} min "
            time_str += f"{secs} sec"
            
            self.remaining_time_label.setText(f"Remaining Time: {time_str}")

    def _format_size(self, size):
        """Format file size for display"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def update_status(self, message):
        """Update status information"""
        # 更新状态信息
        self.status_label.setText(f"Status: {message}")

    def show_error(self, message):
        """Show error dialog"""
        # 显示错误对话框
        QMessageBox.critical(self, "Error", message, QMessageBox.StandardButton.Ok)

    def handle_finish(self, success):
        """Handle download completion"""
        # 如果下载成功
        if success:
            # 显示下载完成对话框
            QMessageBox.information(self, "Complete", "File downloaded successfully!")
        else:
            # 显示下载未完成对话框
            QMessageBox.warning(self, "Warning", "Download incomplete")
        
        # 恢复按钮状态
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def show_thread_status(self):
        """Show thread status window"""
        # 显示线程状态窗口
        self.thread_window.show()

    def closeEvent(self, event):
        """Safe close handling"""

        # 如果下载线程正在运行
        if self.download_thread.isRunning():
            # 显示确认退出对话框
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Download is in progress, are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            # 如果用户选择是
            if reply == QMessageBox.StandardButton.Yes:
                # 请求停止下载
                self.download_thread.request_stop()
                # 等待下载线程结束，最多等待2秒
                self.download_thread.wait(2000)
                # 接受关闭事件
                event.accept()
            else:
                # 忽略关闭事件
                event.ignore()
        else:
            # 接受关闭事件
            event.accept()

if __name__ == "__main__":
    # 创建QApplication对象
    app = QApplication(sys.argv)
    # 创建DownloadApp对象
    window = DownloadApp(
        url="https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal",
        save_path="/Users/liexe/Desktop/VSCode-darwin-universal.zip",
        num_threads=8
    )
    # 显示主窗口
    window.show()
    # 进入主事件循环
    sys.exit(app.exec())