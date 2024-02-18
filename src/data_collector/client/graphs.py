#!/usr/bin/env python
""" Contiene la clase que define
el widget de visualización de datos,
ya sea en forma de graficos o en una
QTable
"""
import os
import json
import asyncio
import random
from typing import List
from datetime import datetime
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
# from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate

#import plotly.graph_objs as go
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
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
from qfluentwidgets import CalendarPicker

from general_functions import open_webbrowser

#from qframelesswindow.webengine import FramelessWebEngineView

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

class GraficosWidget(QFrame):
    """ Crea el widget de graficos
    En el se muestran los datos de la API usando
    un chart de plotly y una Qtable
    """
    def __init__(self, lista_ciudades, lista_variables):
        super().__init__()
        self.token = None
        self.db_data = None
        self.server_ip = "localhost"
        self.setObjectName("GraficosWidget")
        self.lista_ciudades = lista_ciudades
        self.lista_variables = lista_variables
        self.ultimo_color = 'tab:cyan'
        self.df_actual = pd.DataFrame()
        self.df_actual_filtrado = pd.DataFrame()
        #self.fig = go.Figure()
        self.contextMenuEvent = self.menu_general
        self.primer_arranque = True
        self.dialogo_filtrar_ciudad: MessageBoxFiltrar = None
        self.dialogo_filtrar_fecha: MessageBoxFiltrarPorFecha = None
        self.dialogo_filtrar_temperatura: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_humedad: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_presion: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_wind_speed: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_wind_degree: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_precip: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_cloudcover: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_uv_index: MessageBoxFiltrarEntreDosValoresSpinBox = None
        self.dialogo_filtrar_is_day: MessageBoxFiltrarDiaNoche = None
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
        tab_maestra = QTabWidget()
        scroll_area_maestra_graficos = SmoothScrollArea()
        tab_graficos_container = QWidget()
        scroll_area_maestra_graficos.setWidget(tab_graficos_container)
        scroll_area_maestra_graficos.setWidgetResizable(True)
        tab_graficos_container.wheelEvent = \
            lambda event: self.on_whell_event(event, scroll_area_maestra_graficos)
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
        self.boton_eliminar_grafico.setToolTip(
            "Elimina el gráfico seleccionado en el despegable superior"
            )
        self.boton_eliminar_grafico.installEventFilter(
            ToolTipFilter(self.boton_eliminar_grafico, 0, ToolTipPosition.BOTTOM_RIGHT)
            )
        self.boton_eliminar_grafico.clicked.connect(self.eliminar_grafico)
        layout_grupo_anadir_graf.addWidget(label_eliminar_grafico, 0, 2)
        layout_grupo_anadir_graf.addWidget(self.combobox_grupos_a_eliminar, 2, 2)
        layout_grupo_anadir_graf.addWidget(self.boton_eliminar_grafico, 3, 2)

        grupo_modificar_datos = QGroupBox("Modificar datos")
        layout_grupo_modificar_datos = QVBoxLayout()
        grupo_modificar_datos.setLayout(layout_grupo_modificar_datos)
        label_horas_resamplear_df = SubtitleLabel("Horas entre datos")
        self.spinbox_horas_entre_datos_df = SpinBox()
        self.spinbox_horas_entre_datos_df.setValue(3)
        self.spinbox_horas_entre_datos_df.setMaximum(5000)
        boton_recargar_datos_de_la_db = PrimaryPushButton(FIF.DOWNLOAD, "Leer datos de la db", self)
        boton_recargar_datos_de_la_db.clicked.connect(self.read_data_from_db)
        boton_recargar_datos_de_la_db.setToolTip("Lee los datos almacenados en la base de datos")
        boton_recargar_datos_de_la_db.installEventFilter(
            ToolTipFilter(boton_recargar_datos_de_la_db, 300, ToolTipPosition.BOTTOM)
            )
        layout_grupo_modificar_datos.addWidget(label_horas_resamplear_df)
        layout_grupo_modificar_datos.addWidget(self.spinbox_horas_entre_datos_df)
        layout_grupo_modificar_datos.addWidget(boton_recargar_datos_de_la_db)

        self.widget_con_grupo_modificar_graphs = QWidget()
        grupo_widget_customizar_graph = QGroupBox("Modificar gráficos")
        layout_widget_con_grupo_modificar_graphs = QGridLayout()
        layout_grupo_widget_customizar_graph= QVBoxLayout()
        grupo_widget_customizar_graph.setLayout(layout_grupo_widget_customizar_graph)
        self.widget_con_grupo_modificar_graphs.setLayout(layout_widget_con_grupo_modificar_graphs)

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
        layout_widget_con_grupo_modificar_graphs.addWidget(
            self.explicacion_boton, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop
            )
        layout_widget_con_grupo_modificar_graphs.addWidget(
            subtitulo_cambiar_datos, 1, 0, 1, 3, Qt.AlignmentFlag.AlignTop
            )
        layout_widget_con_grupo_modificar_graphs.addWidget(
            self.grafico_combobox, 2, 0, Qt.AlignmentFlag.AlignTop
            )
        layout_widget_con_grupo_modificar_graphs.addWidget(
            self.slider_width, 2, 1, Qt.AlignmentFlag.AlignTop
            )
        layout_widget_con_grupo_modificar_graphs.addWidget(
            self.slider_height, 2, 2, Qt.AlignmentFlag.AlignTop
            )
        #self.flow_layout_graficos_widget.addWidget(self.widget_con_grupo_modificar_graphs)
        layout_grupo_widget_customizar_graph.addWidget(
            self.widget_con_grupo_modificar_graphs
            )
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
            grupo_modificar_datos,
            1,
            1,
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
        self.tabla_datos.setColumnCount(11)
        self.tabla_datos.verticalHeader().hide()
        # NOTA: menu modificar datos --> continuar aqui, boton descargar?
        # añade otros menus click derecho
        self.tabla_datos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_datos.customContextMenuRequested.connect(self.menu_modificar_datos)
        encabezado = [
            "Ciudad", "Fecha", "Temperatura", "Humedad", "Presión",
            "VelocidadViento", "GradosViento", "Precipitaciones",
            "CoberturaNubes", "IndiceUV", "EsDeDia",
            ]
        # self.tabla_datos.setColumnWidth(1, 150)
        self.tabla_datos.setHorizontalHeaderLabels(encabezado)
        self.boton_actualizar_datos = PushButton(FIF.EDIT, "Recargar datos", self)
        self.boton_actualizar_datos.clicked.connect(self.add_lines_to_data_table_all_data)
        self.boton_actualizar_datos.setToolTip("Recarga la tabla de datos, deshace los filtros")
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
    def menu_general(self, event) -> None:
        """ Despliega un menu al hacer click derecho en la
        aplicación
        """
        menu = RoundMenu(parent=self)
        accion_cambiar_usuario = Action(FIF.UPDATE, "Cambiar usuario", shortcut="Ctrl+U")
        menu.addAction(accion_cambiar_usuario)
        menu.addSeparator()
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)
        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)
    def lanzar_filtro_ciudad(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por ciudad
        """
        self.dialogo_filtrar_ciudad = MessageBoxFiltrar(
            parent=self, lista_ciudades=self.lista_ciudades
            )
        self.dialogo_filtrar_ciudad.accepted.connect(self.filtrar_por_ciudad_func)
        self.dialogo_filtrar_ciudad.exec()
    def filtrar_por_ciudad_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por ciudad
        """
        ciudad = self.dialogo_filtrar_ciudad.ciudad_a_filtrar.currentText()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        if ciudad != "Todas las ciudades":
            df_maestro = df_maestro.loc[df_maestro["ciudad"] == ciudad]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_fecha(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por fecha
        """
        self.dialogo_filtrar_fecha = MessageBoxFiltrarPorFecha(parent=self)
        self.dialogo_filtrar_fecha.accepted.connect(self.filtrar_por_fecha_func)
        self.dialogo_filtrar_fecha.exec()
    def filtrar_por_fecha_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por fecha
        """
        fecha_minima = self.dialogo_filtrar_fecha.fecha_minima_filtrar.getDate()
        fecha_minima = fecha_minima.toString("yyyy-MM-dd")
        fecha_minima = datetime.strptime(fecha_minima, "%Y-%m-%d")
        fecha_maxima = self.dialogo_filtrar_fecha.fecha_maxima_filtrar.getDate()
        fecha_maxima = fecha_maxima.toString("yyyy-MM-dd")
        fecha_maxima = datetime.strptime(fecha_maxima, "%Y-%m-%d")
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["fecha"] >= fecha_minima) & (df_maestro["fecha"] <= fecha_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_temperatura(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por temperatura
        """
        self.dialogo_filtrar_temperatura = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Temperatura",
            valor_minimo=200,
            valor_maximo=200,
            valor1=3,
            valor2=15
            )
        self.dialogo_filtrar_temperatura.accepted.connect(self.filtrar_por_temperatura_func)
        self.dialogo_filtrar_temperatura.exec()
    def filtrar_por_temperatura_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por temperatura
        """
        temperatura_minima = \
            self.dialogo_filtrar_temperatura.valor_minima_filtrar.value()
        temperatura_maxima = \
            self.dialogo_filtrar_temperatura.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["temperatura"] >= temperatura_minima) \
            & (df_maestro["temperatura"] <= temperatura_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_humedad(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por humedad
        """
        self.dialogo_filtrar_humedad = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Humedad",
            valor_minimo=100,
            valor_maximo=100,
            valor1=80,
            valor2=90
            )
        self.dialogo_filtrar_humedad.accepted.connect(self.filtrar_por_humedad_func)
        self.dialogo_filtrar_humedad.exec()
    def filtrar_por_humedad_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por humedad
        """
        humedad_minima = \
            self.dialogo_filtrar_humedad.valor_minima_filtrar.value()
        humedad_maxima = \
            self.dialogo_filtrar_humedad.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["humedad"] >= humedad_minima) & (df_maestro["humedad"] <= humedad_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_presion(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por presion
        """
        self.dialogo_filtrar_presion = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Presión",
            valor_minimo=2000,
            valor_maximo=2000,
            valor1=1008,
            valor2=1025
            )
        self.dialogo_filtrar_presion.accepted.connect(self.filtrar_por_presion_func)
        self.dialogo_filtrar_presion.exec()
    def filtrar_por_presion_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por presión
        """
        presion_minima = \
            self.dialogo_filtrar_presion.valor_minima_filtrar.value()
        presion_maxima = \
            self.dialogo_filtrar_presion.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["presion"] >= presion_minima) & (df_maestro["presion"] <= presion_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_wind_speed(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por velocidad del viento
        """
        self.dialogo_filtrar_wind_speed = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Velocidad del viento",
            valor_minimo=200,
            valor_maximo=200,
            valor1=0,
            valor2=100
            )
        self.dialogo_filtrar_wind_speed.accepted.connect(self.filtrar_por_wind_speed_func)
        self.dialogo_filtrar_wind_speed.exec()
    def filtrar_por_wind_speed_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por velocidad del viento
        """
        wind_speed_minima = \
            self.dialogo_filtrar_wind_speed.valor_minima_filtrar.value()
        wind_speed_maxima = \
            self.dialogo_filtrar_wind_speed.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["wind_speed"] >= wind_speed_minima) \
            & (df_maestro["wind_speed"] <= wind_speed_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_wind_degree(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por grados del viento
        """
        self.dialogo_filtrar_wind_degree = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Ángulo del viente",
            valor_minimo=360,
            valor_maximo=360,
            valor1=0,
            valor2=180
            )
        self.dialogo_filtrar_wind_degree.accepted.connect(self.filtrar_por_wind_degree_func)
        self.dialogo_filtrar_wind_degree.exec()
    def filtrar_por_wind_degree_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por grados del viento
        """
        wind_degree_minima = \
            self.dialogo_filtrar_wind_degree.valor_minima_filtrar.value()
        wind_degree_maxima = \
            self.dialogo_filtrar_wind_degree.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["wind_degree"] >= wind_degree_minima) \
            & (df_maestro["wind_degree"] <= wind_degree_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_precip(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por precipitaciones
        """
        self.dialogo_filtrar_precip = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Precipitaciones",
            valor_minimo=200,
            valor_maximo=200,
            valor1=0,
            valor2=100
            )
        self.dialogo_filtrar_precip.accepted.connect(self.filtrar_por_precip_func)
        self.dialogo_filtrar_precip.exec()
    def filtrar_por_precip_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por precipitaciones
        """
        precip_minima = \
            self.dialogo_filtrar_precip.valor_minima_filtrar.value()
        precip_maxima = \
            self.dialogo_filtrar_precip.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["precip"] >= precip_minima) & (df_maestro["precip"] <= precip_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_cloudcover(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por cobertura del cielo
        """
        self.dialogo_filtrar_cloudcover = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Cobertura de nubes",
            valor_minimo=100,
            valor_maximo=100,
            valor1=50,
            valor2=100
            )
        self.dialogo_filtrar_cloudcover.accepted.connect(self.filtrar_por_cloudcover_func)
        self.dialogo_filtrar_cloudcover.exec()
    def filtrar_por_cloudcover_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por cobertura del cielo
        """
        cloudcover_minima = \
            self.dialogo_filtrar_cloudcover.valor_minima_filtrar.value()
        cloudcover_maxima = \
            self.dialogo_filtrar_cloudcover.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["cloudcover"] >= cloudcover_minima) \
            & (df_maestro["cloudcover"] <= cloudcover_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_uv_index(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por indice UV
        """
        self.dialogo_filtrar_uv_index = MessageBoxFiltrarEntreDosValoresSpinBox(
            parent=self,
            valor_variable="Índice UV",
            valor_minimo=100,
            valor_maximo=100,
            valor1=2,
            valor2=5
            )
        self.dialogo_filtrar_uv_index.accepted.connect(self.filtrar_por_uv_index_func)
        self.dialogo_filtrar_uv_index.exec()
    def filtrar_por_uv_index_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por indice UV
        """
        uv_index_minima = \
            self.dialogo_filtrar_uv_index.valor_minima_filtrar.value()
        uv_index_maxima = \
            self.dialogo_filtrar_uv_index.valor_maxima_filtrar.value()
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["uv_index"] >= uv_index_minima) \
            & (df_maestro["uv_index"] <= uv_index_maxima)
            ]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanzar_filtro_is_day(self) -> None:
        """ Ejecuta el proceso para filtrar la tabla de datos
        por si es dia o no
        """
        self.dialogo_filtrar_is_day = MessageBoxFiltrarDiaNoche(parent=self)
        self.dialogo_filtrar_is_day.accepted.connect(self.filtrar_por_is_day_func)
        self.dialogo_filtrar_is_day.exec()
    def filtrar_por_is_day_func(self) -> None:
        """ Ejecuta la lógica del proceso de filtrado
        de la tabla por si es dia o no
        """
        is_day_value = \
            self.dialogo_filtrar_is_day.valor_filtrar.currentText()
        if is_day_value == "No":
            is_day_value = 0
        else:
            is_day_value = 1
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = self.df_actual_filtrado
        df_maestro = df_maestro.loc[
            (df_maestro["is_day"] == is_day_value)
            | (df_maestro["is_day"] == str(is_day_value))]
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        # filtar numero de horas entre datos
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.df_actual_filtrado = df_maestro
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def lanza_export_excel(self) -> None:
        """ Lanza el proceso de exportación de la tabla a excel
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo excel",
            "",
            "Archivos excel (*.xlsx);;All Files (*)", options=options)
        if file_path:
            if not file_path.endswith(".xlsx") and not "." in file_path:
                new_file_path = file_path + ".xlsx"
            else:
                new_file_path = file_path
            df_maestro = self.df_actual_filtrado
            df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
            try:
                df_maestro.to_excel(new_file_path, index=False)
            except Exception:
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
    def menu_modificar_datos(self, event) -> None:
        """ Crea un menu especial para el widget de la tabla
        de datos con opciones custom
        """
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
        accion_filtrar_por_fecha.triggered.connect(self.lanzar_filtro_fecha)
        accion_filtrar_por_temperatura = Action(FIF.VIDEO, 'Por temperatura')
        accion_filtrar_por_temperatura.triggered.connect(self.lanzar_filtro_temperatura)
        accion_filtrar_por_humedad = Action(FIF.VIDEO, 'Por humedad')
        accion_filtrar_por_humedad.triggered.connect(self.lanzar_filtro_humedad)
        accion_filtrar_por_presion = Action(FIF.VIDEO, 'Por presion')
        accion_filtrar_por_presion.triggered.connect(self.lanzar_filtro_presion)
        accion_filtrar_por_wind_speed = Action(FIF.VIDEO, 'Velocidad del viento')
        accion_filtrar_por_wind_speed.triggered.connect(self.lanzar_filtro_wind_speed)
        accion_filtrar_por_wind_degree = Action(FIF.VIDEO, 'Inclinación del viento')
        accion_filtrar_por_wind_degree.triggered.connect(self.lanzar_filtro_wind_degree)
        accion_filtrar_por_precip = Action(FIF.VIDEO, 'Por precipitaciones')
        accion_filtrar_por_precip.triggered.connect(self.lanzar_filtro_precip)
        accion_filtrar_por_cloudcover = Action(FIF.VIDEO, 'Por cobertura del cielo')
        accion_filtrar_por_cloudcover.triggered.connect(self.lanzar_filtro_cloudcover)
        accion_filtrar_por_indice_uv = Action(FIF.VIDEO, 'Por indice UV')
        accion_filtrar_por_indice_uv.triggered.connect(self.lanzar_filtro_uv_index)
        accion_filtrar_por_is_day = Action(FIF.VIDEO, 'Por dia/noche')
        accion_filtrar_por_is_day.triggered.connect(self.lanzar_filtro_is_day)
        submenu.addActions([
            accion_filtrar_por_ciudad,
            accion_filtrar_por_fecha,
            accion_filtrar_por_temperatura,
            accion_filtrar_por_humedad,
            accion_filtrar_por_presion,
            accion_filtrar_por_wind_speed,
            accion_filtrar_por_wind_degree,
            accion_filtrar_por_precip,
            accion_filtrar_por_cloudcover,
            accion_filtrar_por_indice_uv,
            accion_filtrar_por_is_day,
        ])
        menu.addMenu(submenu)
        menu.addSeparator()
        menu.addAction(Action('Por añadir: REVISAR'))
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
    def on_whell_event(self, event, scroll_area) -> None:
        """ Desplaza la aplicación verticalmente al
        usar la rueda del mouse
        """
        delta = event.angleDelta().y()
        delta = int(scroll_area.verticalScrollBar().value() - delta / 3)
        scroll_area.verticalScrollBar().setValue(delta)
    def add_lines_to_data_table_success(self) -> None:
        """ Lanza un aviso al terminar de actualizar la
        tabla de datos
        """
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
    def add_lines_to_data_table_all_data(self) -> None:
        """ Función encargada de solicitar los
        datos de la API y mostralos en la QTable
        """
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = pd.DataFrame()
        self.obtain_data()
        self.create_df_from_data()
        df = self.df_actual
        self.df_actual_filtrado = self.df_actual
        df_maestro = pd.concat([df_maestro, df])
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        numero_horas_entre_datos = self.spin_box_horas_entre_datos.value()
        df_maestro = self.filtrar_df_datos(df_maestro, numero_horas_entre_datos)
        self.add_lines_to_data_table_func(df_maestro)
        self.boton_actualizar_datos.setEnabled(True)
    def add_lines_to_data_table_func(self, df_maestro: pd.DataFrame) -> None:
        """ Ejecuta la lógica para añadir lineas a la tabla de datos
        """
        for _, row in df_maestro.iterrows():
            lineas_actuales = self.tabla_datos.rowCount()
            self.tabla_datos.setRowCount(lineas_actuales + 1)
            ciudad = row["ciudad"]
            fecha = row["fecha"]
            fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
            temperatura = str(row["temperatura"])
            humedad = str(row["humedad"])
            presion = str(row["presion"])
            wind_speed = str(row["wind_speed"])
            wind_degree = str(row["wind_degree"])
            precip = str(row["precip"])
            cloudcover = str(row["cloudcover"])
            uv_index = str(row["uv_index"])
            is_day = str(row["is_day"])
            if is_day == 0 or is_day == "0":
                is_day = "No"
            else:
                is_day = "Si"
            tupla_datos = (
                    ciudad, fecha, temperatura, humedad, presion,
                    wind_speed, wind_degree, precip,
                    cloudcover, uv_index, is_day
                    )
            for i, el in enumerate(tupla_datos):
                element = QTableWidgetItem(el)
                self.tabla_datos.setItem(lineas_actuales, i, element)
        self.tabla_datos.resizeColumnsToContents()
        self.add_lines_to_data_table_success()
    def filtrar_df_datos(self, df: pd.DataFrame,
        numero_horas_entre_datos: int) -> pd.DataFrame:
        """ Modifica el df de datos y selecciona los datos
        para que tengan una separación concreta de horas entre
        cada consecutivo siempre que sean de la misma ciudad
        """
        lista_fechas = []
        lista_temperaturas = []
        lista_humedades = []
        lista_presiones = []
        lista_ciudades = []
        lista_wind_speed = []
        lista_wind_degree = []
        lista_precip = []
        lista_cloudcover = []
        lista_uv_index = []
        lista_is_day = []
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
                lista_wind_speed.append(fila["wind_speed"])
                lista_wind_degree.append(fila["wind_degree"])
                lista_precip.append(fila["precip"])
                lista_cloudcover.append(fila["cloudcover"])
                lista_uv_index.append(fila["uv_index"])
                lista_is_day.append(fila["is_day"])
            else:
                if tomar_siguiente_dato:
                    minimum_date = fila["fecha"]
                    tomar_siguiente_dato = False
                if df.iloc[indice - 1]["ciudad"] == fila["ciudad"]:
                    condition = (
                        (fila["fecha"] - minimum_date).total_seconds() / 3600
                        ) >= numero_horas_entre_datos
                    if condition:
                        lista_fechas.append(fila["fecha"])
                        lista_temperaturas.append(fila["temperatura"])
                        lista_humedades.append(fila["humedad"])
                        lista_presiones.append(fila["presion"])
                        lista_ciudades.append(fila["ciudad"])
                        lista_wind_speed.append(fila["wind_speed"])
                        lista_wind_degree.append(fila["wind_degree"])
                        lista_precip.append(fila["precip"])
                        lista_cloudcover.append(fila["cloudcover"])
                        lista_uv_index.append(fila["uv_index"])
                        lista_is_day.append(fila["is_day"])
                        tomar_siguiente_dato = True
                    else:
                        pass
                else:
                    lista_fechas.append(fila["fecha"])
                    lista_temperaturas.append(fila["temperatura"])
                    lista_humedades.append(fila["humedad"])
                    lista_presiones.append(fila["presion"])
                    lista_ciudades.append(fila["ciudad"])
                    lista_wind_speed.append(fila["wind_speed"])
                    lista_wind_degree.append(fila["wind_degree"])
                    lista_precip.append(fila["precip"])
                    lista_cloudcover.append(fila["cloudcover"])
                    lista_uv_index.append(fila["uv_index"])
                    lista_is_day.append(fila["is_day"])
                    tomar_siguiente_dato = True
        data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones,
            "ciudad" : lista_ciudades,
            "wind_speed" : lista_wind_speed,
            "wind_degree" : lista_wind_degree,
            "precip" : lista_precip,
            "cloudcover" : lista_cloudcover,
            "uv_index" : lista_uv_index,
            "is_day" : lista_is_day,
            }
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values(
            by=["ciudad", "fecha"],
            ascending=False
            )
        df.reset_index(drop=True, inplace=True)
        return df
    def modify_graph_target_to_resize(self) -> None:
        """ Cambia el valor del slider al cambiar
        el grafico que se quiere modificar en
        el desplegable para que no se auto modifique el
        grafico al cambiar el combobox
        """
        grupo_objetivo = self.grafico_combobox.currentText()
        for group in self.lista_grupos_graficos:
            if group.title() == grupo_objetivo:
                width = group.width()
                height = group.height()
                valor_slider_width = 100 - int((width - 250) * 100 / 1000)
                valor_slider_height = 100 - int((height - 250) * 100 / 1000)
                self.slider_width.setValue(valor_slider_width)
                self.slider_height.setValue(valor_slider_height)
    def modify_graph_size(self) -> None:
        """ Cambia el tamaño de los gráficos al mover el
        slider
        """
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
    def anadir_grafico_func(self) -> None:
        """ Ejecuta la lógica para añadir un nuevo grafico
        al pulsar el boton de añadir graph
        """
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
    def volver_a_desplegar_graficos(self) -> None:
        """ Vuelve a renderizar los graficos al
        añadir o eliminar uno
        """
        self.flow_layout_graficos_widget.removeAllWidgets()
        for group in self.lista_grupos_graficos:
            self.flow_layout_graficos_widget.addWidget(group)
    def eliminar_grafico(self) -> None:
        """Elimina de la lista un grafico según el graph que esté
        seleccionado en el combobox de eliminar graficos.
        Vuelve a renderizar el combobox de graficos y los despliega de nuevo
        """
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
    def renombrar_grupos(self) -> None:
        """ Vuelve a renombrar los gráficos cuando un
        grafico es eliminado o añadido
        """
        new_list = []
        for index, group in enumerate(self.lista_grupos_graficos):
            partes_titulo = group.title().split(":")
            parte1 = partes_titulo[0][: -1]
            if len(parte1) == 9:
                parte1 = parte1[: -1]
            parte1 = parte1 + str(index + 1) + ":"
            new_title = parte1 + partes_titulo[1]
            group.setTitle(new_title)
            new_list.append(group)
        self.lista_grupos_graficos = new_list
    def read_data_from_db(self) -> None:
        """ Llama a la funcion encargada de
        obtener los datos de la db, luego a la
        que genera un DataFrame de pandas y
        por ultimo a la funcion de generar la plotly fig
        """
        self.obtain_data()
        self.create_df_from_data()
        self.add_lines_to_data_table_success()
    def showEvent(self, event) -> None:
        pass
        """if self.primer_arranque:
            self.execute_initial_code()
            self.primer_arranque = False"""
    def execute_initial_code(self) -> None:
        """ Ejecuta el codigo inicial cuando
        un usuario se identifica al abrir la app
        """
        self.read_data_from_db()
        self.create_initial_figures()
        self.add_lines_to_data_table_all_data()
    def create_initial_figures(self) -> None:
        """ Crea las 3 primeras figuras que se muestran al abrir la app
        """
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
    def obtain_data(self) -> None:
        # NOTA: Se obtienen los datos para los graphs y
        # para la tabla, ¿debería obtenerse solo una vez?
        """ Lee la ciudad seleccionada en la combobox
        de la tab de visualizar graficos
        y obtiene los datos de la db asociados a esa ciudad
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db())
    async def retrieve_data_from_db(self) -> None:
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
    def create_df_from_data(self) -> None:
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
        lista_wind_speed = []
        lista_wind_degree = []
        lista_precip = []
        lista_cloudcover = []
        lista_uv_index = []
        lista_is_day = []
        datos = self.db_data
        for element in datos:
            try:
                if "temperature" in element["current"].keys():
                    # WeatherStack API
                    fecha = element["location"]["localtime"]
                    temperatura = element["current"]["temperature"]
                    humedad = element["current"]["humidity"]
                    presion = element["current"]["pressure"]
                    ciudad = element["location"]["name"]
                    wind_speed = element["current"]["wind_speed"]
                    wind_degree = element["current"]["wind_degree"]
                    precip = element["current"]["precip"]
                    cloudcover = element["current"]["cloudcover"]
                    uv_index = element["current"]["uv_index"]
                    is_day = element["current"]["is_day"]
                    if is_day == "no":
                        is_day = 0
                    else:
                        is_day = 1
                else:
                    # WeatherAPI
                    fecha = element["location"]["localtime"]
                    temperatura = element["current"]["temp_c"]
                    humedad = element["current"]["humidity"]
                    presion = element["current"]["pressure_mb"]
                    ciudad = element["location"]["name"]
                    wind_speed = element["current"]["wind_kph"]
                    wind_degree = element["current"]["wind_degree"]
                    precip = element["current"]["precip_mm"]
                    cloudcover = element["current"]["cloud"]
                    uv_index = element["current"]["uv"]
                    is_day = element["current"]["is_day"]
                lista_fechas.append(fecha)
                lista_temperaturas.append(temperatura)
                lista_humedades.append(humedad)
                lista_presiones.append(presion)
                lista_ciudades.append(ciudad)
                lista_wind_speed.append(wind_speed)
                lista_wind_degree.append(wind_degree)
                lista_precip.append(precip)
                lista_cloudcover.append(cloudcover)
                lista_uv_index.append(uv_index)
                lista_is_day.append(is_day)
            except KeyError:
                print("error")
                print(element)
        dict_data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones,
            "ciudad" : lista_ciudades,
            "wind_speed" : lista_wind_speed,
            "wind_degree" : lista_wind_degree,
            "precip" : lista_precip,
            "cloudcover" : lista_cloudcover,
            "uv_index" : lista_uv_index,
            "is_day" : lista_is_day,
            }
        df = pd.DataFrame(dict_data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        self.df_actual = df
    def create_figure(self, ciudad: str, valor: str) -> plt.Figure:
        """ Ejecuta la lógica para añadir una nueva figura a la app
        """
        datos = self.df_actual
        datos = datos.loc[datos["ciudad"] == ciudad]
        if valor == "Temperatura":
            valor2 = "temperatura"
        elif valor == "Humedad":
            valor2 = "humedad"
        elif valor == "Presion":
            valor2 = "presion"
        elif valor == "VelocidadViento":
            valor2 = "wind_speed"
        elif valor == "GradosViento":
            valor2 = "wind_degree"
        elif valor == "Precipitaciones":
            valor2 = "precip"
        elif valor == "CoberturaNubes":
            valor2 = "cloudcover"
        elif valor == "IndiceUV":
            valor2 = "uv_index"
        elif valor == "EsDeDia":
            valor2 = "is_day"
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
    def mostrar_explicacion_datos(self) -> None:
        """ Muestra una explicación sobre los gráficos
        cuando se pulsa el boton en la app
        """
        content = """
            Los siguientes graficos muestran los datos
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
    def on_canvas_click(self, event) -> None:
        print("clickc")
class MessageBoxFiltrar(MessageBoxBase):
    """ Abre un dialogo para filtrar la tabla de
    datos por ciudad
    """
    def __init__(self, parent=None, lista_ciudades: List[str]=None):
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
class MessageBoxFiltrarPorFecha(MessageBoxBase):
    """ Abre un dialogo para filtrar la tabla de
    datos por fecha
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titulo = SubtitleLabel("Filtrado de los datos", self)
        self.fecha_minima = BodyLabel("Desde fecha")
        self.fecha_minima_filtrar = CalendarPicker()
        self.fecha_minima_filtrar.setDate(QDate(2023, 12, 30))
        self.fecha_minima_filtrar.setDateFormat("dd-MM-yyyy")
        self.fecha_maxima = BodyLabel("Hasta fecha")
        self.fecha_maxima_filtrar = CalendarPicker()
        self.fecha_maxima_filtrar.setDate(QDate(2024, 2, 10))
        self.fecha_maxima_filtrar.setDateFormat("dd-MM-yyyy")
        self.viewLayout.addWidget(self.titulo)
        self.viewLayout.addWidget(self.fecha_minima)
        self.viewLayout.addWidget(self.fecha_minima_filtrar)
        self.viewLayout.addWidget(self.fecha_maxima)
        self.viewLayout.addWidget(self.fecha_maxima_filtrar)
        self.yesButton.setText('Aceptar')
        self.cancelButton.setText('Cancelar')
        self.widget.setMinimumWidth(350)
class MessageBoxFiltrarEntreDosValoresSpinBox(MessageBoxBase):
    def __init__(self, parent=None, valor_variable: str="Temperatura",
                 valor_minimo=100, valor_maximo=100,
                 valor1=0, valor2=100):
        """ Abre un dialogo para filtrar la tabla de
        datos una variable entre dos valores
        """
        super().__init__(parent)
        self.titulo = SubtitleLabel("Filtrado de los datos", self)
        self.valor_minima = BodyLabel(f"{valor_variable} mínima")
        self.valor_minima_filtrar = SpinBox(self)
        self.valor_minima_filtrar.setMaximum(valor_minimo)
        self.valor_minima_filtrar.setValue(valor1)
        self.valor_maxima = BodyLabel(f"{valor_variable} máxima")
        self.valor_maxima_filtrar = SpinBox(self)
        self.valor_maxima_filtrar.setMaximum(valor_maximo)
        self.valor_maxima_filtrar.setValue(valor2)
        self.viewLayout.addWidget(self.titulo)
        self.viewLayout.addWidget(self.valor_minima)
        self.viewLayout.addWidget(self.valor_minima_filtrar)
        self.viewLayout.addWidget(self.valor_maxima)
        self.viewLayout.addWidget(self.valor_maxima_filtrar)
        self.yesButton.setText('Aceptar')
        self.cancelButton.setText('Cancelar')
        self.widget.setMinimumWidth(350)
class MessageBoxFiltrarDiaNoche(MessageBoxBase):
    """ Abre un dialogo para filtrar la tabla de
    datos por si es de dia o no
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titulo = SubtitleLabel("Filtrado de los datos", self)
        self.valor_titulo = BodyLabel("Es de día:")
        self.valor_filtrar = ComboBox(self)
        self.valor_filtrar.addItem("No")
        self.valor_filtrar.addItem("Si")
        self.viewLayout.addWidget(self.titulo)
        self.viewLayout.addWidget(self.valor_titulo)
        self.viewLayout.addWidget(self.valor_filtrar)
        self.yesButton.setText('Aceptar')
        self.cancelButton.setText('Cancelar')
        self.widget.setMinimumWidth(350)
