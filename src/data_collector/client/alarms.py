#!/usr/bin/env python
""" Contiene el widget de alarmas y sus metodos
Aqui se crean alarmas y se visualizan las notificaciones
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizePolicy

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as Signal


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


class AlarmasWidget(QWidget):
    """ Define el widget de alarmas
    Se compone de dos QTabs, una para añadir,
    visualizar y eliminar alarmas y otra
    para visualizar los avisos en forma de
    QTree
    """
    alarma_anadida_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.token = None
        self.my_alarms = None
        """ Crea una tab con dos valores
        uno para añadir/eliminar/ver a alarmas, cada uno un grupo
        y otra para ver los avisos generados
        """
        self.tab_alarmas_avisos = QTabWidget()
        self.tab_alarmas = QWidget()
        self.tab_avisos = QWidget()
        self.grupo_introduccion_alarma = QGroupBox("Añadir alarma")
        self.titulo_anadir_alarma = QLabel("Tipo de alarma")
        self.tipo_alarma_combo_box = QComboBox()
        lista_tipos_alarma = [
            "Límite superior",
            "Límite inferior",
            "Incremento absoluto",
            "Incremento relativo",
            "Outlier",
            "Desviación absoluta a la previsión",
            "Desviación relativa a la previsión",
            ]
        for element in lista_tipos_alarma:
            self.tipo_alarma_combo_box.addItem(element)
        self.titulo_tipo_dato_alarma = QLabel("Tipo de dato")
        self.tipo_de_dato_combo_box = QComboBox()
        lista_datos = [
            "temperature",
            "wind_speed",
            "pressure",
            "precip",
            "humidity",
            "cloudcover",
            "feelslike",
            "uv_index",
            "visibility",
            ]
        for element in lista_datos:
            self.tipo_de_dato_combo_box.addItem(element)

        self.ciudad_alarma_label = QLabel("Ciudad")
        self.input_ciudad_alarma_combo_box = QComboBox()
        ciudades = ("Vigo", "Lugo", "Madrid")
        for ciudad in ciudades:
            self.input_ciudad_alarma_combo_box.addItem(ciudad)
        self.valor_alarma_label = QLabel("Valor alarma")
        self.input_valor_alarma_spin_box = QSpinBox(self.grupo_introduccion_alarma)
        self.input_valor_alarma_spin_box.setValue(0)
        self.input_valor_alarma_spin_box.setMaximum(3000)
        self.boton_anadir_alarma = QPushButton("Añadir alarma")
        self.boton_anadir_alarma.clicked.connect(self.anadir_alarma_func)
        layout_grupo_anadir_alarma = QGridLayout()
        layout_grupo_anadir_alarma.addWidget(
            self.titulo_anadir_alarma,
            0,
            0,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.tipo_alarma_combo_box,
            0,
            1,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.titulo_tipo_dato_alarma,
            1,
            0,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.tipo_de_dato_combo_box,
            1,
            1,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.ciudad_alarma_label,
            2,
            0,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.input_ciudad_alarma_combo_box,
            2,
            1,
            1,
            -1,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.valor_alarma_label,
            3,
            0,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.input_valor_alarma_spin_box,
            3,
            1,
            1,
            -1,
            Qt.AlignmentFlag.AlignTop
            )
        layout_grupo_anadir_alarma.addWidget(
            self.boton_anadir_alarma,
            4,
            0,
            1,
            -1,
            Qt.AlignmentFlag.AlignTop
            )
        self.grupo_introduccion_alarma.setLayout(layout_grupo_anadir_alarma)

        self.grupo_visualizar_alarmas = QGroupBox("Visualización de alarmas creadas")
        self.tabla_ver_alarmas = QTableWidget(0, 5)
        self.tabla_ver_alarmas.setFixedHeight(400)
        encabezado = ["", "Tipo de alarma", "Dato Afectado", "Ciudad", "Valor", "Fecha"]
        self.tabla_ver_alarmas.setHorizontalHeaderLabels(encabezado)

        self.boton_cargar_alarmas = QPushButton("Cargar alarmas")
        self.boton_cargar_alarmas.clicked.connect(self.obtener_alarmas_creadas)
        self.boton_eliminar_alarmas = QPushButton("Eliminar alarmas seleccionadas")
        self.boton_eliminar_alarmas.clicked.connect(self.eliminar_alarmas_func)

        layout_ver_alarmas = QVBoxLayout()
        layout_ver_alarmas.addWidget(self.boton_cargar_alarmas)
        layout_ver_alarmas.addWidget(self.tabla_ver_alarmas)
        layout_ver_alarmas.addWidget(self.boton_eliminar_alarmas)
        self.grupo_visualizar_alarmas.setLayout(layout_ver_alarmas)
        self.grupo_visualizar_alarmas.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
            )

        alarmas_widget_layout = QGridLayout()
        alarmas_widget_layout.addWidget(
            self.grupo_introduccion_alarma,
            0,
            0,
            1,
            -1,
            Qt.AlignmentFlag.AlignTop
            )
        alarmas_widget_layout.addWidget(
            self.grupo_visualizar_alarmas,
            1,
            0,
            1,
            -1,
            Qt.AlignmentFlag.AlignTop
            )
        alarmas_widget_layout.setRowStretch(2, 1)
        self.tab_alarmas.setLayout(alarmas_widget_layout)


        self.boton_leer_avisos = QPushButton("Leer avisos")
        self.boton_leer_avisos.clicked.connect(self.return_avisos_for_my_user)
        self.avisos_tree = QTreeWidget()
        self.avisos_tree.setColumnCount(5)
        headers = [
            "Ciudad", "Tipo alarma",
            "Dato afectado", "Valor alarma",
            "Valor dato",
            "Fecha alarma" , "Fecha Dato"]
        self.avisos_tree.setHeaderLabels(headers)
        self.avisos_tree.setFixedHeight(650)

        layout_tab_de_avisos = QGridLayout()
        layout_tab_de_avisos.addWidget(self.avisos_tree, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.addWidget(self.boton_leer_avisos, 1, 0, Qt.AlignmentFlag.AlignTop)

        layout_tab_de_avisos.setRowStretch(2, 1)

        self.tab_avisos.setLayout(layout_tab_de_avisos)

        self.tab_alarmas_avisos.addTab(self.tab_alarmas, "Alarmas")
        self.tab_alarmas_avisos.addTab(self.tab_avisos, "Avisos")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_alarmas_avisos)
        self.setLayout(main_layout)
    async def intercambiar_info_con_server(self, request):
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            await websocket.close()
        return response

    def anadir_alarma_func(self):
        """ Obtiene los datos de la alarma a añadir
        a partir de las combobox de la GUI y envia los datos
        al servidor empleando la corutina intercambiar_info_con_server
        """
        self.boton_anadir_alarma.setEnabled(False)
        tipo_alarma = self.tipo_alarma_combo_box.currentText()
        dato_afectado = self.tipo_de_dato_combo_box.currentText()
        ciudad = self.input_ciudad_alarma_combo_box.currentText()
        valor_alarma = self.input_valor_alarma_spin_box.value()
        fecha_alarma = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos_alarma = {
            "token" : self.token,
            "data" : {
                "tipo_alarma" : tipo_alarma,
                "dato_afectado" : dato_afectado,
                "ciudad" : ciudad,
                "valor_alarma" : valor_alarma,
                "fecha_alarma" : fecha_alarma
                }
            }
        data = {
            "tipo_request" : "create_alarm",
            "value" : datos_alarma
            }
        request = json.dumps(data)
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.intercambiar_info_con_server(request)
            )
        self.alarma_anadida_signal.emit(response)
        self.boton_anadir_alarma.setEnabled(True)
        self.obtener_alarmas_creadas()
    def obtener_alarmas_creadas(self):
        """ Solicita las alarmas creadas para un
        user al servidor, envia el token de sesion
        para identificar al user.
        Luego añade las alarmas que recibe usando el
        metodo anadir_lineas_de_alarmas_creadas
        """
        self.boton_cargar_alarmas.setEnabled(False)
        request = {
            "tipo_request" : "return_alarms",
            "value" : self.token
            }
        request = json.dumps(request)
        loop = asyncio.get_event_loop()
        my_alarms = loop.run_until_complete(
            self.intercambiar_info_con_server(request)
            )
        self.my_alarms = json.loads(my_alarms)
        self.alarma_anadida_signal.emit("Alarmas cargadas")
        self.tabla_ver_alarmas.setRowCount(0)
        for alarma in self.my_alarms:
            self.anadir_lineas_de_alarmas_creadas(alarma)
        self.boton_cargar_alarmas.setEnabled(True)
    def anadir_lineas_de_alarmas_creadas(self, row):
        """ Añade las alarmas recibidas por el metodo
        obtener_alarmas_creadas a la QTable.
        """
        lineas_actuales = self.tabla_ver_alarmas.rowCount()
        self.tabla_ver_alarmas.setRowCount(lineas_actuales + 1)
        widget = QWidget()
        checkbox = QCheckBox()
        check_box_layout = QGridLayout()
        check_box_layout.addWidget(checkbox, 0, 0, Qt.AlignmentFlag.AlignCenter)
        widget.setLayout(check_box_layout)

        self.tabla_ver_alarmas.setCellWidget(lineas_actuales, 0, widget)
        tipo_alarma = row["tipo_alarma"]
        dato_afectado = row["dato_afectado"]
        ciudad = row["ciudad"]
        valor_alarma = str(row["valor_alarma"])
        fecha_alarma = row["fecha_alarma"]
        tupla = (tipo_alarma, dato_afectado, ciudad, valor_alarma, fecha_alarma)
        for index, dato in enumerate(tupla):
            element = QTableWidgetItem(dato)
            self.tabla_ver_alarmas.setItem(lineas_actuales, index + 1, element)
    def eliminar_alarmas_func(self):
        """ Lee las lineas de alarmas marcadas con el checkbox,
        recopila sus datos y las elimina de la GUI.
        Ademas envía la info al servidor con el metodo
        intercambiar_info_con_server para que proceda
        a eliminar de la db las alarmas y sus notificaciones
        """
        self.boton_eliminar_alarmas.setEnabled(False)
        row_to_delete = []
        row_to_delete_query = []
        for row in range(self.tabla_ver_alarmas.rowCount()):
            checkbox = self.tabla_ver_alarmas\
                       .cellWidget(row, 0).layout().itemAt(0).widget()
            if checkbox.isChecked():
                row_to_delete.append(row)
        try:
            for row in row_to_delete:

                tipo_alarma = self.tabla_ver_alarmas.item(row, 1).text()
                dato_afectado = self.tabla_ver_alarmas.item(row, 2).text()
                ciudad = self.tabla_ver_alarmas.item(row, 3).text()
                valor_alarma = self.tabla_ver_alarmas.item(row, 4).text()
                self.tabla_ver_alarmas.removeRow(row)
                tupla_temp = (tipo_alarma, dato_afectado, ciudad, valor_alarma)
                row_to_delete_query.append(tupla_temp)
            data = {"token" : self.token, "rows_to_delete" : row_to_delete_query}
            request = {
                "tipo_request" : "delete_alarms",
                "value" : data
                }
            request = json.dumps(request)
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self.intercambiar_info_con_server(request)
                )

            self.alarma_anadida_signal.emit(response)
        except AttributeError:
            pass
        self.boton_eliminar_alarmas.setEnabled(True)
    def return_avisos_for_my_user(self):
        """ Solicita los avisos asociados al user actual
        al servidor.
        Luego los transforma en un DataFrame de pandas,
        reordena los datos para mostrarlos siguiendo una
        lógica y los añade al QTree
        """
        self.boton_leer_avisos.setEnabled(False)
        fecha = "2023-12-01 00:00"
        fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M")
        data = {"token" : self.token, "fecha_avisos": fecha}
        request = {
            "tipo_request" : "return_avisos",
            "value" : data
            }
        request = json.dumps(request, default=str)
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.intercambiar_info_con_server(request)
            )
        response = json.loads(response)
        list_tipo_alarma = []
        list_dato_afectado = []
        list_ciudad = []
        list_valor_alarma = []
        list_valor_dato = []
        list_fecha_alarma = []
        list_fecha_dato = []
        for item in response:
            list_tipo_alarma.append(item["tipo_alarma"])
            list_dato_afectado.append(item["dato_afectado"])
            list_ciudad.append(item["ciudad"])
            list_valor_alarma.append(item["valor_alarma"])
            list_valor_dato.append(item["valor_aviso"])
            list_fecha_alarma.append(item["fecha_alarma"])
            list_fecha_dato.append(item["fecha_dato"])
        data = {
            "tipo_alarma" : list_tipo_alarma,
            "dato_afectado" : list_dato_afectado,
            "ciudad" : list_ciudad,
            "valor_alarma" : list_valor_alarma,
            "valor_dato" : list_valor_dato,
            "fecha_alarma" : list_fecha_alarma,
            "fecha_dato" : list_fecha_dato,
            }
        df = pd.DataFrame(data)
        df = df.sort_values(
            by=["ciudad", "valor_alarma", "tipo_alarma",  "dato_afectado", "fecha_dato"],
            ascending=True
            )
        ciudades = df["ciudad"].unique()
        self.avisos_tree.clear()
        for ciudad in ciudades:
            df_level_1 = df.loc[df["ciudad"] == ciudad]
            tipos_alarma = df_level_1["tipo_alarma"].unique()
            ciudad_item = QTreeWidgetItem(self.avisos_tree)
            ciudad_item.setText(0, ciudad)
            for tipo in tipos_alarma:
                df_level_2 = df_level_1.loc[df_level_1["tipo_alarma"] == tipo]
                datos_afectados = df_level_2["dato_afectado"].unique()
                tipo_alarma_item = QTreeWidgetItem(self.avisos_tree)
                tipo_alarma_item.setText(1, tipo)
                ciudad_item.addChild(tipo_alarma_item)
                for dato in datos_afectados:
                    df_level_3 = df_level_2.loc[df_level_2["dato_afectado"] == dato]
                    for _, row in df_level_3.iterrows():
                        dato_afectado_item = QTreeWidgetItem(self.avisos_tree)
                        dato_afectado_item.setText(2, dato)
                        tipo_alarma_item.addChild(dato_afectado_item)
                        valor_alarma = str(row["valor_alarma"])
                        valor_dato = str(row["valor_dato"])
                        fecha_alarma = str(row["fecha_alarma"])
                        fecha_dato = str(row["fecha_dato"])
                        tupla_datos = (valor_alarma, valor_dato, fecha_alarma, fecha_dato)
                        for idx, resto_columnas in enumerate(tupla_datos):
                            dato_afectado_item.setText(idx + 3, resto_columnas)
        ## continua aqui añadiendo los avisos al
        ## tree view de alarms
        ## añade que al eliminar una alarma elimine sus avisos
        self.boton_leer_avisos.setEnabled(True)
