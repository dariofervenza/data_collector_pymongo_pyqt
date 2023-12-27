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
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGridLayout

from PyQt5.QtCore import Qt

from PyQt5.QtGui import QPixmap


__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.1.3"
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
    def __init__(self):
        super().__init__()
        logo_label = QLabel()
        logo_label_pixmap = QPixmap(LOGO)
        logo_label_pixmap = logo_label_pixmap.scaledToHeight(250)
        logo_label.setPixmap(logo_label_pixmap)

        self.token = None
        self.db_data = None

        self.ciudad_combo_box = QComboBox(self)
        lists_ciudades = ["Vigo", "Lugo", "Madrid"]
        for ciudad in lists_ciudades:
            self.ciudad_combo_box.addItem(ciudad)

        self.text_edit = QTextEdit(self)
        self.text_edit.setFixedSize(800, 300)
        boton_pedir_datos = QPushButton("Extraer datos")
        boton_pedir_datos.clicked.connect(self.leer_datos_db)

        layout = QGridLayout()
        layout.addWidget(
            logo_label,
            0,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            self.text_edit,
            1,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            self.ciudad_combo_box,
            2,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        layout.addWidget(
            boton_pedir_datos,
            3,
            0,
            Qt.AlignmentFlag.AlignCenter
            )
        self.setLayout(layout)
    def leer_datos_db(self):
        """ Funcion provisional, será deprecated.
        Lee los datos de la API que estén en la db y
        los muestra en un QTextEdit
        """
        ciudad = self.ciudad_combo_box.currentText()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db(ciudad))
        self.text_edit.clear()
        self.text_edit.insertPlainText(self.db_data)
    async def retrieve_data_from_db(self, ciudad: str):
        """ Funcion provisional, será deprecated.
        Gestiona la conexion asincrona con la
        db
        """
        uri = "ws://localhost:8765"
        query = {"location.name" : ciudad}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)
        async with websockets.connect(uri) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            self.db_data = response
            await websocket.close()
