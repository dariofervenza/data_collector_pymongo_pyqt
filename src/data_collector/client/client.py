#!/usr/bin/env python
""" Lanza la GUI del cliente,
contiene la clase de la main window.
Instancia la auth window, la tool bar
y el status bar. Tambien instancia la
main widget y los widgets de graficos/datos,
alarmas y analitics.
El widget central contiene un
stacked widget que se emplea para
cambiar entre las pantallas (alarmas, graficos, etc)
mediante los botones de la toolbar
"""
import sys
import os
import webbrowser
from pathlib import Path
from functools import partial
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QVBoxLayout


from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer

from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap

from auth import AuthWindow
from graphs import GraficosWidget
from tool_status_bar import ToolBar
from tool_status_bar import StatusBar
from alarms import AlarmasWidget
from main_widget import MainWidget
from analytics import AnalyticsWidget

from qfluentwidgets import setTheme, Theme, setThemeColor, setFont, FluentThemeColor
from qfluentwidgets import FluentWindow
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import NavigationItemPosition
from qfluentwidgets import AvatarWidget

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.1"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


BASE_DIR = os.getcwd()
IMAGES_FOLDER = os.path.join(BASE_DIR, "images")
LOGO = os.path.join(IMAGES_FOLDER, "logo.png")
AVATAR = os.path.join(IMAGES_FOLDER, "anonymous.jpg")
STYLE = Path("style/style.qss").read_text()

class MainWindow(FluentWindow):
    """ Ventana principal, sobre ella se despliegan
    el resto de widgets
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interview - client")
        #self.setGeometry(100, 100, 800, 800)
        self.setWindowIcon(QIcon(LOGO))
        self.token = None
        self.server_ip = "localhost"


        print("main widget")
        self.main_widget = MainWidget()
        print("graficos widget")

        self.graficos_widget = GraficosWidget()
        print("alarmas widget")

        self.alarmas_widget = AlarmasWidget()
        print("analytics widget")

        self.analytics_widget = AnalyticsWidget()
        print("fin analytics widget")

        self.addSubInterface(self.main_widget, FIF.HOME, 'Home')
        self.addSubInterface(self.graficos_widget, FIF.LIBRARY, 'Graficos')
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.alarmas_widget, FIF.INFO, 'Alarmas')
        self.addSubInterface(self.analytics_widget, FIF.HISTORY, 'Analytics')


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.print_focused_widget)
        self.timer.start(5000)  # 5000 milliseconds = 5 seconds

        setTheme(Theme.LIGHT)
        # setThemeColor(FluentThemeColor.DEFAULT_BLUE.color())
        # setFont(self.comboBox, 16)

    def print_focused_widget(self):
        focused_widget = QApplication.focusWidget()
        if focused_widget:
            print("Focused Widget:")
            print("  Object Name:", focused_widget.objectName())
            print("  Object Type:", type(focused_widget).__name__)
        else:
            print("No focused widget")



    def open_webbrowser(self, url):
        """ Abre mi pagina de github
        al presionar el menu de ayuda
        """
        webbrowser.open(url)


if __name__ == "__main__":
    #user_dict = {"usuario" : "paco", "contraseña" : "paco"}
    #asyncio.run(connect_to_server(user_dict))
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication([])
    app.setStyleSheet(STYLE)
    mainwindow = MainWindow()
    auth_window = AuthWindow(mainwindow)
    sys.exit(app.exec())
