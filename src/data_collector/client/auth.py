#!/usr/bin/env python
""" Auth
"""
import os
import json
import asyncio
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout

from PyQt5.QtGui import QIcon

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


class AuthWindow(QWidget):
    """ Primera ventana que se abre
    pide user y password, si se cierra,
    no se abre la app. Hasta que se ponga un user
    correcto no se lanza la app
    Recibe un token de autenticacion del server
    al iniciar sesion
    """
    def __init__(self, mainwindow):
        super().__init__()
        self.mainwindow = mainwindow
        self.setWindowTitle("Inicio de sesion")
        self.setGeometry(400, 400 , 350, 200)
        self.setWindowIcon(QIcon(LOGO))

        self.token = None
        usuarios_completer = QCompleter([
            "paco",
            "manolo",
            "user",
            ])
        user_label = QLabel("Usuario")
        self.user_line_edit = QLineEdit(
            self,
            placeholderText="Introduce usuario",
            clearButtonEnabled=True
            )
        self.user_line_edit.setCompleter(usuarios_completer)

        pass_label = QLabel("Contraseña")
        self.pass_line_edit = QLineEdit(self,
            placeholderText="Introduce contraseña",
            clearButtonEnabled=True,
            echoMode=QLineEdit.EchoMode.Password
            )


        boton_aceptar = QPushButton("Aceptar")
        boton_aceptar.clicked.connect(self.authenticate)
        self.pass_line_edit.returnPressed.connect(boton_aceptar.click)


        layout = QVBoxLayout()
        layout.addWidget(user_label, stretch=1)
        layout.addWidget(self.user_line_edit, stretch=1)
        layout.addWidget(pass_label, stretch=1)
        layout.addWidget(self.pass_line_edit, stretch=1)
        layout.addWidget(boton_aceptar, stretch=1)

        self.setLayout(layout)
        self.show()

    def closeEvent(self, event):
        """ Cuando se cierra la authwindow,
        si tenemos un token, abre la mainwindow
        """
        if self.token:
            self.mainwindow.show()
            self.mainwindow.showMaximized()
        event.accept()
    def authenticate(self):
        """ Lanza el proceso de inicio sesion
        y lanza la async function para conectarse
        con el server
        """
        username = self.user_line_edit.text()
        password = self.pass_line_edit.text()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.obtain_token(username, password))
        self.mainwindow.token = self.token
        self.mainwindow.main_widget.token = self.token
        self.mainwindow.graficos_widget.token = self.token
        self.mainwindow.alarmas_widget.token = self.token
        self.mainwindow.analytics_widget.token = self.token
        self.mainwindow.alarmas_widget.return_avisos_for_my_user()
        self.mainwindow.alarmas_widget.obtener_alarmas_creadas()
        print(self.token)
        if self.token:
            self.close()
            print("close")
    async def obtain_token(self, username: str, password: str) -> None:
        """ Realiza la ocnexion con websockets a el servidor
        """
        print("obtain")
        uri = "ws://localhost:8765"
        user_dict = {"usuario" : username, "contraseña" : password}
        request = {"tipo_request" : "login", "value" : user_dict}
        request = json.dumps(request)
        async with websockets.connect(uri) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            response = json.loads(response)
            if response.get("autenticado"):
                self.token = response.get("token")
            else:
                self.token = None
            await websocket.close()
