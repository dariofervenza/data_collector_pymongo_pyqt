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

__version__ = "0.1.5"
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

        async with websockets.connect(uri) as websocket:
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
        fig, ax = plt.subplots(figsize=(12, 5), nrows=len(self.ciudades), ncols=1)
        fig.tight_layout()
        fig.subplots_adjust(hspace=0.4)
        for numero, ciudad in enumerate(self.ciudades):
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
            self.train_list[numero][variable].plot(ax=ax[numero], label=f"Train {variable} en {ciudad}")
            self.test_list[numero][variable].plot(ax=ax[numero], label=f"Test {variable} en {ciudad}")
            predictions.plot(ax=ax[numero], label=f"Predictions {variable} en {ciudad}")
            ax[numero].legend()
            ax[numero].set_title(f"Forecasting train-test de {variable} en {ciudad}")
            ax[numero].set_ylabel(variable)
            ax[numero].set_xlabel("fecha")
        return fig

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
            Tab 'Correlaciones':
                Tres graficos de correlaciones (plot_acf)
                cada uno para cada ciudad
                Cada gráfico contiene las correlaciones
                de temperatura, humedad y presión
            Tab 'Distribución de los datos':
                Proximamente

        """
        tab_maestra = QTabWidget()
        tab_maestra.setFocusPolicy(Qt.StrongFocus)
        tab_datos_iniciales_scroll = QScrollArea()
        tab_datos_iniciales_scroll.setFocusPolicy(Qt.StrongFocus)
        tab_datos_iniciales_scroll.setWidgetResizable(True)
        tab_datos_iniciales_scroll.setFixedHeight(800)
        tab_datos_iniciales = QWidget()
        tab_datos_iniciales_scroll.setWidget(tab_datos_iniciales)
        tab_maestra.addTab(tab_datos_iniciales_scroll, "Datos iniciales")
        layout_datos_iniciales_scroll = QVBoxLayout()
        layout_datos_iniciales_scroll.addWidget(tab_datos_iniciales)
        tab_datos_iniciales_scroll.setLayout(layout_datos_iniciales_scroll)

        tab_detalle_corr_scroll_area = QScrollArea()
        tab_detalle_corr = QWidget()
        tab_detalle_corr.setFocusPolicy(Qt.StrongFocus)
        tab_detalle_corr_scroll_area.setWidget(tab_detalle_corr)
        tab_detalle_corr_scroll_area.setWidgetResizable(True)
        tab_detalle_corr_scroll_area.setFixedHeight(800)
        tab_detalle_corr_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        tab_maestra.addTab(tab_detalle_corr_scroll_area, "Correlaciones")
        layout_general_scroll_detalle_corr = QVBoxLayout()
        layout_general_scroll_detalle_corr.addWidget(tab_detalle_corr)
        tab_detalle_corr_scroll_area.setLayout(layout_general_scroll_detalle_corr)


        tab_districucion_datos = QWidget()
        tab_maestra.addTab(tab_districucion_datos, "Distribución de los datos")







        layout_maestro = QVBoxLayout()
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
            evolucion_temp_canvas.setFixedHeight(500)
            evolucion_temp_canvas.setContentsMargins(10, 60, 10, 10)
            
            grupo_item = QGroupBox(item.capitalize())
            layout_grupo_item = QVBoxLayout()
            layout_grupo_item.addWidget(evolucion_temp_canvas)
            grupo_item.setLayout(layout_grupo_item)
            layout_datos_iniciales.addWidget(grupo_item)
        tab_datos_iniciales.setLayout(layout_datos_iniciales)

        layout_detalle_corr = QVBoxLayout()
        lista_fig_correlaciones = self.create_correlaciones_fig()
        for fig_corr, ciudad in zip(lista_fig_correlaciones, self.ciudades):
            corr_canvas = FigureCanvas(fig_corr)
            corr_canvas.setFixedHeight(1500)
            grupo_corr = QGroupBox(f"Correlaciones en {ciudad.capitalize()}")
            layout_grupo_corr = QVBoxLayout()
            layout_grupo_corr.addWidget(corr_canvas)
            grupo_corr.setLayout(layout_grupo_corr)
            layout_detalle_corr.addWidget(grupo_corr)
        tab_detalle_corr.setLayout(layout_detalle_corr)

        layout_distribucion_datos = QGridLayout()
        label_distribucion = QLabel("Proximamente")
        layout_distribucion_datos.addWidget(label_distribucion)
        tab_districucion_datos.setLayout(layout_distribucion_datos)



        sub_tab_maestra_serie_unica = QTabWidget()
        sub_tab_maestra_serie_unica.setContentsMargins(10, 50, 10, 10)
        tab_maestra.addTab(sub_tab_maestra_serie_unica, "Forecasting serie única")



        tab_forecasting_serie_unica = QWidget()
        tab_forecasting_serie_unica_scroll = QScrollArea()       
        layout_forecasting_serie_unica_scroll = QVBoxLayout()
        layout_forecasting_serie_unica_scroll.addWidget(tab_forecasting_serie_unica)
        tab_forecasting_serie_unica_scroll.setWidget(tab_forecasting_serie_unica)
        tab_forecasting_serie_unica_scroll.setWidgetResizable(True)
        tab_forecasting_serie_unica_scroll.setLayout(layout_forecasting_serie_unica_scroll)

        sub_tab_maestra_serie_unica.addTab(tab_forecasting_serie_unica_scroll, "Forecasting")

        msg = (
            "¡ATENCIÓN!",
            "Se ha utilizado el mismo modelo en todos los forecasters.",
            "Es necesario un fine-tunning para cada serie (próximamente)"
            )
        layout_tab_forecasting_serie_unica = QVBoxLayout()
        lista_avisos = []
        for i, mensaje in enumerate(msg):
            lista_avisos.append(QLabel(mensaje))
        for i, aviso in enumerate(lista_avisos):        
            aviso.setObjectName(f"aviso_forecast_unica_{i}")
            layout_tab_forecasting_serie_unica.addWidget(aviso)
            layout_tab_forecasting_serie_unica.setAlignment(
                aviso,
                Qt.AlignCenter
                )
        variables = ("temperatura", "humedad", "presion")
        lista_figuras = []
        
        

        for variable in variables:
            lista_figuras.append(self.forecasting_serie_unica(variable))
        for fig, variable in zip(lista_figuras, variables):
            canvas_forecasting_serie_unica = FigureCanvas(fig)
            canvas_forecasting_serie_unica.setFixedHeight(1150)
            forecasting_serie_unica_group = QGroupBox(variable.capitalize())
            layout_forecasting_serie_unica_group = QVBoxLayout()
            layout_forecasting_serie_unica_group.addWidget(
                canvas_forecasting_serie_unica
                )
            forecasting_serie_unica_group.setLayout(layout_forecasting_serie_unica_group)
            layout_tab_forecasting_serie_unica.addWidget(
                forecasting_serie_unica_group
                )
        tab_forecasting_serie_unica.setLayout(layout_tab_forecasting_serie_unica)
        
        
        
        sub_tab_maestra_serie_unica.addTab(QWidget(), "Backtesting")
