#!/usr/bin/env python
""" Guarda los datos de
configuracion, como las colecciones de
Mongo usadas y la secret key para los tokens
de jwt-python
"""
from motor.motor_asyncio import AsyncIOMotorClient
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
USERS_COLLECTION = MY_DB["usuarios"]
ALARMS_COLLECTION = MY_DB["alarmas"]
AVISOS_COLLECTION = MY_DB["avisos"]
ROOT_USER = "paco"
ROOT_PASSWORD = "paco"

SECRET_KEY = "SuPer_SEcret_kEY"
LISTA_CIUDADES = ("Vigo", "Lugo", "Madrid")
