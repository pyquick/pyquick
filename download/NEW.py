# gui.py
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QListWidget, QSpinBox,
    QGridLayout, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from downloader import download_manager, get_file_info
from chunk import MAX_THREADS, pause_download, resume_download
import threading

class DownloadSignals(QObject):
    update_progress = pyqtSignal(int)
    update_speed = pyqtSignal(float)
    update_status = pyqtSignal(str)
    update_file_size = pyqtSignal(int)
    update_downloaded = pyqtSignal(int, int)  # (downloaded, total)
    update_threads = pyqtSignal(int)
    thread_status = pyqtSignal(int, str)

class DownloadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = DownloadSignals()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # URL Input
        self.url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        layout.addWidget(self.url_label, 0, 0)
        layout.addWidget(self.url_input, 0, 1)

        # Save Path Input
        self.save_path_label = QLabel("Save Path:")
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("Enter the path to save the file")
        layout.addWidget(self.save_path_label, 1, 0)
        layout.addWidget(self.save_path_input, 1, 1)

        # Status
        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label, 2, 0, 1, 2)

        # File Info
        self.size_label = QLabel("File Size: -")
        self.downloaded_label = QLabel("Downloaded: 0.00%")
        layout.addWidget(self.size_label, 3, 0, 1, 2)
        layout.addWidget(self.downloaded_label, 4, 0, 1, 2)

        # Speed & ETA
        self.speed_label = QLabel("Speed: -")
        self.eta_label = QLabel("Remaining Time: -")
        layout.addWidget(self.speed_label, 5, 0)
        layout.addWidget(self.eta_label, 5, 1)

        # Control Buttons
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        layout.addLayout(btn_layout, 6, 0, 1, 2)

        self.setLayout(layout)

class OptionsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # Speed Limit
        self.speed_limit = QLineEdit()
        self.speed_limit.setPlaceholderText("0 = No Limit")
        self.apply_btn = QPushButton("Apply")
        row = QHBoxLayout()
        row.addWidget(QLabel("Limit Speed to"))
        row.addWidget(self.speed_limit)
        row.addWidget(QLabel("KB/sec"))
        row.addWidget(self.apply_btn)
        layout.addRow(row)

        self.setLayout(layout)

class ConnectionsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # Thread List
        self.thread_list = QListWidget()
        layout.addWidget(self.thread_list, 50)

        # Thread Controls
        right_layout = QVBoxLayout()
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 64)
        self.threads_spin.setValue(MAX_THREADS)
        self.apply_btn = QPushButton("Apply")
        right_layout.addWidget(QLabel("Max Threads:"))
        right_layout.addWidget(self.threads_spin)
        right_layout.addWidget(self.apply_btn)
        right_layout.addStretch()
        layout.addLayout(right_layout, 50)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = None
        self.start_time = None
        self.last_bytes = 0
        self.signals = DownloadSignals()
        self.init_ui()
        self.setup_signals()

    def init_ui(self):
        self.setWindowTitle("PyDownloader")
        self.setGeometry(100, 100, 800, 500)

        # Tabs
        self.tabs = QTabWidget()
        self.download_tab = DownloadTab()
        self.options_tab = OptionsTab()
        self.connections_tab = ConnectionsTab()
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.options_tab, "Options")
        self.tabs.addTab(self.connections_tab, "Connections")

        # Progress Area
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threads_label = QLabel(f"Threads: {MAX_THREADS}")
        font = QFont()
        font.setBold(True)
        self.threads_label.setFont(font)

        # Main Layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.threads_label)
        layout.addWidget(self.progress_bar)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Timer for speed calculation
        self.timer = QTimer()
        self.timer.setInterval(1000)

    def setup_signals(self):
        # Download Tab
        self.download_tab.start_btn.clicked.connect(self.start_download)
        self.download_tab.pause_btn.clicked.connect(self.toggle_pause)
        self.signals.update_progress.connect(self.update_progress)
        self.signals.update_speed.connect(self.update_speed)
        self.signals.update_status.connect(self.update_status)
        self.signals.update_file_size.connect(self.update_file_size)
        self.signals.update_downloaded.connect(self.update_downloaded_percent)
        self.signals.update_threads.connect(self.update_thread_count)
        self.signals.thread_status.connect(self.update_thread_status)
        self.timer.timeout.connect(self.calculate_speed)

        # Options Tab
        self.options_tab.apply_btn.clicked.connect(self.apply_speed_limit)

        # Connections Tab
        self.connections_tab.apply_btn.clicked.connect(self.apply_threads)

    def start_download(self):
        url = self.download_tab.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL")
            return

        self.start_time = time.time()
        self.last_bytes = 0
        self.progress_bar.setValue(0)
        self.download_tab.pause_btn.setText("Pause")
        self.download_tab.pause_btn.setEnabled(True)
        self.signals.update_status.emit("Getting file info...")

        # Get file info
        try:
            file_size, supports_partial = get_file_info(url)
            if file_size <= 0:
                raise ValueError("Invalid file size")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.signals.update_file_size.emit(file_size)
        self.signals.update_status.emit("Downloading...")

        # Start download
        self.timer.start()
        self.downloader = threading.Thread(target=download_manager,
                                args=(url, "download.file", self.connections_tab.threads_spin.value(),
                                      self.progress_callback, self.thread_status_callback))
        self.downloader.start()

    def toggle_pause(self):
        if self.download_tab.pause_btn.text() == "Pause":
            pause_download()
            self.download_tab.pause_btn.setText("Resume")
            self.signals.update_status.emit("Paused")
        else:
            resume_download()
            self.download_tab.pause_btn.setText("Pause")
            self.signals.update_status.emit("Downloading...")

    def progress_callback(self, chunk_len):
        self.signals.update_progress.emit(chunk_len)

    def thread_status_callback(self, thread_id, status):
        self.signals.thread_status.emit(thread_id, status)

    def calculate_speed(self):
        if not self.start_time:
            return
        elapsed = time.time() - self.start_time
        current = self.progress_bar.value()
        speed = (current - self.last_bytes) / elapsed
        self.last_bytes = current
        self.signals.update_speed.emit(speed)

    def update_progress(self, increment):
        self.progress_bar.setValue(self.progress_bar.value() + increment)

    def update_speed(self, speed):
        units = ["B", "KB", "MB", "GB"]
        unit_idx = 0
        while speed > 1024 and unit_idx < 3:
            speed /= 1024
            unit_idx += 1
        self.download_tab.speed_label.setText(f"Speed: {speed:.2f} {units[unit_idx]}/s")

    def update_status(self, status):
        self.download_tab.status_label.setText(f"Status: {status}")

    def update_file_size(self, size):
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_idx = 0
        while size > 1024 and unit_idx < 4:
            size /= 1024
            unit_idx += 1
        self.download_tab.size_label.setText(f"File Size: {size:.2f} {units[unit_idx]}")

    def update_downloaded_percent(self, downloaded, total):
        percent = (downloaded / total) * 100 if total > 0 else 0
        self.download_tab.downloaded_label.setText(f"Downloaded: {percent:.2f}%")

    def update_thread_count(self, count):
        self.threads_label.setText(f"Threads: {count}")

    def update_thread_status(self, thread_id, status):
        item = self.connections_tab.thread_list.item(thread_id)
        if not item:
            self.connections_tab.thread_list.addItem(f"Thread {thread_id}: {status}")
        else:
            item.setText(f"Thread {thread_id}: {status}")

    def apply_speed_limit(self):
        # TODO: Implement speed limiting
        pass

    def apply_threads(self):
        new_threads = self.connections_tab.threads_spin.value()
        # TODO: Update thread count dynamically
        self.update_thread_count(new_threads)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()