from qfluentwidgets import  SubtitleLabel, setFont,PushButton
from PyQt6.QtWidgets import QFrame, QHBoxLayout
from PyQt6.QtCore import Qt
class pyquick_widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(self)
        self.hBoxLayout = QHBoxLayout(self)
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)
        self.button = PushButton("Click me", self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)
        # 必须给子界面设置全局唯一的对象名
        self.setObjectName("widget")
class setting_widget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(self)
        self.hBoxLayout = QHBoxLayout(self)
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)

        self.button = PushButton("Click me", self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)
        # 必须给子界面设置全局唯一的对象名
        self.setObjectName("Settings")