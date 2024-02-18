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
from typing import Any
from datetime import datetime
from pydantic import BaseModel
# from pydantic import HttpUrl
from bson import ObjectId

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
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
    contrasenha: str
    tipo_user: str
class Condition(BaseModel):
    """ Comprueba los tipos del campo
    condition de la respuesta de la API
    """
    text: str
    icon: str
    code: int
class Location(BaseModel):
    """ Comprueba que los tipos de datos de la clave
    'location' de la respuesta de la API sean correctos
    """
    name: str
    country: str
    region: str
    lat: float
    lon: float
    tz_id : str
    localtime: str
    localtime_epoch: int
class Current(BaseModel):
    """ Comprueba que los tipos de datos de la clave
    'current' de la respuesta de la API sean correctos
    """
    last_updated_epoch: int
    last_updated: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: Condition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    vis_km: float
    vis_miles: float
    uv: float
    gust_mph: float
    gust_kph: float

class ApiData(BaseModel):
    """ Clase de validación principal
    de la respuesta de la API, emplea
    las clases Request, Location y Current
    ya que la respuesta contiene tres claves
    y dentro de cada una, otro diccionario
    En caso de ser correctos, la lectura de la API
    es almacenada en la coleccion 'api_data'
    """
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
    usuario: str
    valor_alarma: float
    fecha_alarma: datetime
    tipo_alarma: str
    dato_afectado: str
    ciudad: str
    fecha_dato: str
    valor_aviso: Any
    revisado: bool
    class Config:
        """ Configuracion para poder añadir
        el tipo Any a la clase Avisos
        """
        arbitrary_types_allowed = True
