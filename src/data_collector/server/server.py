#!/usr/bin/env python
""" Modulo principal recibe
de los demas modulos las funciones necesarias
y arranca el servidor
"""
import json
import asyncio
from functools import partial
from datetime import datetime
import requests
import websockets
from websockets.server import WebSocketServer
import pickle
import jwt
from datetime import datetime
from aiormq import connect
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis import asyncio as aioredis
import matplotlib

from data_validation import ApiData
from server_alarms import add_alarm
from server_alarms import return_alarms
from server_alarms import delete_alarms
from server_alarms import return_avisos
from server_alarms import create_todos_los_avisos
from server_alarms import create_avisos_event
from server_auth import insert_user
from server_auth import autenticar
from server_auth import check_fecha_caducidad_token
from server_analytics import read_data_from_db
from server_analytics import create_evolucion_variable_fig
from server_analytics import create_correlaciones_fig
from server_analytics import create_train_test_split
from server_analytics import forecasting_serie_unica
from server_analytics import backtesting_serie_unica

from config import (
    DATA_COLLECTION, USERS_COLLECTION,
    ROOT_USER, ROOT_PASSWORD,
    SECRET_KEY,
    ALARMS_COLLECTION,
    AVISOS_COLLECTION,
    LISTA_CIUDADES,
)


__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.1"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"



async def receive_messages():
    connection = await connect("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    declare_ok = await channel.queue_declare('api')
    # read previous messages
    while True:
        message = await channel.basic_get(declare_ok.queue)
        if message.body == b"":
            break
        await callback(message)
        # borrar mensaje
        await channel.basic_ack(message.delivery.delivery_tag)
    consume_ok = await channel.basic_consume(
        declare_ok.queue, callback, no_ack=True
    )
    # no_ack=True para borrar los mensajes
async def callback(message):
    mensaje = json.loads(message.body)
    ciudad = mensaje["ciudad"]
    data = mensaje["data"]
    await insert_api_data_in_mongo(api_response=data, ciudad=ciudad)
    await create_avisos_event(
        alarms_collection=ALARMS_COLLECTION,
        avisos_collection=AVISOS_COLLECTION,
        data_collection=DATA_COLLECTION, 
        api_response=data
        )


async def insert_api_data_in_mongo(api_response, ciudad:str):
    """ Funcion lanzada con un async scheduler, hace la
    request a la API de weather stack y almacena los
    datos en una colección de MongoDB
    """
    query = {
        "location.name" : api_response["location"]["name"],
        "location.country" : api_response["location"]["country"],
        "location.region" : api_response["location"]["region"],
        "location.lat" : api_response["location"]["lat"],
        "location.lon" : api_response["location"]["lon"],
        "location.tz_id" : api_response["location"]["tz_id"],
        "location.localtime" : api_response["location"]["localtime"],
        "location.localtime_epoch" : api_response["location"]["localtime_epoch"],
        "current.condition.text" : api_response["current"]["condition"]["text"],
        "current.condition.icon" : api_response["current"]["condition"]["icon"],
        "current.condition.code" : api_response["current"]["condition"]["code"],
        "current.last_updated_epoch" : api_response["current"]["last_updated_epoch"],
        "current.last_updated" : api_response["current"]["last_updated"],
        "current.temp_c" : api_response["current"]["temp_c"],
        "current.temp_f" : api_response["current"]["temp_f"],
        "current.is_day" : api_response["current"]["is_day"],
        "current.wind_mph" : api_response["current"]["wind_mph"],
        "current.wind_kph" : api_response["current"]["wind_kph"],
        "current.wind_degree" : api_response["current"]["wind_degree"],
        "current.wind_dir" : api_response["current"]["wind_dir"],
        "current.pressure_mb" : api_response["current"]["pressure_mb"],
        "current.pressure_in" : api_response["current"]["pressure_in"],
        "current.precip_mm" : api_response["current"]["precip_mm"],
        "current.precip_in" : api_response["current"]["precip_in"],
        "current.humidity" : api_response["current"]["humidity"],
        "current.cloud" : api_response["current"]["cloud"],
        "current.feelslike_c" : api_response["current"]["feelslike_c"],
        "current.feelslike_f" : api_response["current"]["feelslike_f"],
        "current.vis_km" : api_response["current"]["vis_km"],
        "current.vis_miles" : api_response["current"]["vis_miles"],
        "current.uv" : api_response["current"]["uv"],
        "current.gust_mph" : api_response["current"]["gust_mph"],
        "current.gust_kph" : api_response["current"]["gust_kph"],
        }
    document = await DATA_COLLECTION.find_one(query)
    if document is None:
        data = ApiData(**api_response)
        await DATA_COLLECTION.insert_one(data.dict())
        print(f"Server ha añadido a la db: {ciudad}")
    else:
        print("Dato ya existe en la db")
async def save_to_redis(lista_ciudades, my_col):
    redis = await aioredis.from_url("redis://localhost:6379")
    lista_dfs_resampled = await read_data_from_db(lista_ciudades, my_col)
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



    await redis.aclose()
    matplotlib.pyplot.close()
    print("guardado en redis")  

async def receive_client_query_and_send_db_result(my_col, users_collection,
                                                  secret_key, alarms_collection,
                                                  avisos_collection,
                                                  websocket):
    """ Handler del server con websockets, recibe las peticiones
    en forma de {"tipo_request" : tipo_request, "value" : valor_request}
    Es usada con "partial" de functools para dejar unicamente
    el websocket como argumento.
    Principales procesos:
        - Login --> Comprueba el user en la db y devuelve un token
                    a traves del websocket (en caso de que los
                    datos sean correctos).
        - Data request --> Envía los datos de la API, que estan en la db.
        - Create alarm --> Genera una alarma para un usuario y la almacena
                           en la db.
        - Return alarms --> Devuelve las alarmas que tenga la db
                            almacenadas para un user a traves
                            del websocket.
        - Delete alarms --> Elimina las alarmas que el user marca
                            en la GUI y sus notificaciones generadas
        - Return avisos --> Devuelve los avisos a partir de una fecha,
                            lee los datos posteriores a esa fecha,
                            busca los avisos asociados a esos datos
                            y a el user que lo esté solicitando
                            y los envia a traves del websocket.
    """
    try:
        datos_user_request = await websocket.recv()
        datos_user_request = json.loads(datos_user_request)
        if datos_user_request["tipo_request"] == "login":
            user_dict = datos_user_request["value"]
            autenticado = await autenticar(user_dict, users_collection)
            if autenticado.pop("autenticado"):
                token = jwt.encode(autenticado, secret_key, algorithm="HS256")
                token = {"autenticado" : True, "token" : token}
                token = json.dumps(token)
                await websocket.send(token)
            else:
                token = {"autenticado" : False}
                token = json.dumps(token)
                await websocket.send(token)
        elif datos_user_request["tipo_request"] == "data_request":
            token = datos_user_request["value"]
            query = token["query"]
            token = token["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            autenticado = check_fecha_caducidad_token(token)
            if autenticado:
                result = my_col.find(query)
                result = await result.to_list(length=500000)
                result = {"autenticado": True, "data" : result}
                result = json.dumps(result, default=str)
                await websocket.send(result)
            else:
                result = {"autenticado": False, "data" : []}
        elif datos_user_request["tipo_request"] == "create_alarm":
            datos_alarma = datos_user_request["value"]
            datos = datos_alarma["data"]
            token = datos_alarma["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            autenticado = check_fecha_caducidad_token(token)
            user = token["user"]
            if autenticado:
                resultado = await add_alarm(alarms_collection, user, datos)
            else:
                resultado = "Token expirado, vuelva a iniciar sesión"
            await websocket.send(resultado)
        elif datos_user_request["tipo_request"] == "return_alarms":
            print("peticion de alarmas")
            token = datos_user_request["value"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            autenticado = check_fecha_caducidad_token(token)
            if autenticado:
                alarmas = await return_alarms(alarms_collection, user)
                alarmas = {"autenticado": True, "data" : alarmas}
            else:
                alarmas = {"autenticado": False, "data" : alarmas}
            alarmas = json.dumps(alarmas)
            print("vamos a enviar alarmas")
            await websocket.send(alarmas)
        elif datos_user_request["tipo_request"] == "delete_alarms":
            print("eliminar alarmas")
            data = datos_user_request["value"]
            token = data["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            rows_to_delete = data["rows_to_delete"]
            autenticado = check_fecha_caducidad_token(token)
            if autenticado:
                await delete_alarms(
                    alarms_collection, user,
                    rows_to_delete, avisos_collection
                    )
                await websocket.send("Alarmas eliminadas")
            else:
                await websocket.send("Token expirado, vuelva a iniciar sesión")
        elif datos_user_request["tipo_request"] == "return_avisos":
            print("obtener avisos")
            print(f"control hora: {datetime.now()}")
            data = datos_user_request["value"]
            token = data["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            fecha_avisos = data["fecha_avisos"]
            print(f"control hora2: {datetime.now()}")
            autenticado = check_fecha_caducidad_token(token)
            print(f"control hora3: {datetime.now()}")
            if autenticado:
                lista_avisos = await return_avisos(
                    avisos_collection,
                    fecha_avisos,
                    my_col,
                    alarms_collection,
                    user)
                print(f"control hora4: {datetime.now()}")
                lista_avisos = json.dumps(lista_avisos, default=str)
                response = {"autenticado" : True, "data" : lista_avisos}
                print(f"control hora5: {datetime.now()}")
            else:
                response = {"autenticado" : False, "data" : []}
            response = json.dumps(response)
            await websocket.send(response)
        elif datos_user_request["tipo_request"] == "comprobar_token":
            data = datos_user_request["value"]
            token = data["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            autenticado = check_fecha_caducidad_token(token)
            if autenticado:
                result = {"autenticado" : True}
            else:
                result = {"autenticado" : False}
            result = json.dumps(result, default=str)
            await websocket.send(result)

        await websocket.close()
    except websockets.exceptions.ConnectionClosedError:
        print("conexion cerrada por el client")


async def main():
    """ Función principal del server,
    lanza los procesos en background como async schedulers,
    es decir, insertar los daots de la API de weather stack,
    y crear los avisos (en un futuro los avisos pasarán a
    crearse cuando se añada un dato).
    Lanza el handler del server con webosckets.
    """
    tipo_user = "admin"
    await insert_user(ROOT_USER, ROOT_PASSWORD, USERS_COLLECTION, tipo_user)
    partial_handler = partial(
        receive_client_query_and_send_db_result,
        DATA_COLLECTION,
        USERS_COLLECTION,
        SECRET_KEY,
        ALARMS_COLLECTION,
        AVISOS_COLLECTION
        )
    scheduler = AsyncIOScheduler()
    #ajustar a 21 * 3 datos al dia para 1000 request/mes
    # es decir cada 144 min
    scheduler.add_job(
        receive_messages
        )
    scheduler.add_job(
        save_to_redis, # VALORAR MOVERLO A CELERY PARA QUE NO BLOQUEE EL SERVER
        "interval",
        minutes=15,
        args=[LISTA_CIUDADES, DATA_COLLECTION]
        )
    # NOTA: Cambiar esto, los avisos se crean al añadir un dato
    """scheduler.add_job(
        create_todos_los_avisos,
        "interval",
        minutes=1,
        args=[alarms_collection, avisos_collection, DATA_COLLECTION]
        )"""
    scheduler.start()
    print("AÑADIDOS SCHEDULERS")
    async with websockets.serve(partial_handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
