#!/usr/bin/env python
""" Widget principal, sirve a modo
de presentación, de momento no tiene
nunguna funcionalidad. Algunas ideas
podrían ser añadir algún KPI general
o incluir aqui la creacion de usuarios
"""
import os
import json
import asyncio
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QGridLayout

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from qfluentwidgets import ComboBox
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import LargeTitleLabel
from qfluentwidgets import SubtitleLabel
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ToolTipFilter
from qfluentwidgets import ToolTipPosition
from qfluentwidgets import RoundMenu
from qfluentwidgets import MenuAnimationType
from qfluentwidgets import Action
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition

from general_functions import open_webbrowser

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
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

class MainWidget(QWidget):
    """ Widget default, se es el que se muestra como
    pantalla de inicio
    """
    def __init__(self, lista_ciudades):
        super().__init__()
        logo_label = QLabel()
        logo_label_pixmap = QPixmap(LOGO)
        logo_label_pixmap = logo_label_pixmap.scaledToHeight(250)
        logo_label.setPixmap(logo_label_pixmap)

        self.token = None
        self.db_data = None
        self.server_ip = "localhost"
        self.setObjectName("MainWidget")

        titulo_app = LargeTitleLabel("Visualizador de datos")

        self.ciudad_combo_box = ComboBox(self)
        self.lista_ciudades = lista_ciudades
        for ciudad in self.lista_ciudades:
            self.ciudad_combo_box.addItem(ciudad)
        self.ciudad_combo_box.currentIndexChanged.connect(self.leer_datos_db)

        subtitulo_ver_datos = SubtitleLabel("Visualización JSON")
        self.text_edit = QTextEdit(self)
        self.text_edit.setFixedSize(800, 300)
        boton_pedir_datos = PrimaryPushButton(FIF.SAVE, "Extraer datos", self)
        boton_pedir_datos.clicked.connect(self.leer_datos_db)
        boton_pedir_datos.setToolTip("Lee los datos de la db y los muestra en formato JSON")
        boton_pedir_datos.installEventFilter(
            ToolTipFilter(boton_pedir_datos, 300, ToolTipPosition.RIGHT)
            )
        self.contextMenuEvent = self.menu_general

        layout = QGridLayout()
        layout.addWidget(
            titulo_app,
            0,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            logo_label,
            1,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            subtitulo_ver_datos,
            2,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            self.text_edit,
            3,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            self.ciudad_combo_box,
            4,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            boton_pedir_datos,
            5,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        self.setLayout(layout)
    def menu_general(self, event):
        """ Lanza un menu al hacer click derecho en la
        aplicación
        """
        menu = RoundMenu(parent=self)
        accion_cambiar_usuario = Action(FIF.UPDATE, "Cambiar usuario", shortcut="Ctrl+U")
        accion_cambiar_usuario.connect(self.cambiar_user)
        menu.addAction(accion_cambiar_usuario)
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)

        menu.addSeparator()

        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)
    def cambiar_user(self):
        """ Gestinona el cambio de usuario cuando se hace click derecho
        y se selecciona esa opción
        """
        pass

    def leer_datos_db(self):
        """ Funcion provisional, será deprecated.
        Lee los datos de la API que estén en la db y
        los muestra en un QTextEdit
        """
        ciudad = self.ciudad_combo_box.currentText()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db(ciudad))
        self.text_edit.clear()
        datos = self.db_data
        datos = datos[: 5] # añadir control para regular el numero de datos
        datos = json.dumps(datos, indent=4, sort_keys=True)
        self.text_edit.insertPlainText(datos)
    async def retrieve_data_from_db(self, ciudad: str):
        """ Funcion provisional, será deprecated.
        Gestiona la conexion asincrona con la
        db
        """
        uri = f"ws://{self.server_ip}:8765"
        query = {"location.name" : ciudad}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)
        max_size = 50 * 1024 * 1024
        async with websockets.connect(uri, max_size=max_size) as websocket:
            try:
                await websocket.send(request)
                response = await websocket.recv()
                response = json.loads(response)
                if response["autenticado"]:
                    self.db_data = response["data"]
                else:
                    InfoBar.error(
                        title='Error',
                        content="Token expirado, vuelva a iniciar sesión",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        # position='Custom',   # NOTE: use custom info bar manager
                        duration=1500,
                        parent=self
                    )
            except TimeoutError:
                InfoBar.error(
                    title='Error',
                    content="Servidor ocupado",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    # position='Custom',   # NOTE: use custom info bar manager
                    duration=1500,
                    parent=self
                    )
            except websockets.exceptions.ConnectionClosedError:
                InfoBar.error(
                    title='Error',
                    content="Conexión con el servidor cortada",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    # position='Custom',   # NOTE: use custom info bar manager
                    duration=1500,
                    parent=self
                    )
            finally:
                await websocket.close()
