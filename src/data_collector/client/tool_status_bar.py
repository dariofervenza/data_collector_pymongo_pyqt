#!/usr/bin/env python
""" Tool bar and status bar classes
"""
import os
from pathlib import Path
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import pyqtSignal as Signal

from PyQt5.QtGui import QIcon

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.1.5"
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

class ToolBar(QToolBar):
    """ Define la toolbar para cambiar entre los
    diferentes widgets (mostrar graficos, alarmas, analytics)
    """
    mostrar_pantalla_de_inicio_signal = Signal()
    mostrar_graficos_signal = Signal(int)
    mostrar_alarmas_signal = Signal(int)
    mostrar_analytics_signal = Signal(int)
    def __init__(self):
        super().__init__()
        mostrar_inicio_action = QAction(QIcon(HOME), "Volver a inicio", self)
        mostrar_inicio_action.triggered.connect(self.mostrar_pantalla_inicio)
        self.addAction(mostrar_inicio_action)
        mostrar_graficos_action = QAction(QIcon(GRAPH), "Mostrar graficos", self)
        mostrar_graficos_action.triggered.connect(self.mostrar_graficos)
        self.addAction(mostrar_graficos_action)
        mostrar_alarmas_action = QAction(QIcon(ALERTS), "Mostrar alarmas", self)
        mostrar_alarmas_action.triggered.connect(self.mostrar_alarmas)
        self.addAction(mostrar_alarmas_action)
        mostrar_analytics_action = QAction(QIcon(ANALYTICS), "Mostrar analytics", self)
        mostrar_analytics_action.triggered.connect(self.mostrar_analytics)
        self.addAction(mostrar_analytics_action)
    def mostrar_pantalla_inicio(self):
        """ Emite una señal cada vez que se hace
        click en un boton de la tool bar.
        Esta señal es mostrada en la status bar
        """
        self.mostrar_pantalla_de_inicio_signal.emit()
    def mostrar_graficos(self):
        """ Emite señal al pulsar el boton
        de mostrar graficos
        """
        self.mostrar_graficos_signal.emit(1)

    def mostrar_alarmas(self):
        """ Emite señal al pulsar el boton
        de mostrar alarmas
        """
        self.mostrar_alarmas_signal.emit(1)
    def mostrar_analytics(self):
        """ Emite señal al pulsar el boton
        de mostrar alarmas
        """
        self.mostrar_analytics_signal.emit(1)
class StatusBar(QStatusBar):
    """ Crea la status bar donde se muestra info
    sobre las acciones realizadas en la GUI
    e info general sobre la app (proximamente)
    """
    def mostrar_graficos(self):
        """ Recibe la señal de la clase QToolBr e indica
        que se esta visualizando el widget de graficos
        """
        self.showMessage("Visualizando graficos", 2500)
    def mostrar_alarmas(self):
        """ Recibe la señal de la clase QToolBr e indica
        que se esta visualizando el widget de alarmas
        """
        self.showMessage("Visualizando alarmas", 2500)
    def mostrar_analytics(self):
        """ Recibe la señal de la clase QToolBr e indica
        que se esta visualizando el widget de analytics
        """
        self.showMessage("Visualizando analytics")
    def anadir_alarma(self, mensaje):
        """ Recibe la señal cuando se añade una alarma
        y lo muestra en la status bar
        """
        self.showMessage(mensaje, 5000)
