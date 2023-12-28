#!/usr/bin/env python
""" Auth
"""
import os
import json
import asyncio
import socket
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox

from PyQt5.QtGui import QIcon

from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QThreadPool
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot


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
        self.token = None
        self.server_ip = "localhost"
        self.thread_response = None
        self.worker = None
        self.mainwindow = mainwindow
        self.setWindowTitle("Inicio de sesion")
        self.setGeometry(400, 400 , 350, 200)
        self.setWindowIcon(QIcon(LOGO))

        self.stacked = QStackedWidget()
        self.pagina_introduccion_server = QWidget()
        self.pagina_usuario = QWidget()
        self.stacked.addWidget(self.pagina_introduccion_server)
        self.stacked.addWidget(self.pagina_usuario)

        self.stacked.setCurrentIndex(0)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked)
        self.setLayout(main_layout)


        introduce_server_label = QLabel("Introduce la dirección del servidor:")
        introduce_server_label.setContentsMargins(10, 15, 10, 10)
        self.introduce_server_line_edit = QLineEdit(
            placeholderText="localhost",
            clearButtonEnabled=True
            )
        self.introduce_server_line_edit.setContentsMargins(10, 15, 10, 25)
        self.introduce_server_line_edit.returnPressed.connect(self.cambiar_a_user_page)

        boton_aceptar_server = QPushButton("Aceptar")
        boton_aceptar_server.setContentsMargins(10, 25, 10, 10)
        boton_aceptar_server.clicked.connect(self.cambiar_a_user_page)

        layout_pagina_introduccion_server = QVBoxLayout()
        layout_pagina_introduccion_server.addWidget(introduce_server_label)
        layout_pagina_introduccion_server.addWidget(self.introduce_server_line_edit)
        layout_pagina_introduccion_server.addWidget(boton_aceptar_server)
        layout_pagina_introduccion_server.addStretch(1)
        self.pagina_introduccion_server.setLayout(layout_pagina_introduccion_server)
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
        self.boton_aceptar = QPushButton("Aceptar")
        self.boton_aceptar.clicked.connect(self.authenticate)
        self.pass_line_edit.returnPressed.connect(self.boton_aceptar.click)

        self.boton_regresar = QPushButton("Regresar")
        self.boton_regresar.clicked.connect(self.cambiar_a_servidor_page)

        layout_pagina_usuario = QVBoxLayout()
        layout_pagina_usuario.addWidget(user_label, stretch=1)
        layout_pagina_usuario.addWidget(self.user_line_edit, stretch=1)
        layout_pagina_usuario.addWidget(pass_label, stretch=1)
        layout_pagina_usuario.addWidget(self.pass_line_edit, stretch=1)
        layout_pagina_usuario.addWidget(self.boton_aceptar, stretch=1)
        layout_pagina_usuario.addWidget(self.boton_regresar, stretch=1)
        self.pagina_usuario.setLayout(layout_pagina_usuario)
        self.show()
    def cambiar_a_user_page(self):
        """ Una vez introducida la dirección del server,
        esta funcion cambia a la vista de introducción
        de user + password.
        Además, envia la dirección del server a los demás
        widgets
        """
        self.stacked.setCurrentIndex(1)
        self.server_ip = self.introduce_server_line_edit.text()
        self.mainwindow.server_ip = self.server_ip
        self.mainwindow.main_widget.server_ip = self.server_ip
        self.mainwindow.graficos_widget.server_ip = self.server_ip
        self.mainwindow.alarmas_widget.server_ip = self.server_ip
        self.mainwindow.analytics_widget.server_ip = self.server_ip

    def cambiar_a_servidor_page(self):
        """ Funcion para regresar al widget de introducción
        de la dirección del servidor por si el usuario
        se equivoca y ya le da ha dado a continuar
        a la vista de introducción de username + password
        """
        self.stacked.setCurrentIndex(0)
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
        self.boton_aceptar.setEnabled(False)
        self.boton_regresar.setEnabled(False)
        username = self.user_line_edit.text()
        password = self.pass_line_edit.text()
        self.worker = AuthWorker(
            self.server_ip,
            username,
            password
            )
        self.worker.signals.signal.connect(self.receive_thread_response)
        pool = QThreadPool.globalInstance()
        pool.start(self.worker)
    def receive_thread_response(self, thread_response):
        """ Metodo lanzado por el thread que se encarga de
        la autenticación con el servidor,
        recibe la respuesta y envia  mensajes de error si
        se producen. En caso contrario, procede a el lanzamiento
        de la app
        """
        self.thread_response = thread_response
        self.token = self.worker.token
        if self.thread_response == "Dirección del servidor inválida":
            QMessageBox.critical(
                self,
                "Error",
                "Dirección del servidor inválida"
                )
        elif self.thread_response == "Comprueba usuario y contraseña":
            QMessageBox.critical(
                self,
                "Error",
                "Comprueba usuario y contraseña"
                )
        elif self.thread_response == "No es posible realizar la conexión con el servidor":
            QMessageBox.critical(
                self,
                "Error",
                "No es posible realizar la conexión con el servidor"
                )
        elif self.token \
        and self.thread_response == "Autenticado":
            self.mainwindow.token = self.token
            self.mainwindow.main_widget.token = self.token
            self.mainwindow.graficos_widget.token = self.token
            self.mainwindow.alarmas_widget.token = self.token
            self.mainwindow.analytics_widget.token = self.token
            self.mainwindow.alarmas_widget.return_avisos_for_my_user()
            self.mainwindow.alarmas_widget.obtener_alarmas_creadas()
            self.close()
            print("close")
        self.boton_aceptar.setEnabled(True)
        self.boton_regresar.setEnabled(True)
class Signals(QObject):
    """ Crea una señal para enviar
    la respuesta al proceso de autenticación que
    se realiza en un Qthread, es instanciada
    en la clase que hereda de QRunnable
    """
    signal = Signal(str)

class AuthWorker(QRunnable):
    """ Se encarga de gestionar la comunicación
    con el servidor para el proceso de autenticación.
    Luego envia una respuesta con una signal para
    identificar si ha habido un error o se puede
    lanzar la mainwindow de la GUI.
    """
    def __init__(self, server_ip, username, password):
        super().__init__()
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.signals = Signals()
        self.response = None
        self.token = None
    @Slot()
    def run(self):
        response = asyncio.run(
            self.obtain_token(self.username, self.password)
            )
        self.signals.signal.emit(response)
    async def obtain_token(self, username: str, password: str) -> None:
        """ Realiza la conexion con websockets a el servidor
        """

        uri = f"ws://{self.server_ip}:8765"
        user_dict = {"usuario" : username, "contraseña" : password}
        request = {"tipo_request" : "login", "value" : user_dict}
        request = json.dumps(request)
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(request)
                response = await websocket.recv()
                response = json.loads(response)
                if response.get("autenticado"):
                    self.token = response.get("token")
                    response = "Autenticado"
                else:
                    self.token = None
                    response = "Comprueba usuario y contraseña"
                await websocket.close()
        except TimeoutError:
            response = "No es posible realizar la conexión con el servidor"
        except websockets.exceptions.InvalidURI:
            response = "Dirección del servidor inválida"
        except socket.gaierror:
            response = "Dirección del servidor inválida"
        return response
