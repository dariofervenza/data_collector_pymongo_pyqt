from motor.motor_asyncio import AsyncIOMotorClient

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
