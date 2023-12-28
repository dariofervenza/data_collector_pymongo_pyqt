#!/usr/bin/env python
""" Contiene los modelos de validacion de pydantic,
aqui pueden verse los campos de cada objecto
que se almacena en la db
Clases:
    - Datos de un user (Usuario)
    - Datos clave request (api) (Request)
    - Datos clave location (api) (Location)
    - Datos clave current (api) (Current)
    - Datos de la respuesta de la API (ApiData)
    - Datos de una alarma (Alarma)
    - Datos de un aviso (Avisos)
"""

from typing import List
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from bson import ObjectId

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.1.5"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


class Usuario(BaseModel):
    """ Valida que los tiposde los datos de
    usuario sean correctos. En caso afirmativo,
    se guardará en la coleccion 'usuarios'
    NOTA:
        Añadir tipo de usuario (admin, common_user)
        y funcionalidad para cambiar el tipos de user
        Los admins serían los unicos que pueden crear
        nuevos usuarios
    """
    usuario: str
    contraseña: str
class Request(BaseModel):
    """ Comprueba que los tipos de datos de la clave
    'request' de la respuesta de la API sean correctos
    """
    type: str
    query: str
    language: str
    unit: str
class Location(BaseModel):
    """ Comprueba que los tipos de datos de la clave
    'location' de la respuesta de la API sean correctos
    """
    name: str
    country: str
    region: str
    lat: str
    lon: str
    timezone_id: str
    localtime: str
    localtime_epoch: int
    utc_offset: str
class Current(BaseModel):
    """ Comprueba que los tipos de datos de la clave
    'current' de la respuesta de la API sean correctos
    """
    observation_time: str
    temperature: int
    weather_code: int
    weather_icons: List[HttpUrl]
    weather_descriptions: List[str]
    wind_speed: int
    wind_degree: int
    wind_dir: str
    pressure: int
    precip: float
    humidity: int
    cloudcover: int
    feelslike: int
    uv_index: int
    visibility: int
    is_day: str
class ApiData(BaseModel):
    """ Clase de validación principal
    de la respuesta de la API, emplea
    las clases Request, Location y Current
    ya que la respuesta contiene tres claves
    y dentro de cada una, otro diccionario
    En caso de ser correctos, la lectura de la API
    es almacenada en la coleccion 'api_data'
    """
    request: Request
    location: Location
    current: Current

class Alarma(BaseModel):
    """ Valida que los tipos de datos
    de una nueva alarma, la cual sera almacenada
    en la coleccion 'alarmas'
    """
    usuario: str # cambiar por ObjectId ¿?
    tipo_alarma: str
    dato_afectado: str
    ciudad: str
    valor_alarma: float
    fecha_alarma: datetime

class Avisos(BaseModel):
    """ Valida un nuevo aviso, en caso de ser correcto,
    se almacena en la coleccion 'avisos'
    El aviso contiene:
        _id de la alarma,
        _id del dato que genera la notificacion,
        si está revisado o no
    """
    id_alarma: ObjectId
    medida_id: ObjectId
    revisado: bool
    class Config:
        arbitrary_types_allowed = True