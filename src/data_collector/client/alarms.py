#!/usr/bin/env python
""" Contiene el widget de alarmas y sus metodos
Aqui se crean alarmas y se visualizan las notificaciones
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from PyQt5.QtCore import pyqtSignal as Signal

from qfluentwidgets import ComboBox
from qfluentwidgets import SpinBox
from qfluentwidgets import BodyLabel
from qfluentwidgets import CalendarPicker
from qfluentwidgets import PushButton
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ToolTipFilter
from qfluentwidgets import ToolTipPosition
from qfluentwidgets import TableWidget
from qfluentwidgets import TreeWidget
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition
from qfluentwidgets import RoundMenu
from qfluentwidgets import MenuAnimationType
from qfluentwidgets import Action
from qfluentwidgets import InfoBarIcon


from graphs import MessageBoxFiltrar
from general_functions import open_webbrowser


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
        self.server_ip = "localhost"
        self.setObjectName("AlarmasWidget")
        self.my_alarms = None
        """ Crea una tab con dos valores
        uno para añadir/eliminar/ver a alarmas, cada uno un grupo
        y otra para ver los avisos generados
        """

        self.df_my_notifications = pd.DataFrame()
        self.contextMenuEvent = self.menu_general # OJO
        self.filtro_actual_tabla_datos = "Todas las ciudades"
        self.primer_arranque = True



        self.tab_alarmas_avisos = QTabWidget()
        self.tab_alarmas = QWidget()


        self.tab_avisos = QWidget()
        self.grupo_introduccion_alarma = QGroupBox("Añadir alarma")
        self.titulo_anadir_alarma = QLabel("Tipo de alarma")
        self.tipo_alarma_combo_box = ComboBox()
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
        self.tipo_de_dato_combo_box = ComboBox()
        lista_datos = [
            "temp_c",
            "wind_kph",
            "pressure_mb",
            "precip_mm",
            "humidity",
            "cloud",
            "feelslike_c",
            "uv",
            ]
        for element in lista_datos:
            self.tipo_de_dato_combo_box.addItem(element)

        self.ciudad_alarma_label = QLabel("Ciudad")
        self.input_ciudad_alarma_combo_box = ComboBox()
        self.lista_ciudades = ["Vigo", "Lugo", "Madrid"]
        for ciudad in self.lista_ciudades:
            self.input_ciudad_alarma_combo_box.addItem(ciudad)
        self.valor_alarma_label = QLabel("Valor alarma")
        self.input_valor_alarma_spin_box = SpinBox(self.grupo_introduccion_alarma)
        self.input_valor_alarma_spin_box.setAccelerated(True)
        self.input_valor_alarma_spin_box.setValue(0)
        self.input_valor_alarma_spin_box.setMaximum(3000)
        self.boton_anadir_alarma = PushButton(FIF.ADD, "Añadir alarma", self)
        self.boton_anadir_alarma.clicked.connect(self.anadir_alarma_func)
        self.boton_anadir_alarma.setToolTip("Añade una alarma asociada al usuario actual")
        self.boton_anadir_alarma.installEventFilter(
            ToolTipFilter(self.boton_anadir_alarma, 0, ToolTipPosition.TOP)
            )
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
        self.tabla_ver_alarmas = TableWidget(self)
        self.tabla_ver_alarmas.setBorderVisible(True)
        self.tabla_ver_alarmas.setBorderRadius(8)
        self.tabla_ver_alarmas.setWordWrap(False)
        self.tabla_ver_alarmas.setRowCount(0)
        self.tabla_ver_alarmas.setColumnCount(5) 
        self.tabla_ver_alarmas.verticalHeader().hide()   
        self.tabla_ver_alarmas.setFixedHeight(400)

        encabezado = ["", "Tipo de alarma", "Dato Afectado", "Ciudad", "Valor", "Fecha"]
        self.tabla_ver_alarmas.setHorizontalHeaderLabels(encabezado)

        self.boton_cargar_alarmas = PushButton(FIF.ACCEPT_MEDIUM, "Cargar alarmas", self)
        self.boton_cargar_alarmas.setToolTip("Recarga los datos de alarmas")
        self.boton_cargar_alarmas.installEventFilter(
            ToolTipFilter(self.boton_cargar_alarmas, 0, ToolTipPosition.TOP)
            )
        self.boton_cargar_alarmas.clicked.connect(self.obtener_alarmas_creadas)
        self.boton_eliminar_alarmas = PrimaryPushButton(FIF.DELETE, "Eliminar alarmas seleccionadas", self)
        self.boton_eliminar_alarmas.clicked.connect(self.eliminar_alarmas_func)
        self.boton_eliminar_alarmas.setToolTip("Elimina las alarmas seleccionadas")
        self.boton_eliminar_alarmas.installEventFilter(
            ToolTipFilter(self.boton_eliminar_alarmas, 0, ToolTipPosition.TOP)
            )

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


        self.boton_leer_avisos = PrimaryPushButton(FIF.UPDATE, "Leer avisos", self)
        self.boton_leer_avisos.clicked.connect(self.return_avisos_for_my_user)
        self.boton_leer_avisos.setToolTip("Recarga las notificaciones")
        self.boton_leer_avisos.installEventFilter(
            ToolTipFilter(self.boton_leer_avisos, 0, ToolTipPosition.BOTTOM)
            )
        self.avisos_tree = TreeWidget()
        self.avisos_tree.setColumnCount(7)
        self.avisos_tree.setColumnWidth(5, 150)
        headers = [
            "Ciudad", "Tipo alarma",
            "Dato afectado", "Valor alarma",
            "Valor dato",
            "Fecha alarma" , "Fecha Dato"]
        self.avisos_tree.setHeaderLabels(headers)
        self.avisos_tree.setFixedHeight(650)

        self.avisos_tree.contextMenuEvent = self.menu_modificar_datos

        fecha_avisos_label = BodyLabel(
            "Fecha mínima de los datos que han disparado la alarma:"
            )
        fecha_avisos_label.setContentsMargins(10, 15, 10, 10)
        self.fecha_avisos_date_edit = CalendarPicker()
        self.fecha_avisos_date_edit.setDate(QDate(2023, 12, 10))
        self.fecha_avisos_date_edit.setDateFormat("dd-MM-yyyy")
        self.fecha_avisos_date_edit.setContentsMargins(10, 10, 10, 10)
        numero_de_horas_entre_avisos_label = BodyLabel("Número de horas entre avisos")
        self.numero_de_horas_entre_avisos = SpinBox(self.tab_avisos)
        self.numero_de_horas_entre_avisos.setValue(3)
        self.numero_de_horas_entre_avisos.setMaximum(5000)

        layout_tab_de_avisos = QGridLayout()
        layout_tab_de_avisos.addWidget(self.avisos_tree, 0, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.addWidget(fecha_avisos_label, 1, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.addWidget(self.fecha_avisos_date_edit, 2, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.addWidget(numero_de_horas_entre_avisos_label, 4, 0, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.addWidget(self.numero_de_horas_entre_avisos, 4, 1, Qt.AlignmentFlag.AlignTop)


        layout_tab_de_avisos.addWidget(self.boton_leer_avisos, 5, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        layout_tab_de_avisos.setRowStretch(6, 1)

        self.tab_avisos.setLayout(layout_tab_de_avisos)

        self.tab_alarmas_avisos.addTab(self.tab_alarmas, "Alarmas")
        self.tab_alarmas_avisos.addTab(self.tab_avisos, "Avisos")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_alarmas_avisos)
        self.setLayout(main_layout)
    def execute_initial_code(self):
        self.return_avisos_for_my_user()
        self.obtener_alarmas_creadas()
    def showEvent(self, event):
        pass
        """if self.primer_arranque:
            self.execute_initial_code()
            self.primer_arranque = False"""
    def menu_general(self, event):
        menu = RoundMenu(parent=self)
        accion_cambiar_usuario = Action(FIF.UPDATE, "Cambiar usuario", shortcut="Ctrl+U")
        menu.addAction(accion_cambiar_usuario)
        menu.addSeparator()
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)
        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)
    def menu_modificar_datos(self, event):
        menu = RoundMenu(parent=self)
        accion_exportar_a_excel = Action(FIF.DOCUMENT, 'Exportar', shortcut='Ctrl+E')
        accion_exportar_a_excel.triggered.connect(self.lanza_export_excel)
        menu.addAction(accion_exportar_a_excel)
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)
        menu.addSeparator()
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)

        # add sub menu
        submenu = RoundMenu("Filtrar", self)
        submenu.setIcon(FIF.FILTER)
        accion_filtrar_por_ciudad = Action(FIF.VIDEO, 'Por ciudad')
        accion_filtrar_por_ciudad.triggered.connect(self.lanzar_filtro_ciudad)
        submenu.addActions([
            accion_filtrar_por_ciudad,
            Action(FIF.PEOPLE, "Por tipo alarma"),
            Action(FIF.PEOPLE, "Por dato afectado"),
        ])
        menu.addMenu(submenu)
        menu.addSeparator()

        menu.addAction(Action(f'Por añadir: REVISAR'))

        # insert actions
        menu.insertAction(
            menu.actions()[-1], Action(FIF.SETTING, 'Cambiar usuario', shortcut='Ctrl+U'))
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.insertActions(
            menu.actions()[-1],
            [accion_ayuda,
             Action(FIF.FEEDBACK, 'Feedback', shortcut='Ctrl+F')]
        )
        menu.actions()[-2].setCheckable(True)
        menu.actions()[-2].setChecked(True)


        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)
    def lanzar_filtro_ciudad(self):
        self.dialogo_filtrar_ciudad = MessageBoxFiltrar(parent=self, lista_ciudades=self.lista_ciudades)
        self.dialogo_filtrar_ciudad.accepted.connect(self.filtrar_por_ciudad_func)
        self.dialogo_filtrar_ciudad.exec()

    def filtrar_por_ciudad_func(self):
        ciudad = self.dialogo_filtrar_ciudad.ciudad_a_filtrar.currentText()
        self.filtro_actual_tabla_datos = ciudad

        df_maestro = self.df_my_notifications
        if ciudad != "Todas las ciudades":
            df_maestro = df_maestro.loc[df_maestro["ciudad"] == ciudad]
        self.anadir_avisos(self.ciudades_anadir_al_tree, df_maestro)
    def lanza_export_excel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo excel",
            "",
            "Archivos excel (*.xlsx);;All Files (*)", options=options)
        if file_path:
            ciudad = self.filtro_actual_tabla_datos
            df_maestro = self.df_my_notifications
            if ciudad != "Todas las ciudades":
                df_maestro = df_maestro.loc[df_maestro["ciudad"] == ciudad]
            df_maestro = df_maestro.sort_values(
                by=["ciudad", "tipo_alarma",  "dato_afectado", "fecha_dato"],
                ascending=False
                )
            try:
                df_maestro.to_excel(file_path, index=False)
            except Exception as e:
                InfoBar.error(
                    title='Error',
                    content="Tipo de archivo no compatible, usar .xlsx",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    # position='Custom',   # NOTE: use custom info bar manager
                    duration=4000,
                    parent=self
                )        
    async def intercambiar_info_con_server(self, request):
        uri = f"ws://{self.server_ip}:8765"
        custom_message_size = 1024*1024*50
        async with websockets.connect(uri, max_size=custom_message_size) as websocket:
            try:
                await websocket.send(request)
                response = await websocket.recv()
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
                response = {"autenticado" : False}
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
                response = {"autenticado" : False}   
            finally:
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
        # self.alarma_anadida_signal.emit(response) # NOTA: ELIMINAR SEÑALES?
        if not isinstance(response, dict):
            InfoBar(
                icon=InfoBarIcon.INFORMATION,
                title='Resultado',
                content=response,
                orient=Qt.Vertical,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
                )
            self.obtener_alarmas_creadas()
        self.boton_anadir_alarma.setEnabled(True)
        
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
        if not isinstance(my_alarms, dict):
            my_alarms = json.loads(my_alarms)
            if my_alarms["autenticado"]:
                self.my_alarms = json.loads(my_alarms["data"])
                self.alarma_anadida_signal.emit("Alarmas cargadas")
                self.tabla_ver_alarmas.setRowCount(0)
                for alarma in self.my_alarms:
                    self.anadir_lineas_de_alarmas_creadas(alarma)
                self.tabla_ver_alarmas.resizeColumnsToContents()
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
            if not isinstance(response, dict):
                InfoBar(
                    icon=InfoBarIcon.INFORMATION,
                    title='Resultado',
                    content=response,
                    orient=Qt.Vertical,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                    )
            # self.alarma_anadida_signal.emit(response) # NOTA: ELIMINAR SEÑALES?
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
        fecha = self.fecha_avisos_date_edit.getDate()
        fecha = fecha.toString("yyyy-MM-dd")
        fecha = datetime.strptime(fecha, "%Y-%m-%d")
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
        if not isinstance(response, dict):
            response = json.loads(response)
            if response["autenticado"]:
                response_datos = response["data"]
                response_datos = json.loads(response_datos)
                ciudades, df = self.crear_df_avisos(response_datos)
                self.anadir_avisos(ciudades, df)
            else:
                # NOTA: REVISAR PORQUE CRASHEA CUANDO EXPIRA EL TOKEN
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
        self.boton_leer_avisos.setEnabled(True)
    def crear_df_avisos(self, response_datos):
        list_tipo_alarma = []
        list_dato_afectado = []
        list_ciudad = []
        list_valor_alarma = []
        list_valor_dato = []
        list_fecha_alarma = []
        list_fecha_dato = []
        for item in response_datos:
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
        df["fecha_dato"] = pd.to_datetime(df["fecha_dato"])
        df = df.sort_values(
            by=["ciudad", "tipo_alarma",  "dato_afectado", "fecha_dato"],
            ascending=True
            )
        df.reset_index(drop=True, inplace=True)
        # VAMOS A MOSTRAR SOLO LOS AVISOS QUE TENGAN COMO MINIMO 8 HORAS DE DIFERENCIA
        numero_de_horas_entre_avisos = self.numero_de_horas_entre_avisos.value()
        df = self.set_reducido_de_avisos_filtrar(df, numero_de_horas_entre_avisos)
        ciudades = df["ciudad"].unique()
        self.df_my_notifications = df
        self.ciudades_anadir_al_tree = ciudades
        return ciudades, df

    def anadir_avisos(self, ciudades, df):
        self.avisos_tree.clear()
        ciudades_unicas = df["ciudad"].unique()
        desplegar = False
        for cid in ciudades_unicas:
            if cid in ciudades:
                desplegar = True
            else:
                # remove np elements from array
                # that does not have a coincidence in the df
                ciudades_unicas = ciudades_unicas != cid
                # if not deleted
                # appears a city in the tree view without data
        if desplegar:
            for ciudad in ciudades_unicas:
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
    def set_reducido_de_avisos_filtrar(self, df: pd.DataFrame, numero_de_horas_entre_avisos: int):
        list_tipo_alarma = []
        list_dato_afectado = []
        list_ciudad = []
        list_valor_alarma = []
        list_valor_dato = []
        list_fecha_alarma = []
        list_fecha_dato = []
        tomar_siguiente_dato = True
        for indice, fila in df.iterrows():
            if indice == 0:
                list_tipo_alarma.append(fila["tipo_alarma"])
                list_dato_afectado.append(fila["dato_afectado"])
                list_ciudad.append(fila["ciudad"])
                list_valor_alarma.append(fila["valor_alarma"])
                list_valor_dato.append(fila["valor_dato"])
                list_fecha_alarma.append(fila["fecha_alarma"])
                list_fecha_dato.append(fila["fecha_dato"])
            else:
                if tomar_siguiente_dato:
                    minimum_date = fila["fecha_dato"]
                    tomar_siguiente_dato = False
                if df.iloc[indice - 1]["ciudad"] == fila["ciudad"]:
                    if df.iloc[indice - 1]["tipo_alarma"] == fila["tipo_alarma"]:
                        if df.iloc[indice - 1]["dato_afectado"] == fila["dato_afectado"]:
                            if (fila["fecha_dato"] - minimum_date).total_seconds() / 3600 >= numero_de_horas_entre_avisos:
                                list_tipo_alarma.append(fila["tipo_alarma"])
                                list_dato_afectado.append(fila["dato_afectado"])
                                list_ciudad.append(fila["ciudad"])
                                list_valor_alarma.append(fila["valor_alarma"])
                                list_valor_dato.append(fila["valor_dato"])
                                list_fecha_alarma.append(fila["fecha_alarma"])
                                list_fecha_dato.append(fila["fecha_dato"])
                                tomar_siguiente_dato = True
                        else:
                            tomar_siguiente_dato = True
                    else:
                        tomar_siguiente_dato = True
                else:
                    list_tipo_alarma.append(fila["tipo_alarma"])
                    list_dato_afectado.append(fila["dato_afectado"])
                    list_ciudad.append(fila["ciudad"])
                    list_valor_alarma.append(fila["valor_alarma"])
                    list_valor_dato.append(fila["valor_dato"])
                    list_fecha_alarma.append(fila["fecha_alarma"])
                    list_fecha_dato.append(fila["fecha_dato"])
                    tomar_siguiente_dato = True
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
        df["fecha_dato"] = pd.to_datetime(df["fecha_dato"])
        df = df.sort_values(
            by=["ciudad", "tipo_alarma",  "dato_afectado", "valor_alarma", "fecha_dato"],
            ascending=True
            )
        df.reset_index(drop=True, inplace=True)
        return df

