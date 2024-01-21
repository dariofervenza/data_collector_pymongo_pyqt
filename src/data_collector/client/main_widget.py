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
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGridLayout

from PyQt5.QtCore import Qt

from PyQt5.QtGui import QPixmap

from qfluentwidgets import ComboBox
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import PushButton
from qfluentwidgets import LargeTitleLabel
from qfluentwidgets import SubtitleLabel
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ToolTipFilter
from qfluentwidgets import ToolTipPosition
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
HOME = os.path.join(IMAGES_FOLDER, "home.png")
GRAPH = os.path.join(IMAGES_FOLDER, "graph.png")
ALERTS = os.path.join(IMAGES_FOLDER, "alerts.png")
ANALYTICS = os.path.join(IMAGES_FOLDER, "analytics.png")
STYLE = Path("style/style.qss").read_text()


class MainWidget(QFrame):
    """ Widget default, se es el que se muestra como
    pantalla de inicio
    """
    def __init__(self):
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
        lists_ciudades = ["Vigo", "Lugo", "Madrid"]
        for ciudad in lists_ciudades:
            self.ciudad_combo_box.addItem(ciudad)
        self.ciudad_combo_box.currentIndexChanged.connect(self.leer_datos_db)

        subtitulo_ver_datos = SubtitleLabel("Visualización JSON")
        self.text_edit = QTextEdit(self)
        self.text_edit.setFixedSize(800, 300)
        boton_pedir_datos = PrimaryPushButton(FIF.SAVE, "Extraer datos", self)
        boton_pedir_datos.clicked.connect(self.leer_datos_db)
        boton_pedir_datos.setToolTip("Lee los datos de la db y los muestra en formato JSON")
        boton_pedir_datos.installEventFilter(ToolTipFilter(boton_pedir_datos, 300, ToolTipPosition.RIGHT))

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
        self.leer_datos_db()
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
        datos = json.loads(datos)
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
        async with websockets.connect(uri) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            self.db_data = response
            await websocket.close()
