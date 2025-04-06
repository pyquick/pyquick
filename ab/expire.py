import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from qfluentwidgets import *
import datetime
#0x00000001 表示pyquick没有通过launcher启动(2108)
#0x0000000A 表示pyquick无法连接至Internet（2025）
#0x0000001A 表示pyquick时间超时
#0x0000002A/0x0007000B 表示系统不符合要求
#0x0F00600B--0x00000600 pyquick运行时错误（dev有任何问题都会报错）
#那个info.png是pyquick重大通知用的，如更新
# 在PyQt窗口关闭时强制释放资源

class AboutWindow(QWidget):
    def __init__(self,code,mode,infomation):
        super().__init__()
        self.setWindowTitle("ATTENTION")
        self.setWindowIcon(QIcon("pyquick.ico"))
        self.error_code=code
        self.ico=mode
        self.info=infomation
        self.initUI(self.error_code,self.ico,self.info)

    def initUI(self,error_code,ico,info):


        self.remin = (datetime.datetime(2025, 8, 13) - datetime.datetime.now()).days
        if ico=="error" or ico=="err":
            self.image = ImageLabel("error.png")
            self.la=TitleLabel("Pyquick Error")
            self.error=StrongBodyLabel(f"STOP_CODE: {error_code}")
        elif ico=="warning" or ico=="warn":
            self.image = ImageLabel("warning.png")
            self.la=TitleLabel("Warning")
            self.error=StrongBodyLabel(f"WARN_CODE: {error_code}")
        elif ico=="info":
            self.image = ImageLabel("info.png")
            self.la=TitleLabel("Information")
            #self.error=StrongBodyLabel(f"INFO_CODE: {error_code}")
        self.image.scaledToHeight(100)
        self.image.setBorderRadius(8, 8, 8, 8)

        self.inla=CaptionLabel("Information:")
        self.infoe=TextEdit(self)
        self.infoe.setPlainText(info)
        self.infoe.setFixedWidth(400)
        self.infoe.setFixedHeight(100)
        self.infoe.setReadOnly(True)

        self.layout = QVBoxLayout()

        self.lalay=QVBoxLayout()
        self.lalay.addWidget(self.la)
        if ico!="info":
            self.lalay.addWidget(self.error)
        self.lalay.addStretch(1)

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.image, 0, Qt.AlignmentFlag.AlignCenter)
        self.hlayout.addLayout(self.lalay)
        self.hlayout.addStretch(1)

        self.ok=PushButton("OK")
        self.ok.setFixedWidth(120)
        self.ok.clicked.connect(lambda : sys.exit(error_code))

        self.layout.addLayout(self.hlayout)
        self.layout.addWidget(self.inla)
        self.layout.addWidget(self.infoe)
        self.layout.addWidget(self.ok, 0, Qt.AlignmentFlag.AlignRight)
        self.layout.addStretch(1)
        self.setLayout(self.layout)





def show(code,mode,info):
    app=QApplication(sys.argv)
    window = AboutWindow(code=code,mode=mode,infomation=info)
    window.show()
    sys.exit(app.exec())