#!/usr/bin/env python
""" Analytics widget, contiene varias tabs
en los que se muestran los graficos de datos,
su analisis y los forecast predictivos (future feature)
"""
import json
import asyncio
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QScrollArea

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEasingCurve

from qfluentwidgets import SmoothScrollArea
from qfluentwidgets import Flyout
from qfluentwidgets import FlyoutAnimationType
from qfluentwidgets import Action
from qfluentwidgets import CommandBar
from qfluentwidgets import TransparentDropDownPushButton
from qfluentwidgets import RoundMenu
from qfluentwidgets import CommandBarView
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import setFont

import plotly.graph_objs as go
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf

from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.model_selection import backtesting_forecaster
from skforecast.ForecasterAutoregMultiSeries import ForecasterAutoregMultiSeries
from skforecast.model_selection_multiseries import backtesting_forecaster_multiseries

#plt.style.use('seaborn-v0_8-darkgrid')

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.1"
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
    def __init__(self):
        super().__init__()
        self.token = None
        self.server_ip = "localhost"
        self.setObjectName("AnalyticsWidget")

        self.lista_dfs_resampled = []
        self.train_list = []
        self.test_list = []
        self.ciudades = ("Vigo", "Lugo", "Madrid")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.read_data_from_db())
        self.create_train_test_split()


        self.create_figure()
    async def retrieve_data_from_db(self, ciudad: str):
        """ Lee los datos de la API que se encuentren
        almacenados en la db para una ciudad concreta
        """
        uri = f"ws://{self.server_ip}:8765"
        query = {"location.name" : ciudad}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)

        custom_message_size = 1024*1024*5
        async with websockets.connect(uri, max_size=custom_message_size) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            db_data = response
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
        datos = json.loads(db_data)
        for element in datos:
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
                ciudad = element["location"]["name"]
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

    async def read_data_from_db(self):
        """ Lanza la lectura de datos de la db
        para las tres ciudades, la creacion de los
        DataFrames de pandas.
        Almacena los 3 dfs en una lista
        """
        lista_db_data = []
        lista_dfs = []
        for ciudad in self.ciudades:
            lista_db_data.append(await self.retrieve_data_from_db(ciudad))
        for db_data, ciudad in zip(lista_db_data, self.ciudades):
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
    def create_train_test_split(self):
        """ Crea dos listas, una para los datos train y
        otra para los datos test a partir del resultado del
        metodo read_data_from_db.
        Cada elemento corresponde a los datos de una ciudad
        (Vigo, Lugo o Madrid)
        """
        for df_resampled in self.lista_dfs_resampled:
            largo = len(df_resampled)
            train = df_resampled.iloc[: int(largo*6 / 8)]
            test = df_resampled.iloc[int(largo*6 / 8) :]
            self.train_list.append(train)
            self.test_list.append(test)
    def create_correlaciones_fig(self):
        """ Crea 3 figuras de matplotlib cada una con
        el grafico de correlaciones para cada ciudad.
        Cada gráfico es un subplot con 3 rows (temperatura,
        humedad y presion)
        """
        lista_fig_correlaciones = []
        for i, ciudad in enumerate(self.ciudades):
            fig, ax = plt.subplots(
                figsize=(12, 12),
                nrows=len(self.lista_dfs_resampled[i].columns),
                ncols=1
                )
            ax = ax.flat
            fig.tight_layout()
            fig.subplots_adjust(hspace=0.20)
            for index, columna in enumerate(self.lista_dfs_resampled[i].columns):
                plot_acf(self.lista_dfs_resampled[i][columna], ax=ax[index], lags=7*5)
                ax[index].set_title(f"Correlaciones {columna.capitalize()} en {ciudad}")
                ax[index].set_xlabel("Lags")
                ax[index].set_ylabel("Correlación")
            lista_fig_correlaciones.append(fig)
        return lista_fig_correlaciones

    def forecasting_serie_unica(self, variable):
        """ Genera una figura de matplotlib en la que se
        muestran los datos train, los datos test y las predicciones.
        Cada figura cuenta con un subplot para cada ciudad.
        Esta funcion debe ser llamada varias veces ya que
        el grafico solo se calcula para una variable (temperatura, humedad)
        """
        fig, ax = plt.subplots(figsize=(12, 8), nrows=len(self.ciudades), ncols=1)
        fig.tight_layout(pad=2.0)
        fig.subplots_adjust(hspace=0.6)
        """for numero, ciudad in enumerate(self.ciudades):
            forecaster = ForecasterAutoreg(
                regressor=LGBMRegressor(
                    random_state=15926, verbose=-1,
                    n_estimators=1300, max_depth=8,
                    learning_rate=0.027914, reg_alpha=0,
                    reg_lambda=0
                    ),
                lags=30
                )
            forecaster.fit(y=self.train_list[numero][variable])
            predictions = forecaster.predict(steps=len(self.test_list[numero]))
            self.train_list[numero][variable].plot(
                ax=ax[numero], label=f"Train {variable} en {ciudad}"
                )
            self.test_list[numero][variable].plot(
                ax=ax[numero], label=f"Test {variable} en {ciudad}"
                )
            predictions.plot(ax=ax[numero], label=f"Predictions {variable} en {ciudad}")
            ax[numero].legend()
            ax[numero].set_title(f"Forecasting train-test de {variable} en {ciudad}")
            ax[numero].set_ylabel(variable)
            ax[numero].set_xlabel("Fecha")"""
        return fig
    def backtesting_serie_unica(self, variable):
        """ Genera una figura de matplotlib en la que se
        muestran los reales y las predicciones del backtesting.
        Cada figura cuenta con un subplot para cada ciudad.
        Esta funcion debe ser llamada varias veces ya que
        el grafico solo se calcula para una variable (temperatura, humedad)
        """        
        fig, ax = plt.subplots(figsize=(12, 8), nrows=len(self.ciudades), ncols=1)
        fig.tight_layout(pad=2.0)
        fig.subplots_adjust(hspace=0.6)
        """for numero, ciudad in enumerate(self.ciudades):
            forecaster = ForecasterAutoreg(
                regressor=LGBMRegressor(
                    random_state=15926, verbose=-1,
                    n_estimators=1300, max_depth=8,
                    learning_rate=0.027914, reg_alpha=0,
                    reg_lambda=0
                    ),
                lags=30
                )
            _, predictions_backtest = backtesting_forecaster(
                forecaster=forecaster,
                y=self.lista_dfs_resampled[numero][variable],
                steps=1,
                metric="mean_squared_error",
                initial_train_size=int(len(self.lista_dfs_resampled[numero])*3/4),
                refit=True,
                n_jobs="auto",
                verbose=False,
                show_progress=False
                )
            predictions_backtest = predictions_backtest.rename(
                columns={"pred" : f"Predictions de {variable} en {ciudad}"}
                )
            self.lista_dfs_resampled[numero][variable].plot(
                ax=ax[numero], label=f"Datos reales de {variable} en {ciudad}"
                )
            predictions_backtest.name = f"Predictions de {variable} en {ciudad}"
            predictions_backtest.plot(ax=ax[numero], label=f"Predictions de {variable} en {ciudad}")
            ax[numero].legend()
            ax[numero].set_title(f"Backtesting de {variable} en {ciudad}")
            ax[numero].set_ylabel(variable)
            ax[numero].set_xlabel("Fecha")"""
        return fig
    def on_graph_click(self, event):
        if event.inaxes:
            view = CommandBarView(self)
        view.addAction(Action(FIF.SHARE, 'Share'))
        view.addAction(Action(FIF.SAVE, 'Save', triggered=self.save_fig))
        view.addAction(Action(FIF.DELETE, 'Delete'))

        view.addHiddenAction(Action(FIF.APPLICATION, 'App', shortcut='Ctrl+A'))
        view.addHiddenAction(Action(FIF.SETTING, 'Settings', shortcut='Ctrl+S'))
        view.resizeToSuitableWidth()

        Flyout.make(view, self.tab_datos_iniciales_scroll, self, FlyoutAnimationType.FADE_IN)            
    def save_fig(self):
        pass
    def switch_to_datos_iniciales(self):
        pass
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
        datos_iniciales_action = Action(FIF.CALENDAR, "Datos iniciales", self)
        datos_iniciales_action.triggered.connect(self.switch_to_datos_iniciales)
        self.command_bar.addAction(datos_iniciales_action)
        self.command_bar.addSeparator()
        button = TransparentDropDownPushButton('Menu', self, FIF.MENU)
        button.setFixedHeight(34)
        setFont(button, 12)

        menu = RoundMenu(parent=self)
        menu.addActions([
            Action(FIF.COPY, 'Copy'),
            Action(FIF.CUT, 'Cut'),
            Action(FIF.PASTE, 'Paste'),
            Action(FIF.CANCEL, 'Cancel'),
            Action('Select all'),
        ])
        button.setMenu(menu)
        self.command_bar.addWidget(button)
        self.command_bar.addHiddenAction(Action(FIF.SETTING, 'Settings', shortcut='Ctrl+S'))




        tab_maestra = QTabWidget()
        self.tab_datos_iniciales_scroll = QScrollArea()
        self.tab_datos_iniciales_scroll.setWidgetResizable(True)
        tab_datos_iniciales_widget = QWidget()
        self.tab_datos_iniciales_scroll.setWidget(tab_datos_iniciales_widget)
        tab_maestra.addTab(self.tab_datos_iniciales_scroll, "Datos iniciales")
        layout_datos_iniciales_scroll = QVBoxLayout()
        layout_datos_iniciales_scroll.addWidget(tab_datos_iniciales_widget)
        self.tab_datos_iniciales_scroll.setLayout(layout_datos_iniciales_scroll)

        self.tab_datos_iniciales_scroll.installEventFilter(self)

        tab_detalle_corr_scroll_area = SmoothScrollArea()
        tab_detalle_corr_widget = QWidget()
        tab_detalle_corr_scroll_area.setWidget(tab_detalle_corr_widget)
        tab_detalle_corr_scroll_area.setWidgetResizable(True)
        tab_detalle_corr_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        tab_maestra.addTab(tab_detalle_corr_scroll_area, "Correlaciones")
        layout_general_scroll_detalle_corr = QVBoxLayout()
        layout_general_scroll_detalle_corr.addWidget(tab_detalle_corr_widget)
        tab_detalle_corr_scroll_area.setLayout(layout_general_scroll_detalle_corr)


        tab_districucion_datos = QWidget()
        tab_maestra.addTab(tab_districucion_datos, "Distribución de los datos")


        layout_maestro = QVBoxLayout()
        layout_maestro.addWidget(self.command_bar)
        layout_maestro.addWidget(tab_maestra)

        self.setLayout(layout_maestro)

        layout_datos_iniciales = QVBoxLayout()

        items = self.lista_dfs_resampled[0].columns[:3]
        for item in items:
            fig, ax = plt.subplots(figsize=(14, 8))
            for df_resampled, ciudad in zip(self.lista_dfs_resampled, self.ciudades):
                df_resampled[item].plot(ax=ax, label=f"{item.capitalize()} en {ciudad}")
            ax.set_title(f"Evolución {item}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel(item.capitalize())
            ax.legend()
            #fig.tight_layout()

            evolucion_temp_canvas = FigureCanvas(fig)
            evolucion_temp_canvas.mpl_connect("button_press_event", self.on_graph_click)
            evolucion_temp_canvas.setFixedHeight(500)
            evolucion_temp_canvas.setContentsMargins(10, 60, 10, 10)
            evolucion_temp_canvas.setFocusPolicy(Qt.StrongFocus)
            evolucion_temp_canvas.wheelEvent = lambda event: self.on_whell_event(
                event, self.tab_datos_iniciales_scroll
                )
            grupo_item = QGroupBox(item.capitalize())
            layout_grupo_item = QVBoxLayout()
            layout_grupo_item.addWidget(evolucion_temp_canvas)
            grupo_item.setLayout(layout_grupo_item)
            grupo_item.wheelEvent = lambda event: self.on_whell_event(
                event, self.tab_datos_iniciales_scroll
                )
            layout_datos_iniciales.addWidget(grupo_item)
        tab_datos_iniciales_widget.setLayout(layout_datos_iniciales)
        
        layout_detalle_corr = QVBoxLayout()
        lista_fig_correlaciones = self.create_correlaciones_fig()
        for fig_corr, ciudad in zip(lista_fig_correlaciones, self.ciudades):
            corr_canvas = FigureCanvas(fig_corr)
            corr_canvas.wheelEvent = lambda event: self.on_whell_event(
                event,
                tab_detalle_corr_scroll_area
                )
            corr_canvas.setFixedHeight(1500)
            grupo_corr = QGroupBox(f"Correlaciones en {ciudad.capitalize()}")
            layout_grupo_corr = QVBoxLayout()
            layout_grupo_corr.addWidget(corr_canvas)
            grupo_corr.setLayout(layout_grupo_corr)
            grupo_corr.wheelEvent = lambda event: self.on_whell_event(
                event,
                tab_detalle_corr_scroll_area
                )
            layout_detalle_corr.addWidget(grupo_corr)
        tab_detalle_corr_widget.setLayout(layout_detalle_corr)

        layout_distribucion_datos = QGridLayout()
        label_distribucion = QLabel("Proximamente")
        layout_distribucion_datos.addWidget(label_distribucion)
        tab_districucion_datos.setLayout(layout_distribucion_datos)



        sub_tab_maestra_serie_unica = QTabWidget()
        sub_tab_maestra_serie_unica.setContentsMargins(10, 50, 10, 10)
        tab_maestra.addTab(sub_tab_maestra_serie_unica, "Forecasting serie única")



        tab_forecasting_serie_unica_widget = QWidget()
        tab_forecasting_serie_unica_scroll = SmoothScrollArea()
        layout_forecasting_serie_unica_scroll = QVBoxLayout()
        layout_forecasting_serie_unica_scroll.addWidget(tab_forecasting_serie_unica_widget)
        tab_forecasting_serie_unica_scroll.setWidget(tab_forecasting_serie_unica_widget)
        tab_forecasting_serie_unica_scroll.setWidgetResizable(True)
        tab_forecasting_serie_unica_scroll.setLayout(layout_forecasting_serie_unica_scroll)

        sub_tab_maestra_serie_unica.addTab(tab_forecasting_serie_unica_scroll, "Forecasting")

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


        self.variables = ("temperatura", "humedad", "presion")
        self.lista_figuras_serie_unica = []
        

        for variable in self.variables:
            self.lista_figuras_serie_unica.append(self.forecasting_serie_unica(variable))
        for fig, variable in zip(self.lista_figuras_serie_unica, self.variables):
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
        sub_tab_maestra_serie_unica.addTab(backtesting_serie_unica_scroll, "Backtesting")
        layout_backtesting_unica_widget = QVBoxLayout()
        backtesting_serie_unica_widget.setLayout(layout_backtesting_unica_widget)
        self.lista_figuras_backtest_unica = []
        for variable in self.variables:
            self.lista_figuras_backtest_unica.append(self.backtesting_serie_unica(variable))
        for fig, variable in zip(self.lista_figuras_backtest_unica, self.variables):
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
        sub_tab_maestra_serie_unica.addTab(
            QWidget(), "Forecasting con variables cíclicas"
            )
        sub_tab_maestra_serie_unica.addTab(
            QWidget(), "Backtesting con variables cíclicas"
            )
        
        tab_forecasting_multiseries = QWidget()
        tab_maestra.addTab(tab_forecasting_multiseries, "Forecasting multiseries")
    def on_whell_event(self, event, scroll_area):
        delta = event.angleDelta().y()
        delta = int(scroll_area.verticalScrollBar().value() - delta / 3)
        scroll_area.verticalScrollBar().setValue(delta)



