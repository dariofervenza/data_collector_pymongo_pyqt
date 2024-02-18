#!/usr/bin/env python
""" Modulo con tareas de celery.
Conecta con la base de datos de MongoDB y extrae los datos
de la API de Weather.
Realiza los calculos de forecasting y backtesting.
Crea las figuras de matplotlib y las serializa con pickle
Guarda los datos en redis
"""
import asyncio
import pickle
from typing import List
from typing import Dict
from typing import Tuple
from datetime import datetime
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf
# from statsmodels.graphics.tsaplots import plot_pacf

from lightgbm import LGBMRegressor
# from sklearn.metrics import mean_squared_error
# from sklearn.preprocessing import StandardScaler
from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.model_selection import backtesting_forecaster
# from skforecast.ForecasterAutoregMultiSeries import ForecasterAutoregMultiSeries
# from skforecast.model_selection_multiseries import backtesting_forecaster_multiseries

from redis import asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from celery import Celery
from celery.schedules import crontab

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"

CONNECTION_STRING = "mongodb://localhost:27017/"
MY_CLIENT = AsyncIOMotorClient(CONNECTION_STRING)
MY_DB = MY_CLIENT["my_app_db"]
DATA_COLLECTION = MY_DB["api_data"]
CIUDADES = ("Vigo", "Lugo", "Madrid")
VARIABLES = ("temperatura", "humedad", "presion")

async def obtain_data_form_db(data_collection: AsyncIOMotorCollection,
    ciudad: str) -> List[Dict]:
    """ Recibe la colección de datos de MongoDB y la ciudad
    a buscar.
    Realiza la búsqueda en MongoDB y devuelve una lista
    como resultado
    """
    query = {"location.name" : ciudad}
    result = data_collection.find(query)
    result = await result.to_list(length=500000)
    return result
def create_df_from_data(db_data: List[Dict]) -> pd.DataFrame:
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
            #ciudad = element["location"]["name"]
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

async def obtain_data_form_cities(data_collection: AsyncIOMotorCollection,
    ciudades: str) -> List[pd.DataFrame]:
    """ LLama a las funciones para obtener datos y crear dfs
    Genera una lista de df's y la devuleve
    """
    lista_db_data = []
    lista_dfs = []
    lista_dfs_resampled = []
    for ciudad in ciudades:
        append = await obtain_data_form_db(data_collection, ciudad)
        lista_db_data.append(append)
    for db_data, ciudad in zip(lista_db_data, ciudades):
        df = create_df_from_data(db_data)
        df["ciudad"] = ciudad
        lista_dfs.append(df)
    for index, df in enumerate(lista_dfs):
        df.set_index("fecha", inplace=True)
        lista_dfs[index] = df
    lista_dfs_datos = []
    for index, df in enumerate(lista_dfs):
        df = df[["temperatura", "humedad", "presion"]]
        lista_dfs_datos.append(df)
    for index, df in enumerate(lista_dfs_datos):
        df_resampled = df.resample("2H", closed="left", label="right").mean()
        df_resampled = df_resampled.fillna(method='ffill')
        lista_dfs_resampled.append(df_resampled)
    return lista_dfs_resampled

def create_evolucion_variable_fig(lista_dfs_resampled: List[pd.DataFrame],
    lista_ciudades: List[str], item: str) -> bytes:
    """ Crea la figura que muestra simplemente la evolución de las
    variables y la devulve serializada con pickle
    """
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

def create_correlaciones_fig(lista_dfs_resampled: List[pd.DataFrame],
    lista_ciudades: List[str]) -> List[plt.Figure]:
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
def create_train_test_split(
    lista_dfs_resampled: List[pd.DataFrame]) -> Tuple[List[float]]:
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
def forecasting_serie_unica(variable: str,
    lista_ciudades: List[str], train_list: List[float],
    test_list: List[float]) -> plt.Figure:
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
def backtesting_serie_unica(variable: str,
    lista_dfs_resampled: List[pd.DataFrame],
    lista_ciudades: List[str]) -> plt.Figure:
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

async def save_to_redis(lista_ciudades: List[str],
    data_collection: AsyncIOMotorCollection) -> None:
    """ Guarda los datos serializados en una base de datos de redis.
    Se realiza el guardado en forma de listas con rpush.
    Para ello, llama a el resto de funciones (obtener datos, crear lista de dfs,
    generar las figuras serializadas)
    """
    redis = await aioredis.from_url("redis://localhost:6379")
    lista_dfs_resampled = await obtain_data_form_cities(data_collection, lista_ciudades)
    items = lista_dfs_resampled[0].columns[: 3]
    await redis.delete("figuras_evolucion")
    await redis.delete("items_figuras_evolucion")
    for item in items:
        await redis.rpush("items_figuras_evolucion", item)
        serialized_fig = create_evolucion_variable_fig(
            lista_dfs_resampled, lista_ciudades, item
            )
        await redis.rpush("figuras_evolucion", serialized_fig)
    lista_fig_correlaciones = create_correlaciones_fig(lista_dfs_resampled, lista_ciudades)
    await redis.delete("figuras_correlaciones")
    for fig in lista_fig_correlaciones:
        fig_serialized = pickle.dumps(fig)
        await redis.rpush("figuras_correlaciones", fig_serialized)
    train_list, test_list = create_train_test_split(lista_dfs_resampled)
    lista_figuras_serie_unica = []
    for variable in items:
        lista_figuras_serie_unica.append(forecasting_serie_unica(
            variable,
            lista_ciudades,
            train_list,
            test_list
            ))
    await redis.delete("figuras_forecasting_serie_unica")
    for fig in lista_figuras_serie_unica:
        fig_serialized = pickle.dumps(fig)
        await redis.rpush("figuras_forecasting_serie_unica", fig_serialized)
    lista_figuras_backtest_unica = []
    for variable in items:
        lista_figuras_backtest_unica.append(backtesting_serie_unica(
            variable,
            lista_dfs_resampled,
            lista_ciudades
            ))
    await redis.delete("figuras_backtesting_serie_unica")
    for fig in lista_figuras_backtest_unica:
        fig_serialized = pickle.dumps(fig)
        await redis.rpush("figuras_backtesting_serie_unica", fig_serialized)
    await redis.aclose()
    matplotlib.pyplot.close()
    for _ in range(20):
        print("guardado en redis")

app = Celery("tasks", broker="pyamqp://guest@localhost//")
@app.task
def save_to_redis_task() -> None:
    """ Tarea de celery responsable del guardado de figuras
    serializadas en listas de redis
    """
    print("\n\n")
    print(f"[Guardando en redis: {datetime.now()}]")
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(save_to_redis(CIUDADES, DATA_COLLECTION))
    except RuntimeError:
        print("\n\n")
        print(f"error: {datetime.now()}")

app.conf.beat_schedule = {
    'every-five-minutes-task': {
        'task': 'tasks.save_to_redis_task',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}
