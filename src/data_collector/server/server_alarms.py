#!/usr/bin/env python
""" Contiene las funciones relacionadas con
alarmas y notificaciones.
Funciones:
    - Añadir alarma (add_alarm)
    - Devolver alarmas (return_alarms)
    - Eliminar alarmas (delete_alarms)
    - Crear notificaciones (create_avisos)
    - Guardar una notificación (add_aviso)
    - Devolver notificaciones (return_avisos)
"""
import json
from datetime import datetime
from typing import List
from typing import Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from data_validation import Alarma
from data_validation import Avisos

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


async def add_alarm(alarms_collection: AsyncIOMotorCollection,
    user: str, data: Dict) -> str:
    """ Recibe los datos de la alarma, comprueba si
    ya existe y en caso negativo, la añade a la
    coleccion 'alarmas'
    """
    fecha_alarma = data.pop("fecha_alarma")
    fecha_alarma = datetime.strptime(fecha_alarma, "%Y-%m-%d %H:%M:%S")
    alarma_instance = Alarma(usuario=user, fecha_alarma=fecha_alarma, **data)
    query = {
        "usuario" : user,
        "tipo_alarma" : data["tipo_alarma"],
        "dato_afectado" : data["dato_afectado"],
        "ciudad" : data["ciudad"],
        "valor_alarma" : data["valor_alarma"],
        }
    alarma_from_db = await alarms_collection.find_one(query)
    if not alarma_from_db:
        await alarms_collection.insert_one(alarma_instance.dict())
        resultado = "Alarma añadida"
        print("Alarma añadida")
    else:
        resultado = "Ya existe esta alarma"
        print("Ya existe esta alarma")
    return resultado
async def return_alarms(alarms_collection: AsyncIOMotorCollection,
    user: str) -> str:
    """ Recibe el nombre de usuario, busca las
    alarmas que tenga asociadas y las devuelve
    """
    alarmas = alarms_collection.find({"usuario": user})
    alarmas = await alarmas.to_list(length=500)
    alarmas = json.dumps(alarmas, default=str)
    return alarmas

async def delete_alarms(alarms_collection: AsyncIOMotorCollection,
    user: str, rows_to_delete: List,
    avisos_collection: AsyncIOMotorCollection) -> None:
    """ Recibe los datos de las alarmas a eliminar y las
    elimina de la db, elimina ademas sus avisos asociados
    """
    for row in rows_to_delete:
        query = {
            "usuario" : user,
            "tipo_alarma" : row[0],
            "dato_afectado" : row[1],
            "ciudad" : row[2],
            "valor_alarma" : float(row[3]),
            }
        print(f"la query es: {query}")
        alarma = await alarms_collection.find_one(query)
        alarma_id = alarma["_id"]
        alarma_id = ObjectId(alarma_id)
        query_borrar_aviso = {"id_alarma" : ObjectId(alarma_id)}
        await avisos_collection.delete_many(query_borrar_aviso)
        await alarms_collection.delete_one(query)
async def create_avisos_event(alarms_collection: AsyncIOMotorCollection,
    avisos_collection: AsyncIOMotorCollection,
    data_collection: AsyncIOMotorCollection,
    api_response: Dict) -> None:
    """ Cada vez que se añade un dato a la db de Mongo,
    se lanza esta función.
    Comprueba todas las alarmas creadas y, si corresponde, crea un
    aviso asociado a ese par dato-alarma
    """
    print("añadir avisos para el ultimo dato")
    alarmas = alarms_collection.find()
    alarmas = await alarmas.to_list(length=100000)
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
    dato = await data_collection.find_one(query)
    if dato:
        for alarm in alarmas:
            ciudad = alarm["ciudad"]
            if ciudad == api_response["location"]["name"]:
                id_alarma = alarm["_id"]
                tipo_alarma = alarm["tipo_alarma"]
                dato_afectado = alarm["dato_afectado"]

                valor_alarma = alarm["valor_alarma"]
                fecha_alarma = alarm["fecha_alarma"]
                usuario = alarm["usuario"]

                medida_id = dato["_id"]
                fecha_dato = api_response["location"]["localtime"]
                valor_aviso = api_response["current"][dato_afectado]
                query = {
                    "id_alarma" : ObjectId(id_alarma),
                    "medida_id" : ObjectId(medida_id),
                    }
                document = await avisos_collection.find_one(query)
                if not document:
                    aviso_obj = Avisos(
                        id_alarma=ObjectId(id_alarma),
                        medida_id=ObjectId(medida_id),
                        usuario=usuario,
                        valor_alarma=valor_alarma,
                        fecha_alarma=fecha_alarma,
                        tipo_alarma=tipo_alarma,
                        dato_afectado=dato_afectado,
                        ciudad=ciudad,
                        fecha_dato=fecha_dato,
                        valor_aviso=valor_aviso,
                        revisado=False
                        )
                    await add_aviso(
                        avisos_collection, aviso_obj
                        )
                else:
                    print("aviso ya creado")

async def create_todos_los_avisos(alarms_collection: AsyncIOMotorCollection,
    avisos_collection: AsyncIOMotorCollection,
    data_collection: AsyncIOMotorCollection) -> None:
    """ Crea las notificaciones de todas las
    alarmas, lee los datos de la API almacenados en la db,
    comprueba si corresponde crear una notificacion, comprueba
    si ya existe una notificacion igual y la crea si es necesario
    Por tanto, crea todos los avisos de manera historica
    """
    print("vamos a añdir avisos")
    alarmas = alarms_collection.find()
    alarmas = await alarmas.to_list(length=100000)
    datos = data_collection.find()
    datos = await datos.to_list(length=100000)
    for alarm in alarmas:
        id_alarma = alarm["_id"]
        tipo_alarma = alarm["tipo_alarma"]
        dato_afectado = alarm["dato_afectado"]
        ciudad = alarm["ciudad"]
        valor_alarma = alarm["valor_alarma"]
        fecha_alarma = alarm["fecha_alarma"]
        usuario = alarm["usuario"]
        for dato in datos:
            try:
                dato["location"]
                medida_id = dato["_id"]
                fecha_dato = dato["location"]["localtime"]
                valor_aviso = dato["current"][dato_afectado]
            except KeyError:
                continue
            if dato["location"]["name"] == ciudad:
                query = {
                    "id_alarma" : ObjectId(id_alarma),
                    "medida_id" : ObjectId(medida_id),
                    }
                document = await avisos_collection.find_one(query)
                if not document:
                    aviso_obj = Avisos(
                        id_alarma=ObjectId(id_alarma),
                        medida_id=ObjectId(medida_id),
                        usuario=usuario,
                        valor_alarma=valor_alarma,
                        fecha_alarma=fecha_alarma,
                        tipo_alarma=tipo_alarma,
                        dato_afectado=dato_afectado,
                        ciudad=ciudad,
                        fecha_dato=fecha_dato,
                        valor_aviso=valor_aviso,
                        revisado=False
                        )
                    await add_aviso(
                        avisos_collection, aviso_obj
                        )
    print("fin alarmas")

async def add_aviso(avisos_collection: AsyncIOMotorCollection,
    aviso_obj: Avisos) -> None:
    """ Añade un nuevo aviso a la db, una vez se ha
    comprobado en la funcion create_avisos, que se
    debe crear y que no existe uno igual
    """
    print("add aviso function")
    valor_dato_afectado = aviso_obj.valor_aviso
    tipo_alarma = aviso_obj.tipo_alarma
    valor_alarma = aviso_obj.valor_alarma
    if tipo_alarma == "Límite superior" \
    and valor_dato_afectado > valor_alarma:
        await avisos_collection.insert_one(aviso_obj.dict())
    elif tipo_alarma == "Límite inferior" \
    and valor_dato_afectado < valor_alarma:
        await avisos_collection.insert_one(aviso_obj.dict())

async def return_avisos(avisos_collection: AsyncIOMotorCollection,
    fecha_avisos: str,
    user: str) -> List[Dict]:
    """ Lee las notificacioens almacenadas en la db que
    estén asociados a unos datos a partir de cierta fecha
    que el user introduce en la GUI del cliente
    """
    query = {
        "usuario" : user,
        "revisado" : False,
        "fecha_dato" : {"$gt" : fecha_avisos}
        }
    avisos = avisos_collection.find(query)
    lista_avisos = await avisos.to_list(length=5000)
    return lista_avisos
