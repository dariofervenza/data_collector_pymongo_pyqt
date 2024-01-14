#!/usr/bin/env python
""" Modulo principal recibe
de los demas modulos las funciones necesarias
y arranca el servidor
"""
import json
import asyncio
from functools import partial
import requests
import websockets
import jwt
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data_validation import ApiData
from server_alarms import add_alarm
from server_alarms import return_alarms
from server_alarms import delete_alarms
from server_alarms import return_avisos
from server_alarms import create_avisos
from server_auth import insert_user
from server_auth import autenticar


__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.0"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


CONNECTION_STRING = "mongodb://localhost:27017/"
MY_CLIENT = AsyncIOMotorClient(CONNECTION_STRING)
MY_DB = MY_CLIENT["my_app_db"]
DATA_COLLECTION = MY_DB["api_data"]
USERS_COLLECTION = MY_DB["usuarios"]
ALARMS_COLLECTION = MY_DB["alarmas"]
AVISOS_COLLECTION = MY_DB["avisos"]


ROOT_USER = "paco"
ROOT_PASSWORD = "paco"

SECRET_KEY = "SuPer_SEcret_kEY"


async def insert_api_data_in_mongo(my_db, my_col, ciudad: str):
    """ Funcion lanzada con un async scheduler, hace la
    request a la API de weather stack y almacena los
    datos en una colección de MongoDB
    """
    print(await my_db.list_collection_names())
    params = {
        'access_key': 'aaaa',
        'query': ciudad
    }
    api_result = requests.get(
        'http://api.weatherstack.com/current',
        params,
        timeout=5
        )
    print(api_result.status_code, type(api_result.status_code))
    if api_result.status_code == 200:
        api_response = api_result.json()
        data = ApiData(**api_response)
        await my_col.insert_one(data.dict())
        print("añadido")


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
                # VALORAR PONERLE CADUCIDAD
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
            if True:
                # aqui se comprobaria que el token es correcto
                # (¿que pasa si roban un token?)
                result = my_col.find(query)
                result = await result.to_list(length=1000)
                result = json.dumps(result, default=str)
                await websocket.send(result)
        elif datos_user_request["tipo_request"] == "create_alarm":
            datos_alarma = datos_user_request["value"]
            datos = datos_alarma["data"]
            token = datos_alarma["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            resultado = await add_alarm(alarms_collection, user, datos)
            await websocket.send(resultado)
        elif datos_user_request["tipo_request"] == "return_alarms":
            print("peticion de alarmas")
            token = datos_user_request["value"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            alarmas = await return_alarms(alarms_collection, user)
            print("vamos a enviar alarmas")
            await websocket.send(alarmas)
        elif datos_user_request["tipo_request"] == "delete_alarms":
            print("eliminar alarmas")
            data = datos_user_request["value"]
            token = data["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            rows_to_delete = data["rows_to_delete"]
            await delete_alarms(
                alarms_collection, user,
                rows_to_delete, avisos_collection
                )
            await websocket.send("Alarmas eliminadas")
        elif datos_user_request["tipo_request"] == "return_avisos":
            print("obtener avisos")
            data = datos_user_request["value"]
            token = data["token"]
            token = jwt.decode(token, secret_key, algorithms=["HS256"])
            user = token["user"]
            fecha_avisos = data["fecha_avisos"]
            lista_avisos = await return_avisos(
                avisos_collection,
                fecha_avisos,
                my_col,
                alarms_collection,
                user)
            lista_avisos = json.dumps(lista_avisos, default=str)
            await websocket.send(lista_avisos)
        await websocket.close()
    except websockets.exceptions.ConnectionClosedError:
        print("conexion cerrada por el client")


async def main(my_col, users_collection,
               root_user, root_pasword,
               secret_key, alarms_collection,
               avisos_collection):
    """ Función principal del server,
    lanza los procesos en background como async schedulers,
    es decir, insertar los daots de la API de weather stack,
    y crear los avisos (en un futuro los avisos pasarán a
    crearse cuando se añada un dato).
    Lanza el handler del server con webosckets.
    """
    await insert_user(root_user, root_pasword, users_collection)
    partial_handler = partial(
        receive_client_query_and_send_db_result,
        my_col,
        users_collection,
        secret_key,
        alarms_collection,
        avisos_collection
        )
    scheduler = AsyncIOScheduler()
    #ajustar a 21 * 3 datos al dia para 1000 request/mes
    # es decir cada 144 min
    scheduler.add_job(
        insert_api_data_in_mongo,
        "interval",
        minutes=207,
        args=[MY_DB, DATA_COLLECTION, "Vigo"]
        )
    scheduler.add_job(
        insert_api_data_in_mongo,
        "interval",
        minutes=207,
        args=[MY_DB, DATA_COLLECTION, "Madrid"]
        )
    scheduler.add_job(
        insert_api_data_in_mongo,
        "interval",
        minutes=207,
        args=[MY_DB, DATA_COLLECTION, "Lugo"]
        )
    scheduler.add_job(
        create_avisos,
        "interval",
        seconds=120,
        args=[alarms_collection, avisos_collection, DATA_COLLECTION]
        )
    scheduler.start()
    print("AÑADIDOS SCHEDULERS")
    async with websockets.serve(partial_handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main(
        DATA_COLLECTION, USERS_COLLECTION,
        ROOT_USER, ROOT_PASSWORD,
        SECRET_KEY,
        ALARMS_COLLECTION,
        AVISOS_COLLECTION
        ))
