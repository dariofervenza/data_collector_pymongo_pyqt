#!/usr/bin/env python
""" Simula la entrada de datos y
los envia al cliente de RabbitMQ
"""

import json
import pika
import requests
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
print(f"secret key api: {API_KEY}")

def read_from_api(ciudad):
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key" : API_KEY,
        "q" : ciudad
        }
    api_result = requests.get(base_url, params=params)
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
	scheduler.add_job(read_from_api, "interval", minutes=20, args=["Vigo"])
	scheduler.add_job(read_from_api, "interval", minutes=20, args=["Lugo"])
	scheduler.add_job(read_from_api, "interval", minutes=20, args=["Madrid"])
	try:
		scheduler.start()
	except (KeyboardInterrupt, SystemExit):
		pass
