#!/usr/bin/env python
""" Contiene la clase que define
el widget de visualización de datos,
ya sea en forma de graficos o en una
QTable
"""
import os
import json
import asyncio
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

from PyQt5.QtCore import Qt

import plotly.graph_objs as go
import pandas as pd

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

class GraficosWidget(QWidget):
    """ Crea el widget de graficos
    En el se muestran los datos de la API usando
    un chart de plotly y una Qtable
    """
    def __init__(self):
        super().__init__()
        self.token = None
        self.db_data = None
        self.server_ip = "localhost"

        self.df_actual = pd.DataFrame()
        self.fig = go.Figure()

        tab_maestra = QTabWidget()
        tab_graficos_container = QWidget()
        tab_maestra.addTab(tab_graficos_container, "Graficos")

        tab_datos_container = QWidget()
        tab_maestra.addTab(tab_datos_container, "Datos")

        layout_maestro = QVBoxLayout()

        self.grupo_temperatura = QGroupBox("Temperaturas")
        self.plotly_fig_temp = QWebEngineView(self)
        self.plotly_fig_temp.setFixedHeight(500)
        layout_temperatura = QVBoxLayout()
        layout_temperatura.addWidget(self.plotly_fig_temp, 1)
        self.grupo_temperatura.setLayout(layout_temperatura)


        self.grupo_humedad = QGroupBox("Humedad")
        self.plotly_fig_humedad = QWebEngineView(self)
        self.plotly_fig_humedad.setFixedHeight(500)
        layout_humedad = QVBoxLayout()
        layout_humedad.addWidget(self.plotly_fig_humedad)
        self.grupo_humedad.setLayout(layout_humedad)

        self.grupo_presion = QGroupBox("Presion")
        self.plotly_fig_presion = QWebEngineView(self)
        self.plotly_fig_presion.setFixedHeight(500)
        layout_presion = QVBoxLayout()
        layout_presion.addWidget(self.plotly_fig_presion)
        self.grupo_presion.setLayout(layout_presion)

        self.fig_temp = go.Figure()
        self.fig_humedad = go.Figure()
        self.fig_presion = go.Figure()

        self.label_seleccion_ciudad = QLabel("Selecciona la ciudad")

        self.ciudad_combo_box = QComboBox()
        lists_ciudades = ["Vigo", "Lugo", "Madrid"]
        for ciudad in lists_ciudades:
            self.ciudad_combo_box.addItem(ciudad)
        self.ciudad_combo_box.currentIndexChanged.connect(self.read_data_from_db)

        self.leer_datos_db_button = QPushButton("Recargar datos")
        self.leer_datos_db_button.clicked.connect(
            self.read_data_from_db
            )
        layout_tab_graficos = QGridLayout()

        layout_tab_graficos.addWidget(
            self.grupo_temperatura,
            0,
            0,
            1,
            1,
            Qt.AlignmentFlag.AlignTop
            )
        layout_tab_graficos.addWidget(
            self.grupo_humedad,
            0,
            1,

            )
        layout_tab_graficos.addWidget(
            self.grupo_presion,
            0,
            2,

            )
        layout_tab_graficos.addWidget(
            self.label_seleccion_ciudad,
            1,
            0,
            1,
            3,
            )
        layout_tab_graficos.addWidget(
            self.ciudad_combo_box,
            2,
            0,
            1,
            3,
            )
        layout_tab_graficos.addWidget(
            self.leer_datos_db_button,
            3,
            0,
            1,
            3,
            )
        layout_tab_graficos.setContentsMargins(10, 30, 10, 10)
        layout_tab_graficos.setRowStretch(4, 1)
        self.tabla_datos = QTableWidget(0, 5)
        encabezado = ["Ciudad", "Fecha", "Temperatura", "Humedad", "Presión"]
        self.tabla_datos.setColumnWidth(1, 150)
        self.tabla_datos.setHorizontalHeaderLabels(encabezado)
        self.boton_actualizar_datos = QPushButton("Recargar datos")
        self.boton_actualizar_datos.clicked.connect(self.add_lines_to_data_table)

        layout_ver_datos = QGridLayout()
        layout_ver_datos.addWidget(self.tabla_datos)
        layout_ver_datos.addWidget(self.boton_actualizar_datos)
        tab_datos_container.setLayout(layout_ver_datos)

        tab_graficos_container.setLayout(layout_tab_graficos)
        layout_maestro.addWidget(tab_maestra)
        self.setLayout(layout_maestro)
        self.read_data_from_db()
        self.add_lines_to_data_table()
    def add_lines_to_data_table(self):
        """ Función encargada de solicitar los
        datos de la API y mostralos en la QTable
        """
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        tupla_ciudades = ("Vigo", "Lugo", "Madrid")
        df_maestro = pd.DataFrame()
        for ciudad in tupla_ciudades:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.retrieve_data_from_db(ciudad))
            self.create_df_from_data()
            df = self.df_actual
            df["ciudad"] = ciudad
            df_maestro = pd.concat([df_maestro, df])
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        for _, row in df_maestro.iterrows():
            lineas_actuales = self.tabla_datos.rowCount()
            self.tabla_datos.setRowCount(lineas_actuales + 1)
            ciudad = row["ciudad"]
            fecha = row["fecha"]
            fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
            temperatura = str(row["temperatura"])
            humedad = str(row["humedad"])
            presion = str(row["presion"])
            tupla_datos = (ciudad, fecha, temperatura, humedad, presion)
            for i, el in enumerate(tupla_datos):
                element = QTableWidgetItem(el)
                self.tabla_datos.setItem(lineas_actuales, i, element)
        self.boton_actualizar_datos.setEnabled(True)
    def read_data_from_db(self):
        """ Llama a la funcion encargada de
        obtener los datos de la db, luego a la
        que genera un DataFrame de pandas y
        por ultimo a la funcion de generar la plotly fig
        """
        ciudad = self.obtain_temperatures()
        self.create_df_from_data()
        self.create_plotly_fig(ciudad, valor="Temperatura", variable=self.plotly_fig_temp)
        self.create_plotly_fig(ciudad, valor="Humedad", variable=self.plotly_fig_humedad)
        self.create_plotly_fig(ciudad, valor="Presion", variable=self.plotly_fig_presion)
    def obtain_temperatures(self):
        """ Lee la ciudad seleccionada en la combobox
        de la tab de visualizar graficos
        y obtiene los datos de la db asociados a esa ciudad
        """
        ciudad = self.ciudad_combo_box.currentText()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db(ciudad))
        return ciudad
    async def retrieve_data_from_db(self, ciudad: str):
        """ Realiza la solicitud de datos al servidor
        utilizando websockets
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
    def create_df_from_data(self):
        """ Crea un DataFrame de pandas con los datos
        obtenidos en la funcion read_data_from_db
        Las columnas seleccionadas son la temperatura,
        la presion y la humedad.
        """
        lista_fechas = []
        lista_temperaturas = []
        lista_humedades = []
        lista_presiones = []
        datos = json.loads(self.db_data)
        for element in datos:
            fecha = element["location"]["localtime"]
            temperatura = element["current"]["temperature"]
            humedad = element["current"]["humidity"]
            presion = element["current"]["pressure"]
            lista_fechas.append(fecha)
            lista_temperaturas.append(temperatura)
            lista_humedades.append(humedad)
            lista_presiones.append(presion)
        dict_data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones
            }
        df = pd.DataFrame(dict_data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        self.df_actual = df
    def create_plotly_fig(self, ciudad: str, valor: str, variable: QWebEngineView):
        """ Crea una figura de plotly con el DataFrame
        de pandas generado con el metodo create_df_from_data
        y devuelve asigna su html a un widget QWebView, el
        cual es recibido como parametro
        """
        datos = self.df_actual
        if valor == "Temperatura":
            valor2 = "temperatura"
        elif valor == "Humedad":
            valor2 = "humedad"
        elif valor == "Presion":
            valor2 = "presion"
        self.fig = go.Figure()
        self.fig.add_trace(go.Scatter(
            x=datos["fecha"],
            y=datos[valor2],
            mode="lines",
            name="Temperaturas"
            ))
        self.fig.update_layout(
            title=valor + " en: " + ciudad
            )
        html = self.fig.to_html(include_plotlyjs='cdn')
        variable.setHtml(html)
        print("ok")
