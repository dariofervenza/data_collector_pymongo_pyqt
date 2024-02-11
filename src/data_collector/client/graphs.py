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
import random
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizePolicy
#from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRunnable
from PyQt5.QtCore import QThreadPool

#import plotly.graph_objs as go
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from qfluentwidgets import ComboBox
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import PushButton
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TeachingTip
from qfluentwidgets import InfoBarIcon
from qfluentwidgets import TeachingTipTailPosition
from qfluentwidgets import TitleLabel
from qfluentwidgets import SubtitleLabel
from qfluentwidgets import BodyLabel
from qfluentwidgets import ToolTipFilter
from qfluentwidgets import ToolTipPosition
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition
from qfluentwidgets import SpinBox
from qfluentwidgets import FlowLayout
from qfluentwidgets import SmoothScrollArea
from qfluentwidgets import TableWidget
from qfluentwidgets import Slider
from qfluentwidgets import Action
from qfluentwidgets import RoundMenu
from qfluentwidgets import MenuAnimationType
from qfluentwidgets import MessageBoxBase

from general_functions import open_webbrowser

#from qframelesswindow.webengine import FramelessWebEngineView

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

class GraficosWidget(QFrame):
    """ Crea el widget de graficos
    En el se muestran los datos de la API usando
    un chart de plotly y una Qtable
    """
    def __init__(self):
        super().__init__()
        self.token = None
        self.db_data = None
        self.server_ip = "localhost"
        self.setObjectName("GraficosWidget")
        self.lista_ciudades = ["Vigo", "Lugo", "Madrid"]
        self.lista_variables = ["Temperatura", "Humedad", "Presion"]
        self.filtro_actual_tabla_datos = "Todas las ciudades"
        self.ultimo_color = 'tab:cyan'

        self.df_actual = pd.DataFrame()
        #self.fig = go.Figure()
        self.contextMenuEvent = self.menu_general
        self.primer_arranque = True



        tab_maestra = QTabWidget()
        scroll_area_maestra_graficos = SmoothScrollArea()
        tab_graficos_container = QWidget()
        scroll_area_maestra_graficos.setWidget(tab_graficos_container)
        scroll_area_maestra_graficos.setWidgetResizable(True)
        tab_graficos_container.wheelEvent = lambda event: self.on_whell_event(event, scroll_area_maestra_graficos) 
        layout_scroll_maestro_graficos = QVBoxLayout()
        layout_scroll_maestro_graficos.addWidget(tab_graficos_container)
        scroll_area_maestra_graficos.setLayout(layout_scroll_maestro_graficos)

        tab_maestra.addTab(scroll_area_maestra_graficos, "Graficos")

        tab_datos_container = QWidget()
        tab_maestra.addTab(tab_datos_container, "Datos")

        layout_maestro = QVBoxLayout()


        titulo_graficos = TitleLabel("Visualización de los gráficos")
        grupo_anadir_eliminar_graficos = QGroupBox("Modificar datos mostrados")
        layout_grupo_anadir_graf = QGridLayout()
        grupo_anadir_eliminar_graficos.setLayout(layout_grupo_anadir_graf)
        label_anadir_grafico = SubtitleLabel("Añadir gráfico")
        self.ciudad_anadir_grafico = ComboBox()
        for ciudad in self.lista_ciudades:
            self.ciudad_anadir_grafico.addItem(ciudad)
        self.variable_anadir_grafico = ComboBox()
        for variable in self.lista_variables:
            self.variable_anadir_grafico.addItem(variable)
        boton_anadir_grafico = PushButton(FIF.ADD, "Añadir gráfico", self)
        boton_anadir_grafico.setToolTip("Añade un nuevo grafico en la zona inferior")
        boton_anadir_grafico.installEventFilter(
            ToolTipFilter(boton_anadir_grafico, 0, ToolTipPosition.BOTTOM_RIGHT)
            )

        boton_anadir_grafico.clicked.connect(self.anadir_grafico_func)
        layout_grupo_anadir_graf.addWidget(label_anadir_grafico, 0, 0)   
        layout_grupo_anadir_graf.addWidget(self.ciudad_anadir_grafico, 1, 0)   
        layout_grupo_anadir_graf.addWidget(self.variable_anadir_grafico, 2, 0)   
        layout_grupo_anadir_graf.addWidget(boton_anadir_grafico, 3, 0)

        boton_recargar_datos_de_la_db = PrimaryPushButton(FIF.DOWNLOAD, "Leer datos de la db", self)
        boton_recargar_datos_de_la_db.clicked.connect(self.read_data_from_db)

        boton_recargar_datos_de_la_db.setToolTip("Lee los datos almacenados en la base de datos")
        boton_recargar_datos_de_la_db.installEventFilter(ToolTipFilter(boton_recargar_datos_de_la_db, 300, ToolTipPosition.BOTTOM))
        layout_grupo_anadir_graf.addWidget(boton_recargar_datos_de_la_db, 1, 1, 2, 1)
        self.indice_color = 0


        graficos_widget_container = QWidget()
        self.flow_layout_graficos_widget = FlowLayout()
        graficos_widget_container.setLayout(self.flow_layout_graficos_widget)

        self.lista_grupos_graficos = []

        grupo_1 = QGroupBox("Grafico 1: Temperaturas en Vigo")
        canvas_fig_1 = FigureCanvas()
        canvas_fig_1.mpl_connect('button_press_event', self.on_canvas_click)
        layout = QVBoxLayout()
        layout.addWidget(canvas_fig_1)
        grupo_1.setLayout(layout)
        self.lista_grupos_graficos.append(grupo_1)

        grupo_2 = QGroupBox("Gráfico 2: Humedad en Vigo")
        canvas_fig_humedad = FigureCanvas()
        canvas_fig_humedad.mpl_connect('button_press_event', self.on_canvas_click)

        layout_humedad = QVBoxLayout()
        layout_humedad.addWidget(canvas_fig_humedad)
        grupo_2.setLayout(layout_humedad)
        self.lista_grupos_graficos.append(grupo_2)

        grupo_3 = QGroupBox("Gráfico 3: Presion en Vigo")
        canvas_fig_3 = FigureCanvas()
        canvas_fig_3.mpl_connect('button_press_event', self.on_canvas_click)
        layout_presion = QVBoxLayout()
        layout_presion.addWidget(canvas_fig_3)
        grupo_3.setLayout(layout_presion)
        self.lista_grupos_graficos.append(grupo_3)

        for grupo in self.lista_grupos_graficos:
            self.flow_layout_graficos_widget.addWidget(grupo)


        self.combobox_grupos_a_eliminar = ComboBox()
        label_eliminar_grafico = SubtitleLabel("Eliminar grupo")
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.boton_eliminar_grafico = PushButton(FIF.DELETE, "Eliminar", self)
        self.boton_eliminar_grafico.setToolTip("Elimina el gráfico seleccionado en el despegable superior")
        self.boton_eliminar_grafico.installEventFilter(
            ToolTipFilter(self.boton_eliminar_grafico, 0, ToolTipPosition.BOTTOM_RIGHT)
            )
        self.boton_eliminar_grafico.clicked.connect(self.eliminar_grafico)
        layout_grupo_anadir_graf.addWidget(label_eliminar_grafico, 0, 2)
        layout_grupo_anadir_graf.addWidget(self.combobox_grupos_a_eliminar, 2, 2)
        layout_grupo_anadir_graf.addWidget(self.boton_eliminar_grafico, 3, 2)

        self.widget_inferior_graphs = QWidget()
        grupo_widget_customizar_graph = QGroupBox("Modificar gráficos")
        layout_widget_inferior_graphs = QGridLayout()
        layout_grupo_widget_customizar_graph= QVBoxLayout()
        grupo_widget_customizar_graph.setLayout(layout_grupo_widget_customizar_graph)
        self.widget_inferior_graphs.setLayout(layout_widget_inferior_graphs)

        self.explicacion_boton = PushButton(FIF.EDUCATION, "Mostrar explicación", self)
        self.explicacion_boton.clicked.connect(self.mostrar_explicacion_datos)

        subtitulo_cambiar_datos = SubtitleLabel("Modificar tamaño")

        self.grafico_combobox = ComboBox()

        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.grafico_combobox.currentIndexChanged.connect(self.modify_graph_target_to_resize)

        self.slider_width = Slider(Qt.Vertical)
        self.slider_width.setValue(75)
        self.slider_width.sliderReleased.connect(self.modify_graph_size)
        self.slider_height = Slider(Qt.Vertical)
        self.slider_height.setValue(75)
        self.slider_height.sliderReleased.connect(self.modify_graph_size)

        layout_widget_inferior_graphs.addWidget(self.explicacion_boton, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(subtitulo_cambiar_datos, 1, 0, 1, 3, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.grafico_combobox, 2, 0, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.slider_width, 2, 1, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.slider_height, 2, 2, Qt.AlignmentFlag.AlignTop)
        #self.flow_layout_graficos_widget.addWidget(self.widget_inferior_graphs)
        layout_grupo_widget_customizar_graph.addWidget(self.widget_inferior_graphs)


        layout_tab_graficos = QGridLayout()
        layout_tab_graficos.addWidget(
            titulo_graficos,
            0,
            0,
            1,
            3,
            Qt.AlignmentFlag.AlignCenter
            )
        layout_tab_graficos.addWidget(
            grupo_anadir_eliminar_graficos,
            1,
            0,
            1,
            1,
            Qt.AlignmentFlag.AlignCenter
            )
        layout_tab_graficos.addWidget(
            grupo_widget_customizar_graph,
            1,
            2,
            1,
            1,
            Qt.AlignmentFlag.AlignCenter
            )       
        layout_tab_graficos.addWidget(
            graficos_widget_container,
            2,
            0,
            1,
            3,
            Qt.AlignmentFlag.AlignTop
            )


        layout_tab_graficos.setContentsMargins(10, 30, 10, 10)
        layout_tab_graficos.setRowStretch(8, 1)

        titulo_datos = TitleLabel("Visualización de los datos")
        label_seleccionar_horas_entre_datos = BodyLabel("Numero de horas entre datos")
        self.spin_box_horas_entre_datos = SpinBox(tab_datos_container)
        self.spin_box_horas_entre_datos.setValue(3)
        self.spin_box_horas_entre_datos.setMaximum(5000)
        self.tabla_datos = TableWidget(self)
        self.tabla_datos.setBorderVisible(True)
        self.tabla_datos.setBorderRadius(8)
        self.tabla_datos.setWordWrap(False)
        self.tabla_datos.setRowCount(0)
        self.tabla_datos.setColumnCount(5) 
        self.tabla_datos.verticalHeader().hide() 
        # NOTA: menu modificar datos --> continuar aqui, boton descargar?
        # añade otros menus click derecho
        self.tabla_datos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_datos.customContextMenuRequested.connect(self.menu_modificar_datos)
        
  
        encabezado = ["Ciudad", "Fecha", "Temperatura", "Humedad", "Presión"]
        #self.tabla_datos.setColumnWidth(1, 150)
        self.tabla_datos.setHorizontalHeaderLabels(encabezado)
        self.boton_actualizar_datos = PushButton(FIF.EDIT, "Recargar datos", self)
        self.boton_actualizar_datos.clicked.connect(self.add_lines_to_data_table)
        self.boton_actualizar_datos.setToolTip("Recarga la tabla de datos")
        self.boton_actualizar_datos.installEventFilter(
            ToolTipFilter(self.boton_actualizar_datos, 0, ToolTipPosition.TOP)
            )

        layout_ver_datos = QGridLayout()
        layout_ver_datos.addWidget(titulo_datos, 0, 0)
        layout_ver_datos.addWidget(label_seleccionar_horas_entre_datos, 0, 1)
        layout_ver_datos.addWidget(self.spin_box_horas_entre_datos, 0, 2)
        layout_ver_datos.addWidget(self.tabla_datos, 1, 0, 1, 3)
        layout_ver_datos.addWidget(self.boton_actualizar_datos, 2, 0, 1, 3)
        tab_datos_container.setLayout(layout_ver_datos)

        tab_graficos_container.setLayout(layout_tab_graficos)
        layout_maestro.addWidget(tab_maestra)
        self.setLayout(layout_maestro)
    def menu_general(self, event):
        menu = RoundMenu(parent=self)
        accion_cambiar_usuario = Action(FIF.UPDATE, "Cambiar usuario", shortcut="Ctrl+U")
        menu.addAction(accion_cambiar_usuario)
        menu.addSeparator()
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)
        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)
    def lanzar_filtro_ciudad(self):
        self.dialogo_filtrar_ciudad = MessageBoxFiltrar(parent=self, lista_ciudades=self.lista_ciudades)
        self.dialogo_filtrar_ciudad.accepted.connect(self.filtrar_por_ciudad_func)
        self.dialogo_filtrar_ciudad.exec()
    def filtrar_por_ciudad_func(self):
        ciudad = self.dialogo_filtrar_ciudad.ciudad_a_filtrar.currentText()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        self.filtro_actual_tabla_datos = ciudad
        df_maestro = self.df_actual
        if ciudad != "Todas las ciudades":
            df_maestro = df_maestro.loc[df_maestro["ciudad"] == ciudad]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
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
        self.tabla_datos.resizeColumnsToContents()
        self.add_lines_to_data_table_success()
        self.boton_actualizar_datos.setEnabled(True)
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
            df_maestro = self.df_actual
            if ciudad != "Todas las ciudades":
                df_maestro = df_maestro.loc[df_maestro["ciudad"] == ciudad]
            df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
            numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
            df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
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


    def menu_modificar_datos(self, event):
        menu = RoundMenu(parent=self)
        accion_exportar_a_excel = Action(FIF.DOCUMENT, 'Exportar', shortcut='Ctrl+E')
        accion_exportar_a_excel.triggered.connect(self.lanza_export_excel)
        menu.addAction(accion_exportar_a_excel)
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)

        # add sub menu
        submenu = RoundMenu("Filtrar", self)
        submenu.setIcon(FIF.FILTER)
        accion_filtrar_por_ciudad = Action(FIF.VIDEO, 'Por ciudad')
        accion_filtrar_por_ciudad.triggered.connect(self.lanzar_filtro_ciudad)
        accion_filtrar_por_fecha = Action(FIF.VIDEO, 'Por fecha')
        accion_filtrar_por_temperatura = Action(FIF.VIDEO, 'Por temperatura')
        accion_filtrar_por_humedad = Action(FIF.VIDEO, 'Por humedad')
        accion_filtrar_por_presion = Action(FIF.VIDEO, 'Por presion')
        submenu.addActions([
            accion_filtrar_por_ciudad,
            accion_filtrar_por_fecha,
            accion_filtrar_por_temperatura,
            accion_filtrar_por_humedad,
            accion_filtrar_por_presion,
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

        # show menu
        menu.exec(self.mapToGlobal(event), aniType=MenuAnimationType.DROP_DOWN)
    def on_whell_event(self, event, scroll_area):
        delta = event.angleDelta().y()
        delta = int(scroll_area.verticalScrollBar().value() - delta / 3)
        scroll_area.verticalScrollBar().setValue(delta)
    def add_lines_to_data_table_success(self):
        InfoBar.success(
            title='Finalizado',
            content="Datos recargados",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            # position='Custom',   # NOTE: use custom info bar manager
            duration=1000,
            parent=self
        )
    def add_lines_to_data_table(self):
        """ Función encargada de solicitar los
        datos de la API y mostralos en la QTable
        """
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = pd.DataFrame()
        self.obtain_data()
        self.create_df_from_data()
        df = self.df_actual
        df_maestro = pd.concat([df_maestro, df])
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
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
        self.tabla_datos.resizeColumnsToContents()
        self.add_lines_to_data_table_success()
        self.boton_actualizar_datos.setEnabled(True)
    def filtrar_df_datos(self, df, numero_horas_entre_datos):
        lista_fechas = []
        lista_temperaturas = []
        lista_humedades = []
        lista_presiones = []
        lista_ciudades = []
        tomar_siguiente_dato = True
        df = df.sort_values(by=["ciudad", "fecha"], ascending=True)
        df.reset_index(drop=True, inplace=True)
        for indice, fila in df.iterrows():
            if indice == 0:
                lista_fechas.append(fila["fecha"])
                lista_temperaturas.append(fila["temperatura"])
                lista_humedades.append(fila["humedad"])
                lista_presiones.append(fila["presion"])
                lista_ciudades.append(fila["ciudad"])
            else:
                if tomar_siguiente_dato:
                    minimum_date = fila["fecha"]
                    tomar_siguiente_dato = False
                if df.iloc[indice - 1]["ciudad"] == fila["ciudad"]:
                    if ((fila["fecha"] - minimum_date).total_seconds() / 3600) >= numero_horas_entre_datos:
                        lista_fechas.append(fila["fecha"])
                        lista_temperaturas.append(fila["temperatura"])
                        lista_humedades.append(fila["humedad"])
                        lista_presiones.append(fila["presion"])
                        lista_ciudades.append(fila["ciudad"])
                        tomar_siguiente_dato = True
                    else:
                        pass
                else:
                    lista_fechas.append(fila["fecha"])
                    lista_temperaturas.append(fila["temperatura"])
                    lista_humedades.append(fila["humedad"])
                    lista_presiones.append(fila["presion"])
                    lista_ciudades.append(fila["ciudad"])
                    tomar_siguiente_dato = True
        data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones,
            "ciudad" : lista_ciudades,
            }
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values(
            by=["ciudad", "fecha"],
            ascending=False
            )
        df.reset_index(drop=True, inplace=True)       
        return df
    def modify_graph_target_to_resize(self):
        grupo_objetivo = self.grafico_combobox.currentText()
        for group in self.lista_grupos_graficos:
            if group.title() == grupo_objetivo:
                width = group.width()
                height = group.height()
                valor_slider_width = 100 - int((width - 250) * 100 / 1000)
                valor_slider_height = 100 - int((height - 250) * 100 / 1000)
                self.slider_width.setValue(valor_slider_width)
                self.slider_height.setValue(valor_slider_height)

    def modify_graph_size(self):
        grafico = self.grafico_combobox.currentText()
        grafico = int(grafico.split(":")[0][-1]) - 1
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        group = self.lista_grupos_graficos[grafico]
        canvas = group.layout().itemAt(0).widget()
        canvas.setFixedHeight(height)
        group.setFixedHeight(height)
        canvas.setFixedWidth(width)
        group.setFixedWidth(width)
        canvas.draw()

    def anadir_grafico_func(self):
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        ciudad = self.ciudad_anadir_grafico.currentText()
        variable = self.variable_anadir_grafico.currentText()
        fig = self.create_figure(ciudad, variable)
        print("largo:")
        print(len(self.lista_grupos_graficos))
        ultima_figura_index = int(len(self.lista_grupos_graficos)) + 1
        print(ultima_figura_index)
        grupo = QGroupBox(f"Gráfico {ultima_figura_index}: {variable} en {ciudad}")
        layout_grupo = QVBoxLayout()
        canvas = FigureCanvas(fig)
        canvas.mpl_connect('button_press_event', self.on_canvas_click)
        canvas.setFixedHeight(height)
        grupo.setFixedHeight(height)
        canvas.setFixedWidth(width)
        grupo.setFixedWidth(width)
        layout_grupo.addWidget(canvas)
        grupo.setLayout(layout_grupo)
        self.lista_grupos_graficos.append(grupo)
        self.renombrar_grupos()

        self.combobox_grupos_a_eliminar.clear()
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.grafico_combobox.clear()    
        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.volver_a_desplegar_graficos()
    def volver_a_desplegar_graficos(self):
        self.flow_layout_graficos_widget.removeAllWidgets()
        for group in self.lista_grupos_graficos:
            self.flow_layout_graficos_widget.addWidget(group)

    def eliminar_grafico(self):
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        titulo_grupo = self.combobox_grupos_a_eliminar.currentText()
        for index, group in enumerate(self.lista_grupos_graficos):
            if len(self.lista_grupos_graficos) == 1:
                TeachingTip.create(
                    target=self.boton_eliminar_grafico,
                    icon=InfoBarIcon.ERROR,
                    title="Info",
                    content="No puede eliminarse el último grafico",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                    )
            else:
                if group.title() == titulo_grupo:
                    canvas = group.layout().itemAt(0).widget()
                    canvas.figure.clear()
                    plt.close(canvas.figure)
                    grupo = self.lista_grupos_graficos[index]
                    self.flow_layout_graficos_widget.removeWidget(grupo)
                    grupo.deleteLater()
                    self.lista_grupos_graficos.pop(index)
                    self.renombrar_grupos()
        self.combobox_grupos_a_eliminar.clear()
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.grafico_combobox.clear()    
        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.volver_a_desplegar_graficos()

    def renombrar_grupos(self):
        new_list = []
        for index, group in enumerate(self.lista_grupos_graficos):
            partes_titulo = group.title().split(":")
            parte1 = partes_titulo[0][: -1]
            print(len(parte1))
            if len(parte1) == 9:
                parte1 = parte1[: -1]
            print(parte1)
            parte1 = parte1 + str(index + 1) + ":"
            new_title = parte1 + partes_titulo[1]
            print("partes renombrar")
            print(partes_titulo)
            print(parte1)
            
            print(new_title)
            group.setTitle(new_title)
            new_list.append(group)
        self.lista_grupos_graficos = new_list

    def read_data_from_db(self):
        """ Llama a la funcion encargada de
        obtener los datos de la db, luego a la
        que genera un DataFrame de pandas y
        por ultimo a la funcion de generar la plotly fig
        """
        self.obtain_data()
        self.create_df_from_data()
        self.add_lines_to_data_table_success()
    def showEvent(self, event):
        pass
        """if self.primer_arranque:
            self.execute_initial_code()
            self.primer_arranque = False"""
    def execute_initial_code(self):
        self.read_data_from_db()
        self.create_initial_figures()
        self.add_lines_to_data_table()
    def create_initial_figures(self):
        ciudad = self.ciudad_anadir_grafico.currentText()
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        fig_tuple = (
            self.create_figure(ciudad, valor="Temperatura"),
            self.create_figure(ciudad, valor="Humedad"),
            self.create_figure(ciudad, valor="Presion")
            )
        for index, group in enumerate(self.lista_grupos_graficos):
            canvas = group.layout().itemAt(0).widget()
            canvas.figure = fig_tuple[index]
            canvas.setFixedHeight(height)
            group.setFixedHeight(height)
            canvas.setFixedWidth(width)
            group.setFixedWidth(width)
            canvas.draw()

    def obtain_data(self): # NOTA: Se obtienen los datos para los graphs y para la tabla, ¿debería obtenerse solo una vez?
        """ Lee la ciudad seleccionada en la combobox
        de la tab de visualizar graficos
        y obtiene los datos de la db asociados a esa ciudad
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db())
    async def retrieve_data_from_db(self):
        """ Realiza la solicitud de datos al servidor
        utilizando websockets
        """
        uri = f"ws://{self.server_ip}:8765"
        query = {}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)
        custom_message_size = 1024*1024*50
        async with websockets.connect(uri, max_size=custom_message_size) as websocket:
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
        lista_ciudades = []
        datos = self.db_data
        for element in datos:
            try:
                if "temperature" in element["current"].keys():
                    fecha = element["location"]["localtime"]
                    temperatura = element["current"]["temperature"]
                    humedad = element["current"]["humidity"]
                    presion = element["current"]["pressure"]
                    ciudad = element["location"]["name"]
                else:
                    fecha = element["location"]["localtime"]
                    temperatura = element["current"]["temp_c"]
                    humedad = element["current"]["humidity"]
                    presion = element["current"]["pressure_mb"]
                    ciudad = element["location"]["name"]
                lista_fechas.append(fecha)
                lista_temperaturas.append(temperatura)
                lista_humedades.append(humedad)
                lista_presiones.append(presion)
                lista_ciudades.append(ciudad)
            except KeyError:
                print("error")
                print(element)
        dict_data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones,
            "ciudad" : lista_ciudades,
            }
        df = pd.DataFrame(dict_data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        self.df_actual = df
    def create_figure(self, ciudad: str, valor: str):
        datos = self.df_actual
        datos = datos.loc[datos["ciudad"] == ciudad]
        if valor == "Temperatura":
            valor2 = "temperatura"
        elif valor == "Humedad":
            valor2 = "humedad"
        elif valor == "Presion":
            valor2 = "presion"
        self.colors = [
            'tab:blue',
            'tab:orange',
            'tab:green',
            'tab:red',
            'tab:purple',
            'tab:brown',
            'tab:pink',
            'tab:gray',
            'tab:olive',
            'tab:cyan'
        ]
        color = random.choice(self.colors)
        while color == self.ultimo_color:
            color = random.choice(self.colors)
        fig, ax = plt.subplots(figsize=(5, 4))
        datos = datos[["fecha", valor2]]
        datos = datos.set_index("fecha")
        datos.plot(ax=ax, label=f"{valor} en {ciudad}", color=color)
        ax.set_title(f"Evolución {valor2} en {ciudad}", fontsize=15)
        ax.set_xlabel("Fecha", fontsize=15)
        ax.set_ylabel(f"{valor}", fontsize=15)
        locator = mdates.DayLocator(interval=10) # Set to every 2 weeks (15 days)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.tight_layout()
        plt.xticks(rotation=35)
        ax.tick_params(axis='both', which='both', labelsize=12)
        return fig
    """def create_plotly_fig(self, ciudad: str, valor: str, variable: FramelessWebEngineView):"""
    """ Crea una figura de plotly con el DataFrame
    de pandas generado con el metodo create_df_from_data
    y devuelve asigna su html a un widget QWebView, el
    cual es recibido como parametro
    """
    """datos = self.df_actual
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
    print("ok")"""
    def mostrar_explicacion_datos(self):
        content = """
            Los anteriores graficos muestran los datos
            obtenidos de la API de WeatherStack.
            \nSe muestra la temperatura, humedad y presión en
            un de las ciudades (Vigo, Lugo o Madrid).
            \nEn una futura actualización se podrán añadir/eliminar
            gráficos, por ejemplo, si solo quiero ver los gráficos
            de humedad y velocidad del viento (además de combinar ciudades)
            """
        TeachingTip.create(
            target=self.explicacion_boton,
            icon=InfoBarIcon.SUCCESS,
            title="Info",
            content=content,
            isClosable=True,
            tailPosition=TeachingTipTailPosition.TOP,
            duration=20000,
            parent=self
            )
    def on_canvas_click(self, event):
        print("clickc")
class MessageBoxFiltrar(MessageBoxBase):
    def __init__(self, parent=None, lista_ciudades=None):
        super().__init__(parent)
        self.lista_ciudades = lista_ciudades
        self.titulo = SubtitleLabel("Filtrado de los datos", self)
        self.ciudad_a_filtrar = ComboBox(self)
        self.ciudad_a_filtrar.addItem("Todas las ciudades")
        for ciudad in self.lista_ciudades:
            self.ciudad_a_filtrar.addItem(ciudad)
        self.viewLayout.addWidget(self.titulo)
        self.viewLayout.addWidget(self.ciudad_a_filtrar)
        self.yesButton.setText('Aceptar')
        self.cancelButton.setText('Cancelar')
        self.widget.setMinimumWidth(350)

