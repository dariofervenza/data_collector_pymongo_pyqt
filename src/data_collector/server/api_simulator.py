#!/usr/bin/env python
""" Simula la entrada de datos y
los envia al cliente de RabbitMQ
"""
import json
import os
import pika
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.2"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"

load_dotenv()
API_KEY = os.getenv("API_KEY")
print(f"secret key api: {API_KEY}")

def read_from_api(ciudad: str) -> None:
    """ Realiza peticion Http a la Api
    y envia el resultado a una cola de
    RabitMQ
    """
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key" : API_KEY,
        "q" : ciudad
        }
    api_result = requests.get(base_url, params=params, timeout=20)
    if api_result.status_code == 200:
        api_response = api_result.json()
    if api_response:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        mensaje = {"ciudad" : ciudad, "data" : api_response}
        mensaje = json.dumps(mensaje)
        channel = connection.channel()
        channel.queue_declare(queue='api')
        channel.basic_publish(exchange='', routing_key='api', body=mensaje)
        connection.close()
        print(f"añadido: {ciudad}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Vigo"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Lugo"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Madrid"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Barcelona"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Malaga"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Santander"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Oviedo"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Salamanca"])
    scheduler.add_job(read_from_api, "interval", minutes=60, args=["Bilbao"])
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
