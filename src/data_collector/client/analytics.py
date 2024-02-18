#!/usr/bin/env python
""" Analytics widget, contiene varias tabs
en los que se muestran los graficos de datos,
su analisis y los forecast predictivos (future feature)
"""
import json
import asyncio
import pickle
import websockets

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QStackedWidget

from PyQt5.QtCore import Qt

from qfluentwidgets import SmoothScrollArea
from qfluentwidgets import Flyout
from qfluentwidgets import FlyoutAnimationType
from qfluentwidgets import Action
from qfluentwidgets import CommandBar
from qfluentwidgets import TransparentDropDownPushButton
from qfluentwidgets import RoundMenu
from qfluentwidgets import MenuAnimationType
from qfluentwidgets import CommandBarView
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import setFont
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition
from qfluentwidgets import TransparentPushButton

import pandas as pd
from redis import asyncio as aioredis # CHANGE THIS
# CLIENT SHOULD NOT CONNECT TO REDDIS BUT SERVER INSTEAD

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from general_functions import open_webbrowser

#plt.style.use('seaborn-v0_8-darkgrid')

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


class AnalyticsWidget(QWidget):
    """ Define los elementos del widget de
    analytics y sus metodos asociados
    Incluye:
        - Visualización de los datos con matplotlib
        - Análisis de correlaciones
        - Análisis de distribución de los datos (proximamente)
        - Forecasting (proximamente)
        - Detección de outliers/clustering (proximamente)
    """
    def __init__(self, lista_ciudades):
        super().__init__()
        self.token = None
        self.server_ip = "localhost"
        self.setObjectName("AnalyticsWidget")
        self.lista_ciudades = lista_ciudades
        self.variables = ("temperatura", "humedad", "presion")
        self.contextMenuEvent = self.menu_general
        self.command_bar: CommandBar = None
        self.button_change_serie_unica: TransparentDropDownPushButton = None
        self.contenido_stackedwidget = QStackedWidget()
        self.datos_iniciales_scroll = QScrollArea()
    def menu_general(self, event):
        """ Despliega un menu al hacer click derecho en
        la aplicación
        """
        menu = RoundMenu(parent=self)
        accion_cambiar_usuario = Action(FIF.UPDATE, "Cambiar usuario", shortcut="Ctrl+U")
        menu.addAction(accion_cambiar_usuario)
        menu.addSeparator()
        accion_ayuda = Action(FIF.HELP, 'Help', shortcut='Ctrl+H')
        accion_ayuda.triggered.connect(open_webbrowser)
        menu.addAction(accion_ayuda)
        menu.exec(self.mapToGlobal(event.pos()), aniType=MenuAnimationType.DROP_DOWN)

    async def retrieve_data_from_db(self, ciudad: str):
        """ Lee los datos de la API que se encuentren
        almacenados en la db para una ciudad concreta
        """
        uri = f"ws://{self.server_ip}:8765"
        query = {"location.name" : ciudad}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)

        custom_message_size = 1024*1024*50
        async with websockets.connect(uri, max_size=custom_message_size) as websocket:
            try:
                await websocket.send(request)
                response = await websocket.recv()
                db_data = response
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
                db_data = {"autenticado" : False}
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
                db_data = {"autenticado" : False}
            finally:
                await websocket.close()
        return db_data
    def create_df_from_data(self, db_data) -> pd.DataFrame:
        """ Crea un df con los datos proporcionados
        por el metodo retrieve_data_from_db
        """
        lista_fechas = []
        lista_temperaturas = []
        lista_humedades = []
        lista_presiones = []
        for element in db_data:
            if "temperature" in element["current"].keys():
                fecha = element["location"]["localtime"]
                temperatura = element["current"]["temperature"]
                humedad = element["current"]["humidity"]
                presion = element["current"]["pressure"]
            else:
                fecha = element["location"]["localtime"]
                temperatura = element["current"]["temp_c"]
                humedad = element["current"]["humidity"]
                presion = element["current"]["pressure_mb"]
                # ciudad = element["location"]["name"]
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
        return df
    async def comprobar_token(self):
        """ Comprueba que el token de jwt
        sea valido. Para ello hace una
        petición al servidor
        """
        uri = f"ws://{self.server_ip}:8765"
        token = {"token" : self.token}
        request = {"tipo_request" : "comprobar_token", "value" : token}
        request = json.dumps(request)
        async with websockets.connect(uri) as websocket:
            try:
                await websocket.send(request)
                response = await websocket.recv()
                response = json.loads(response)
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
        return response["autenticado"]

    async def read_data_from_db(self):
        """ Lanza la lectura de datos de la db
        para las tres ciudades, la creacion de los
        DataFrames de pandas.
        Almacena los 3 dfs en una lista
        """
        response = await self.comprobar_token()
        if response:
            lista_db_data = []
            lista_dfs = []
            for ciudad in self.lista_ciudades:
                append = await self.retrieve_data_from_db(ciudad)
                if not isinstance(append, dict):
                    append = json.loads(append)
                    append = append["data"]
                    lista_db_data.append(append)
            for db_data, ciudad in zip(lista_db_data, self.lista_ciudades):
                df = self.create_df_from_data(db_data)
                df["ciudad"] = ciudad
                df["fecha"] = pd.to_datetime(df["fecha"])
                lista_dfs.append(df)
            for index, df in enumerate(lista_dfs):
                df.set_index("fecha", inplace=True)
                lista_dfs[index] = df
            lista_dfs_datos = []
            for index, df in enumerate(lista_dfs):
                df = df[["temperatura", "humedad", "presion"]]
                lista_dfs_datos.append(df)
            for index, df in enumerate(lista_dfs_datos):
                df_resampled = df.resample("4H", closed="left", label="right").mean()
                df_resampled = df_resampled.fillna(method='ffill')
                self.lista_dfs_resampled.append(df_resampled)
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
    def on_graph_click(self, event):
        """ Despliega un menu al hacer click en un grafico
        para poder exportarlo como imagen y otras opciones
        """
        if event.inaxes:
            view = CommandBarView(self)
        view.addAction(Action(FIF.SHARE, 'Share'))
        view.addAction(Action(FIF.SAVE, 'Save', triggered=self.save_fig))
        view.addAction(Action(FIF.DELETE, 'Delete'))

        view.addHiddenAction(Action(FIF.APPLICATION, 'App', shortcut='Ctrl+A'))
        view.addHiddenAction(Action(FIF.SETTING, 'Settings', shortcut='Ctrl+S'))
        view.resizeToSuitableWidth()

        Flyout.make(view, self.datos_iniciales_scroll, self, FlyoutAnimationType.FADE_IN)
    def save_fig(self):
        """ Ejecuta la exportación del grafico a un
        archivo png en el menu que se lanza al hacer click en
        un grafico y seleccionar esa opcion en el
        menu que se despliega
        """
        pass # CONTINUAR AQUI
    def switch_to_datos_iniciales(self):
        """ Cambia el stacked widget a datos iniciales
        """
        self.contenido_stackedwidget.setCurrentIndex(0)
    def switch_to_correlaciones(self):
        """ Cambia el stacked widget a correlaciones
        """
        self.contenido_stackedwidget.setCurrentIndex(1)
    def switch_to_distribucion(self):
        """ Cambia el stacked widget a distribución
        de los datos
        """
        self.contenido_stackedwidget.setCurrentIndex(2)
    def switch_to_serie_unica_forecasting(self):
        """ Cambia el stacked widget a forecasting
        """
        self.contenido_stackedwidget.setCurrentIndex(3)
        self.button_change_serie_unica.setText("Forecasting Serie Unica")
    def switch_to_serie_unica_backtesting(self):
        """ Cambia el stacked widget a backtesting
        """
        self.contenido_stackedwidget.setCurrentIndex(4)
        self.button_change_serie_unica.setText("Backtesting de serie unica")
    def switch_to_serie_unica_forecasting_ciclicas(self):
        """ Cambia el stacked widget a forecasting con variables ciclicas
        """
        self.contenido_stackedwidget.setCurrentIndex(5)
        self.button_change_serie_unica.setText("Forecasting con variables cíclicas")
    def switch_to_serie_unica_backtesting_ciclicas(self):
        """ Cambia el stacked widget a backtesting con variables ciclicas
        """
        self.contenido_stackedwidget.setCurrentIndex(6)
        self.button_change_serie_unica.setText("Backtesting con variables cíclicas")
    def switch_to_serie_unica_forecast_multi(self):
        """ Cambia el stacked widget a forecasting multiseries
        """
        self.contenido_stackedwidget.setCurrentIndex(7)
    async def leer_de_redis_lista(self, key):
        """ Lee datos de la base de datos redis
        WARNING: THIS WILL BE DEPRECATED, CLIENT SHOULD ONLY CONNECT
        WITH WEBSOCKETS SERVER
        """
        redis = await aioredis.from_url("redis://localhost:6379")
        lista_datos = await redis.lrange(key, 0, -1)
        await redis.aclose()
        return lista_datos
    def create_figure(self):
        """ Crea el layout de las tabs que
        contiene este widget.
        Al instanciarse este widget, se leen los datoss
        y se guardan como un atributo de tipo lista que
        contiene los DataFrames de datos resampleados
        Cada elemento de esa lista
        Contiene:
            Tab 'Datos iniciales':
                Tres figuras, cada una con la evolucion
                de la temperatura, presion y humedad en
                las tres ciudades
                Estructura:
                QscrollArea
                    Qwidget
                        QGroupBox (x3)
                            QFigureCanvas
            Tab 'Correlaciones':
                Tres graficos de correlaciones (plot_acf)
                cada uno para cada ciudad
                Cada gráfico contiene las correlaciones
                de temperatura, humedad y presión
                Estructura:
                QscrollArea
                    Qwidget
                        QGroupBox (x3)
                            QFigureCanvas
            Tab 'Distribución de los datos':
                Proximamente
            Tab "Forecasting serie unica":
                Estructura:
                SubTab "Forecasting serie única"
                    QScrollArea
                        QWidget
                            Qgroup (x3)
                                QFigureCanvas
                SubTab "Forecasting serie única"
                    QScrollArea
                        QWidget
                            Qgroup (x3)
                                QFigureCanvas
            Tab 'Forecasting multiseries':
        """

        # NOTA: sustituye la tab aqui por el command bar con qstackedwidget ¿+scroll?
        # y ponle el wheel event para el scrol

        self.command_bar = CommandBar(self)
        boton_datos_iniciales = TransparentPushButton('Datos iniciales', self, FIF.HOME)
        boton_datos_iniciales.setFixedHeight(34)
        boton_datos_iniciales.setFixedWidth(250)
        boton_datos_iniciales.clicked.connect(self.switch_to_datos_iniciales)
        self.command_bar.addWidget(boton_datos_iniciales)
        boton_correlaciones = TransparentPushButton('Correlaciones', self, FIF.DOCUMENT)
        boton_correlaciones.setFixedHeight(34)
        boton_correlaciones.setFixedWidth(250)
        boton_correlaciones.clicked.connect(self.switch_to_correlaciones)
        self.command_bar.addWidget(boton_correlaciones)

        distribucion_action = Action(FIF.ALIGNMENT, "Distribución de los datos", self)
        distribucion_action.triggered.connect(self.switch_to_distribucion)
        self.command_bar.addAction(distribucion_action)
        self.command_bar.addSeparator()
        self.button_change_serie_unica = TransparentDropDownPushButton(
            'Forecasting Serie Unica', self, FIF.MENU
            )
        self.button_change_serie_unica.setFixedHeight(34)
        self.button_change_serie_unica.setFixedWidth(250)
        setFont(self.button_change_serie_unica, 12)
        menu = RoundMenu(parent=self)
        forecasting_serie_unica_action = Action(FIF.COPY, 'Forecasting de serie unica')
        forecasting_serie_unica_action.triggered.connect(self.switch_to_serie_unica_forecasting)
        backtest_serie_unica_action = Action(FIF.CUT, 'Backtesting de serie unica')
        backtest_serie_unica_action.triggered.connect(self.switch_to_serie_unica_backtesting)
        forecasting_serie_unica__cic_action = Action(
            FIF.PASTE, 'Forecasting con variables cíclicas'
            )
        forecasting_serie_unica__cic_action.triggered.connect(
            self.switch_to_serie_unica_forecasting_ciclicas
            )
        backtest_serie_unica_cic_action = Action(
            FIF.CANCEL, 'Backtesting con variables cíclicas'
            )
        backtest_serie_unica_cic_action.triggered.connect(
            self.switch_to_serie_unica_backtesting_ciclicas
            )
        menu.addActions([
            forecasting_serie_unica_action,
            backtest_serie_unica_action,
            forecasting_serie_unica__cic_action,
            backtest_serie_unica_cic_action,
        ])
        self.button_change_serie_unica.setMenu(menu)
        self.command_bar.addWidget(self.button_change_serie_unica)
        forecast_multi_series_action = Action(
            FIF.SETTING, 'Forecasting multi series', shortcut='Ctrl+S'
            )
        forecast_multi_series_action.triggered.connect(self.switch_to_serie_unica_forecast_multi)
        self.command_bar.addSeparator()
        self.command_bar.addHiddenAction(forecast_multi_series_action)
        self.datos_iniciales_scroll.setWidgetResizable(True)
        datos_iniciales_widget = QWidget()
        self.datos_iniciales_scroll.setWidget(datos_iniciales_widget)
        self.contenido_stackedwidget.addWidget(self.datos_iniciales_scroll)
        layout_datos_iniciales_scroll = QVBoxLayout()
        layout_datos_iniciales_scroll.addWidget(datos_iniciales_widget)
        self.datos_iniciales_scroll.setLayout(layout_datos_iniciales_scroll)
        self.datos_iniciales_scroll.installEventFilter(self)
        correlaciones_scroll_area = SmoothScrollArea()
        correlaciones_widget = QWidget()
        correlaciones_scroll_area.setWidget(correlaciones_widget)
        correlaciones_scroll_area.setWidgetResizable(True)
        correlaciones_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.contenido_stackedwidget.addWidget(correlaciones_scroll_area)
        layout_general_scroll_detalle_corr = QVBoxLayout()
        layout_general_scroll_detalle_corr.addWidget(correlaciones_widget)
        correlaciones_scroll_area.setLayout(layout_general_scroll_detalle_corr)
        distribucion_datos_widget = QWidget()
        self.contenido_stackedwidget.addWidget(distribucion_datos_widget)
        layout_maestro = QVBoxLayout()
        layout_maestro.addWidget(self.command_bar)
        layout_maestro.addWidget(self.contenido_stackedwidget)
        self.setLayout(layout_maestro)
        layout_datos_iniciales = QVBoxLayout()
        loop = asyncio.get_event_loop()
        serialized_figures = loop.run_until_complete(self.leer_de_redis_lista("figuras_evolucion"))
        items = loop.run_until_complete(self.leer_de_redis_lista("items_figuras_evolucion"))
        list_fig = \
            [pickle.loads(ser_fig) for ser_fig in serialized_figures]
        for fig, item in zip(list_fig, items):
            evolucion_temp_canvas = FigureCanvas(fig)
            evolucion_temp_canvas.mpl_connect("button_press_event", self.on_graph_click)
            evolucion_temp_canvas.setFixedHeight(500)
            evolucion_temp_canvas.setContentsMargins(10, 60, 10, 10)
            evolucion_temp_canvas.setFocusPolicy(Qt.StrongFocus)
            evolucion_temp_canvas.wheelEvent = lambda event: self.on_whell_event(
                event, self.datos_iniciales_scroll
                )
            grupo_item = QGroupBox(item.decode('utf-8').capitalize())
            layout_grupo_item = QVBoxLayout()
            layout_grupo_item.addWidget(evolucion_temp_canvas)
            grupo_item.setLayout(layout_grupo_item)
            grupo_item.wheelEvent = lambda event: self.on_whell_event(
                event, self.datos_iniciales_scroll
                )
            layout_datos_iniciales.addWidget(grupo_item)
        datos_iniciales_widget.setLayout(layout_datos_iniciales)

        layout_detalle_corr = QVBoxLayout()
        lista_fig_correlaciones_ser = loop.run_until_complete(
            self.leer_de_redis_lista("figuras_correlaciones")
            )
        lista_fig_correlaciones = \
            [pickle.loads(ser_fig) for ser_fig in lista_fig_correlaciones_ser]
        for fig_corr, ciudad in zip(lista_fig_correlaciones, self.lista_ciudades):
            corr_canvas = FigureCanvas(fig_corr)
            corr_canvas.wheelEvent = lambda event: self.on_whell_event(
                event,
                correlaciones_scroll_area
                )
            corr_canvas.setFixedHeight(1500)
            grupo_corr = QGroupBox(f"Correlaciones en {ciudad.capitalize()}")
            layout_grupo_corr = QVBoxLayout()
            layout_grupo_corr.addWidget(corr_canvas)
            grupo_corr.setLayout(layout_grupo_corr)
            grupo_corr.wheelEvent = lambda event: self.on_whell_event(
                event,
                correlaciones_scroll_area
                )
            layout_detalle_corr.addWidget(grupo_corr)
        correlaciones_widget.setLayout(layout_detalle_corr)
        layout_distribucion_datos = QGridLayout()
        label_distribucion = QLabel("Proximamente")
        layout_distribucion_datos.addWidget(label_distribucion)
        distribucion_datos_widget.setLayout(layout_distribucion_datos)

        tab_forecasting_serie_unica_widget = QWidget()
        tab_forecasting_serie_unica_scroll = SmoothScrollArea()
        layout_forecasting_serie_unica_scroll = QVBoxLayout()
        layout_forecasting_serie_unica_scroll.addWidget(tab_forecasting_serie_unica_widget)
        tab_forecasting_serie_unica_scroll.setWidget(tab_forecasting_serie_unica_widget)
        tab_forecasting_serie_unica_scroll.setWidgetResizable(True)
        tab_forecasting_serie_unica_scroll.setLayout(layout_forecasting_serie_unica_scroll)
        self.contenido_stackedwidget.addWidget(tab_forecasting_serie_unica_scroll)
        msg = (
            "¡ATENCIÓN!",
            "Se ha utilizado el mismo modelo en todos los forecasters.",
            "Es necesario un fine-tunning para cada serie (próximamente)"
            )
        layout_tab_forecasting_serie_unica_widget = QVBoxLayout()
        tab_forecasting_serie_unica_widget.setLayout(layout_tab_forecasting_serie_unica_widget)
        lista_avisos = []
        for i, mensaje in enumerate(msg):
            lista_avisos.append(QLabel(mensaje))
        for i, aviso in enumerate(lista_avisos):
            aviso.setObjectName(f"aviso_forecast_unica_{i}")
            aviso.wheelEvent = lambda event: self.on_whell_event(
                event,
                tab_forecasting_serie_unica_scroll
                )
            layout_tab_forecasting_serie_unica_widget.addWidget(aviso)
            layout_tab_forecasting_serie_unica_widget.setAlignment(
                aviso,
                Qt.AlignCenter
                )
        lista_figuras_serie_unica_ser = loop.run_until_complete(
            self.leer_de_redis_lista("figuras_forecasting_serie_unica"
                ))
        lista_figuras_serie_unica = \
            [pickle.loads(ser_fig) for ser_fig in lista_figuras_serie_unica_ser]
        for fig, variable in zip(lista_figuras_serie_unica, self.variables):
            canvas_forecasting_serie_unica = FigureCanvas(fig)
            canvas_forecasting_serie_unica.wheelEvent = \
                lambda event: self.on_whell_event(event, tab_forecasting_serie_unica_scroll)
            canvas_forecasting_serie_unica.setFixedHeight(1150)
            forecasting_serie_unica_group = QGroupBox(variable.capitalize())
            forecasting_serie_unica_group.wheelEvent = \
                lambda event: self.on_whell_event(event, tab_forecasting_serie_unica_scroll)
            layout_forecasting_serie_unica_group = QVBoxLayout()
            layout_forecasting_serie_unica_group.addWidget(
                canvas_forecasting_serie_unica
                )
            forecasting_serie_unica_group.setLayout(layout_forecasting_serie_unica_group)
            layout_tab_forecasting_serie_unica_widget.addWidget(
                forecasting_serie_unica_group
                )
        backtesting_serie_unica_scroll = SmoothScrollArea()
        backtesting_serie_unica_widget = QWidget()
        backtesting_serie_unica_scroll.setWidgetResizable(True)
        backtesting_serie_unica_scroll.setWidget(backtesting_serie_unica_widget)
        layout_backtesting_serie_unica_scroll = QVBoxLayout()
        layout_backtesting_serie_unica_scroll.addWidget(backtesting_serie_unica_widget)
        backtesting_serie_unica_scroll.setLayout(layout_backtesting_serie_unica_scroll)
        self.contenido_stackedwidget.addWidget(backtesting_serie_unica_scroll)
        layout_backtesting_unica_widget = QVBoxLayout()
        backtesting_serie_unica_widget.setLayout(layout_backtesting_unica_widget)
        lista_figuras_backtest_unica_ser = loop.run_until_complete(
            self.leer_de_redis_lista("figuras_backtesting_serie_unica"
                ))
        lista_figuras_backtest_unica = \
            [pickle.loads(ser_fig) for ser_fig in lista_figuras_backtest_unica_ser]
        for fig, variable in zip(lista_figuras_backtest_unica, self.variables):
            grupo_backtesting_unica = QGroupBox(f"Backtesting de {variable}")
            grupo_backtesting_unica.wheelEvent = \
                lambda event: self.on_whell_event(
                    event, backtesting_serie_unica_scroll
                    )
            layout_grupo_backtest_unica = QVBoxLayout()
            grupo_backtesting_unica.setLayout(layout_grupo_backtest_unica)
            canvas_backtesting_unica = FigureCanvas(fig)
            canvas_backtesting_unica.setFixedHeight(1150)
            canvas_backtesting_unica.wheelEvent = \
                lambda event: self.on_whell_event(
                    event, backtesting_serie_unica_scroll
                    )
            layout_grupo_backtest_unica.addWidget(canvas_backtesting_unica)
            layout_backtesting_unica_widget.addWidget(grupo_backtesting_unica)
        self.contenido_stackedwidget.addWidget(
            QWidget()
            )
        self.contenido_stackedwidget.addWidget(
            QWidget()
            )

        tab_forecasting_multiseries = QWidget()
        self.contenido_stackedwidget.addWidget(tab_forecasting_multiseries)
    def on_whell_event(self, event, scroll_area):
        """ Desplaza la aplicación verticalmente
        cuando se usa la rueda del mouse
        """
        delta = event.angleDelta().y()
        delta = int(scroll_area.verticalScrollBar().value() - delta / 3)
        scroll_area.verticalScrollBar().setValue(delta)
