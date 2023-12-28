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
from bson import ObjectId

from data_validation import Alarma
from data_validation import Avisos

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.1.5"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


async def add_alarm(alarms_collection, user, data):
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
async def return_alarms(alarms_collection, user):
    """ Recibe el nombre de usuario, busca las
    alarmas que tenga asociadas y las devuelve
    """
    alarmas = alarms_collection.find({"usuario": user})
    alarmas = await alarmas.to_list(length=500)
    alarmas = json.dumps(alarmas, default=str)
    return alarmas

async def delete_alarms(alarms_collection, user, rows_to_delete, avisos_collection):
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
async def create_avisos(alarms_collection, avisos_collection, data_collection):
    """ Crea las notificaciones de todas las
    alarmas, lee los datos de la API almacenados en la db,
    comprueba si corresponde crear una notificacion, comprueba
    si ya existe una notificacion igual y la crea si es necesario
    """
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
        for dato in datos:
            medida_id = dato["_id"]
            try:
                dato["location"]
            except KeyError:
                continue;
            if dato["location"]["name"] == ciudad:
                query = {
                    "id_alarma" : ObjectId(id_alarma),
                    "medida_id" : ObjectId(medida_id),
                    }
                document = await avisos_collection.find_one(query)
                if not document:
                    valor_dato_afectado = dato["current"][dato_afectado]
                    aviso_obj = Avisos(
                        id_alarma=ObjectId(id_alarma),
                        medida_id=ObjectId(medida_id),
                        revisado=False
                        )
                    await add_aviso(
                        avisos_collection, aviso_obj, tipo_alarma,
                        valor_dato_afectado, valor_alarma
                        )
async def add_aviso(avisos_collection, aviso_obj,
                    tipo_alarma, valor_dato_afectado,
                    valor_alarma):
    """ Añade un nuevo aviso a la db, una vez se ha
    comprobado en la funcion create_avisos, que se
    debe crear y que no existe uno igual
    """
    if tipo_alarma == "Límite superior" \
    and valor_dato_afectado > valor_alarma:
        await avisos_collection.insert_one(aviso_obj.dict())
    elif tipo_alarma == "Límite inferior" \
    and valor_dato_afectado < valor_alarma:
        await avisos_collection.insert_one(aviso_obj.dict())

async def return_avisos(avisos_collection, fecha_avisos,
                        data_collection, alarms_collection,
                        user):
    """ Lee las notificacioens almacenadas en la db que
    estén asociados a unos datos a partir de cierta fecha
    que el user introduce en la GUI del cliente
    """
    query = {"location.localtime" : {"$gt" : fecha_avisos}}
    datos_afectados = data_collection.find(query)
    datos_afectados = await datos_afectados.to_list(length=500)
    lista_avisos = []
    for dato in datos_afectados:
        dato_id = dato["_id"]
        query = {"revisado" : False, "medida_id" : ObjectId(dato_id)}
        avisos = avisos_collection.find(query)
        avisos = await avisos.to_list(length=500)
        for aviso in avisos:
            query_alarma = {"_id" : ObjectId(aviso["id_alarma"])}
            alarma_obj = await alarms_collection.find_one(query_alarma)
            usuario = alarma_obj["usuario"]
            if usuario == user:
                aviso["valor_alarma"] = alarma_obj["valor_alarma"]
                aviso["fecha_alarma"] = alarma_obj["fecha_alarma"]
                aviso["tipo_alarma"] = alarma_obj["tipo_alarma"]
                aviso["dato_afectado"] = alarma_obj["dato_afectado"]
                aviso["ciudad"] = alarma_obj["ciudad"]
                query_dato = {"_id" : ObjectId(aviso["medida_id"])}
                dato_obj = await data_collection.find_one(query_dato)
                fecha_dato = dato_obj["location"]["localtime"]
                aviso["fecha_dato"] = fecha_dato
                dato_afectado = aviso["dato_afectado"]
                aviso["valor_aviso"] = dato_obj["current"][dato_afectado]
                lista_avisos.append(aviso)
    return lista_avisos
