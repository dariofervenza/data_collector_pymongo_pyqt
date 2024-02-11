#!/usr/bin/env python
""" Analytics widget, contiene varias tabs
en los que se muestran los graficos de datos,
su analisis y los forecast predictivos (future feature)
"""
import json
import asyncio
import websockets
import pickle

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

from redis import asyncio as aioredis

#plt.style.use('seaborn-v0_8-darkgrid')

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.1"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"

lista_ciudades = ("Vigo", "Lugo", "Madrid")

async def retrieve_data_from_db(my_col, ciudad: str):
    """ Lee los datos de la API que se encuentren
    almacenados en la db para una ciudad concreta
    """
    query = {"location.name" : ciudad}
    result = my_col.find(query)
    db_data = await result.to_list(length=500000)
    return db_data

def create_df_from_data(db_data) -> pd.DataFrame:
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
async def read_data_from_db(lista_ciudades, my_col):
    """ Lanza la lectura de datos de la db
    para las tres ciudades, la creacion de los
    DataFrames de pandas.
    Almacena los 3 dfs en una lista
    """
    lista_dfs_resampled = []
    lista_dfs = []
    tasks_list = []
    for ciudad in lista_ciudades:
    	task = asyncio.create_task(retrieve_data_from_db(my_col, ciudad))
    	tasks_list.append(task)
    results = await asyncio.gather(*tasks_list)
    for db_data, ciudad in zip(results, lista_ciudades):
        df = create_df_from_data(db_data)
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
        df_resampled = df.resample("8H", closed="left", label="right").mean()
        df_resampled = df_resampled.fillna(method='ffill')
        lista_dfs_resampled.append(df_resampled)
    return lista_dfs_resampled

def create_evolucion_variable_fig(lista_dfs_resampled, lista_ciudades, item):
    fig, ax = plt.subplots(figsize=(14, 8))
    for df_resampled, ciudad in zip(lista_dfs_resampled, lista_ciudades):
        df_resampled[item].plot(ax=ax, label=f"{item.capitalize()} en {ciudad}")
    ax.set_title(f"Evolución {item}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel(item.capitalize())
    ax.legend()
    #fig.tight_layout()
    serialized_fig = pickle.dumps(fig)
    return serialized_fig

def create_correlaciones_fig(lista_dfs_resampled, lista_ciudades):
    """ Crea 3 figuras de matplotlib cada una con
    el grafico de correlaciones para cada ciudad.
    Cada gráfico es un subplot con 3 rows (temperatura,
    humedad y presion)
    """
    lista_fig_correlaciones = []
    for i, ciudad in enumerate(lista_ciudades):
        fig, ax = plt.subplots(
            figsize=(12, 12),
            nrows=len(lista_dfs_resampled[i].columns),
            ncols=1
            )
        ax = ax.flat
        fig.tight_layout()
        fig.subplots_adjust(hspace=0.20)
        for index, columna in enumerate(lista_dfs_resampled[i].columns):
            plot_acf(lista_dfs_resampled[i][columna], ax=ax[index], lags=7*5)
            ax[index].set_title(f"Correlaciones {columna.capitalize()} en {ciudad}")
            ax[index].set_xlabel("Lags")
            ax[index].set_ylabel("Correlación")
        lista_fig_correlaciones.append(fig)
    return lista_fig_correlaciones
def create_train_test_split(lista_dfs_resampled):
    """ Crea dos listas, una para los datos train y
    otra para los datos test a partir del resultado del
    metodo read_data_from_db.
    Cada elemento corresponde a los datos de una ciudad
    (Vigo, Lugo o Madrid)
    """
    train_list = []
    test_list = []
    for df_resampled in lista_dfs_resampled:
        largo = len(df_resampled)
        train = df_resampled.iloc[: int(largo*6 / 8)]
        test = df_resampled.iloc[int(largo*6 / 8) :]
        train_list.append(train)
        test_list.append(test)
    return train_list, test_list
def forecasting_serie_unica(variable, lista_ciudades, train_list, test_list):
    """ Genera una figura de matplotlib en la que se
    muestran los datos train, los datos test y las predicciones.
    Cada figura cuenta con un subplot para cada ciudad.
    Esta funcion debe ser llamada varias veces ya que
    el grafico solo se calcula para una variable (temperatura, humedad)
    """
    fig, ax = plt.subplots(figsize=(12, 8), nrows=len(lista_ciudades), ncols=1)
    fig.tight_layout(pad=2.0)
    fig.subplots_adjust(hspace=0.6)
    for numero, ciudad in enumerate(lista_ciudades):
        forecaster = ForecasterAutoreg(
            regressor=LGBMRegressor(
                random_state=15926, verbose=-1,
                n_estimators=1300, max_depth=8,
                learning_rate=0.027914, reg_alpha=0,
                reg_lambda=0
                ),
            lags=10
            )
        forecaster.fit(y=train_list[numero][variable])
        predictions = forecaster.predict(steps=len(test_list[numero]))
        train_list[numero][variable].plot(
            ax=ax[numero], label=f"Train {variable} en {ciudad}"
            )
        test_list[numero][variable].plot(
            ax=ax[numero], label=f"Test {variable} en {ciudad}"
            )
        predictions.plot(ax=ax[numero], label=f"Predictions {variable} en {ciudad}")
        ax[numero].legend()
        ax[numero].set_title(f"Forecasting train-test de {variable} en {ciudad}")
        ax[numero].set_ylabel(variable)
        ax[numero].set_xlabel("Fecha")
    return fig
def backtesting_serie_unica(variable, lista_dfs_resampled, lista_ciudades):
    """ Genera una figura de matplotlib en la que se
    muestran los reales y las predicciones del backtesting.
    Cada figura cuenta con un subplot para cada ciudad.
    Esta funcion debe ser llamada varias veces ya que
    el grafico solo se calcula para una variable (temperatura, humedad)
    """        
    fig, ax = plt.subplots(figsize=(12, 8), nrows=len(lista_ciudades), ncols=1)
    fig.tight_layout(pad=2.0)
    fig.subplots_adjust(hspace=0.6)
    for numero, ciudad in enumerate(lista_ciudades):
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
            y=lista_dfs_resampled[numero][variable],
            steps=1,
            metric="mean_squared_error",
            initial_train_size=int(len(lista_dfs_resampled[numero])*3/4),
            refit=True,
            n_jobs="auto",
            verbose=False,
            show_progress=False
            )
        predictions_backtest = predictions_backtest.rename(
            columns={"pred" : f"Predictions de {variable} en {ciudad}"}
            )
        lista_dfs_resampled[numero][variable].plot(
            ax=ax[numero], label=f"Datos reales de {variable} en {ciudad}"
            )
        predictions_backtest.name = f"Predictions de {variable} en {ciudad}"
        predictions_backtest.plot(ax=ax[numero], label=f"Predictions de {variable} en {ciudad}")
        ax[numero].legend()
        ax[numero].set_title(f"Backtesting de {variable} en {ciudad}")
        ax[numero].set_ylabel(variable)
        ax[numero].set_xlabel("Fecha")
    return fig
