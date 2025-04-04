import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from qfluentwidgets import *


class App(QWidget):
    def __init__(self, url, save_path, nums_threads):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("About")
        # 主布局：垂直
        main_layout = QVBoxLayout(self)

        # 顶部按钮（水平靠右）
        top_layout = QHBoxLayout()
        # top_layout.addStretch()

        top_layout.addWidget(button)

        # 底部状态栏

        # 组装主布局
        main_layout.addLayout(top_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())