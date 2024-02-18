#!/usr/bin/env python
""" Modulo con las funciones necesarias
para realizar la autenticación en el server.
Funciones:
    - Crear hash de contraseña (generate_password_hash)
    - Comprobar si el hash es correcto (check_hashed_password)
    - Devolver usuario de la db (return_user)
    - Añadir un nuevo user en la db (insert_user)
    - Autenticar (autenticar)
"""
from typing import Dict
from datetime import datetime
from datetime import timedelta
import bcrypt
from motor.motor_asyncio import AsyncIOMotorCollection
from data_validation import Usuario

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"

def generate_password_hash(password: str) -> str:
    """ Crea un password hash para evitar
    almacenar las passwords de los users en plain text
    """
    hash_pass = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_pass

def check_hashed_password(password: str, hashed_password: str) -> bool:
    """ Comprueba si la contraseña introducida por
    el usuario en la GUI coincide con el hash almacenado
    en la db.
    """
    password_encoded = password.encode("utf-8")
    return bcrypt.checkpw(password_encoded, hashed_password)

async def return_user(username: str,
    users_collection: AsyncIOMotorCollection) ->Dict:
    """ Comprueba si existe en la db un usuario
    con el nombre introducido en la GUI. Devuelve
    el objecto con los datos del usuario
    """
    query = {"usuario" : username}
    result = await users_collection.find_one(query)
    return result

async def insert_user(username: str,
    password: str, users_collection,
    tipo_user: str) -> None:
    """ Añade un usuario nuevo, comprueba primero si ya existe uno
    con igual username.
    Genera el hash de la contraseña y lo guarda en la db
    """
    user = await return_user(username, users_collection)
    if user:
        print("no añadido root user")
    else:
        hashed_password = generate_password_hash(password)
        query = {"usuario" : username, "contrasenha" : hashed_password, "tipo_user" : tipo_user}
        usuario_obj = Usuario(**query)
        await users_collection.insert_one(usuario_obj.dict())
        print("añadido root user")


async def autenticar(user_dict: Dict,
    users_collection: AsyncIOMotorCollection) -> Dict:
    """ Recibe los datos de usuario que se han introducido
    en la GUI en forma de diccionario, comprueba si existe
    y confirma que el password coincide con su hash
    Devuelve un diccionario en forma de
    {"autenticado" : True/False}
    Si es True, ese diccionario devuelve ademas el user _id
    y el nombre de usuario para posteriormente generar
    un token con pyjwt
    """
    user = user_dict.get("usuario")
    password = user_dict.get("contrasenha")
    user = await return_user(user, users_collection)
    if user:
        hashed_password = user["contrasenha"].encode("utf-8")
        crear_token = check_hashed_password(password, hashed_password)
        if crear_token:
            fecha_caducidad_token = datetime.now() + timedelta(days=1)
            fecha_caducidad_token = fecha_caducidad_token.strftime("%Y-%m-%d %H:%M:%S")
            result = {
                "autenticado" : True,
                "sub" : str(user["_id"]),
                "user" : user["usuario"],
                "fecha_caducidad" : fecha_caducidad_token
                }
        else:
            result = {"autenticado" : False}
    else:
        result = {"autenticado" : False}
    return result
def check_fecha_caducidad_token(token: str) -> bool:
    """ Comprueba si un token de jwt ha expirado y devuelve
    un booleano como respuesta, False si no es válido
    """
    now = datetime.now()
    fecha_caducidad = token["fecha_caducidad"]
    fecha_caducidad = datetime.strptime(fecha_caducidad, "%Y-%m-%d %H:%M:%S")
    result = bool(now < fecha_caducidad)
    return result
