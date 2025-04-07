import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from qfluentwidgets import *
import datetime

class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon("pyquick.ico"))
        self.initUI()

    def initUI(self):
        view=QWidget()
        scrollArea = SingleDirectionScrollArea(orient=Qt.Orientation.Vertical)
        scrollArea.resize(200, 400)
        with open("gpl3.txt", "r") as f:
            self.gpl=f.read()
        self.textEdit = TextEdit()
        self.textEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout()
        self.remin = (datetime.datetime(2025, 8, 13) - datetime.datetime.now()).days
        self.image = ImageLabel("magic.png")
        self.image.setBorderRadius(8, 8, 8, 8)
        self.link=HyperlinkLabel(QUrl('https://github.com/pyquick/pyquick/'), 'This Project')
        self.pyquick=SubtitleLabel("PyQuick")
        self.version=StrongBodyLabel("Version: Dev (App build:2020) ")
        self.ex=StrongBodyLabel(f"Expiration time: 2025.8.13 ({self.remin} days)")
        self.gp=BodyLabel("GNU GENERAL PUBLIC LICENSE:\n")
        self.pq=CaptionLabel("®Pyquick™ 2025. All rights reserved.")
        self.ok=PushButton("OK")
        self.ok.setFixedWidth(120)
        self.ok.clicked.connect(self.close)
        if self.remin<=14:
            self.warnings = BodyLabel("⚠️ This Version Will Expire SOON! Please Upgrade this quickly.")
            self.warnings.setTextColor(QColor(255,0,0))
        self.dev1=BodyLabel("⚠️The Dev version is not stable.")
        self.dev2=BodyLabel("If there is any problem, please post the problem immediately to the issues.")
        self.dev1.setTextColor(QColor(255,0,0))
        self.dev2.setTextColor(QColor(255,0,0))
        self.textEdit.setPlainText(self.gpl)
        self.textEdit.setReadOnly(True)
        self.textEdit.setFontPointSize(300)
        layout.addWidget(self.image,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.link,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pyquick,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ex,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gp,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.textEdit)
        layout.addWidget(self.dev1,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dev2,0,Qt.AlignmentFlag.AlignCenter)
        if self.remin<=14:
            layout.addWidget(self.warnings,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pq)
        layout.addWidget(self.ok,0,Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
        scrollArea.setWidget(view)




def show():
    app = QApplication(sys.argv)
    window = AboutWindow()
    window.show()
    sys.exit(app.exec())