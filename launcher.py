from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont
from qfluentwidgets import FluentIcon as FIF
from la_souc import launch_in
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import sys
import os
from settings.save import SettingsManager
class Window(FluentWindow):
    """ 主界面 """
    def __init__(self):
        super().__init__()

        # 初始化设置管理器
        self.settings_manager = SettingsManager(os.path.dirname(os.path.abspath(__file__)))
        self.settings_manager.load_settings()

        # 创建子界面，实际使用时将 Widget 换成自己的子界面
        self.settingInterface = launch_in.pyquick_widget(self)
        self.albumInterface = launch_in.setting_widget(self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.albumInterface, FIF.ALBUM, 'Albums', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
    def initWindow(self):
        self.resize(900, 700)
        self.setWindowTitle('PyQt-Fluent-Widgets')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
