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

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.0"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


BASE_DIR = os.getcwd()
IMAGES_FOLDER = os.path.join(BASE_DIR, "images")
LOGO = os.path.join(IMAGES_FOLDER, "logo.png")
HOME = os.path.join(IMAGES_FOLDER, "home.png")
GRAPH = os.path.join(IMAGES_FOLDER, "graph.png")
ALERTS = os.path.join(IMAGES_FOLDER, "alerts.png")
ANALYTICS = os.path.join(IMAGES_FOLDER, "analytics.png")
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

        """menu_bar = self.menuBar()
        archivo_menu = menu_bar.addMenu("Archivo")
        ayuda_menu = menu_bar.addMenu("&Ayuda")

        archivo_menu.addAction("Cerrar", self.close)
        url = "https://github.com/dariofervenza"
        funcion_parcial_github = partial(self.open_webbrowser, url)
        abrir_github_action = QAction("Abrir github", self)
        abrir_github_action.triggered.connect(funcion_parcial_github)
        ayuda_menu.addAction(abrir_github_action)"""

        """print("toolb bar")
        tool_bar = ToolBar()
        tool_bar.setStyleSheet(STYLE)
        self.addToolBar(tool_bar)"""

        """status_bar = StatusBar()
        self.setStatusBar(status_bar)"""


        """print("central widget")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)"""


        #self.stacket_widget = QStackedWidget(self, objectName='homeInterface')


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

        """self.stacket_widget.addWidget(self.main_widget)
        self.stacket_widget.addWidget(self.graficos_widget)
        self.stacket_widget.addWidget(self.alarmas_widget)
        self.stacket_widget.addWidget(self.analytics_widget)
        self.stacket_widget.setCurrentIndex(0)"""

        """layout = QVBoxLayout()
        layout.addWidget(self.stacket_widget, stretch=1)
        self.central_widget.setLayout(layout)"""

        """tool_bar.mostrar_pantalla_de_inicio_signal.connect(
            self.return_to_home
            )
        tool_bar.mostrar_graficos_signal.connect(status_bar.mostrar_graficos)
        tool_bar.mostrar_graficos_signal.connect(self.change_to_graficos_widget)
        tool_bar.mostrar_alarmas_signal.connect(status_bar.mostrar_alarmas)
        tool_bar.mostrar_alarmas_signal.connect(self.change_to_alarmas_widget)
        tool_bar.mostrar_analytics_signal.connect(status_bar.mostrar_analytics)
        tool_bar.mostrar_analytics_signal.connect(self.change_to_analytics_widget)
        self.alarmas_widget.alarma_anadida_signal.connect(status_bar.anadir_alarma)"""

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
    def return_to_home(self):
        """ Cambia el stacked widget a
        el main widget
        """
        self.stacket_widget.setCurrentIndex(0)
    def change_to_graficos_widget(self):
        """ Hace switch a el widget de mostrar
        graficos cuando se pulsa el boton de los graficos
        en la toolbar. Esta toolbar envia señal para
        activar esta funcion
        """
        self.stacket_widget.setCurrentIndex(1)
    def change_to_alarmas_widget(self):
        """ Cambia el stacked widget a
        el alarmas widget
        """
        self.stacket_widget.setCurrentIndex(2)
    def change_to_analytics_widget(self):
        """ Cambia el stacked widget a
        el analytics widget
        """
        self.stacket_widget.setCurrentIndex(3)

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
