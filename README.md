# DATA COLLECTOR V2

Hello this is my second attempt to solve a problem I was asked. I wanted to try pyQt for months but I couldn´t find an oportunity in my job. So finally I decided to give it a try!

Project is in Spanish so you may not understand all the variable names. I usually mix english with spanish when naming objects and variables.

## Purpose of the project

The main goal is educational, I do not want to build the best possible application so others could use it.\
I want to experiment with different technologies and increase my coding experience. That said, If you see this and you want to help me, you are welcome!

## Requirements for the project

Create a logging system where different users have different permissions or features\
Read data from an API or an MQTT device\
Display the data in real time + historical data\
Create an alarms system where users can define which variables they want to be alerted when it passes a threshold\
Add machine learning to detect outliers in the data provided by the API\
Any other suggestion the developed consider adding

## My second solution

The application is a server-client one. Where the server collects data from the weatherstack API and stores it in a MongoDB database.\
It uses websockets to communicate with the client. The server also is in charge of user authentication and alarms, so the server handles all interaction with the db.\
The server uses pydantic to validate the data that is sent, dataclasses are stored in a separate module.

The client is a GUI made with pyQt5. It starts with an auth window. The root user is "paco" and the password is the same. This user is created automatically. After loggin in, the server creates a jwt token that is send to the client. This token will be used later when an user creates an alarm, so the server can identify who created the alarm.

The client has a tool bar to display the different widgets. For the moment, I created a mainwidget which is the default page (It does not have a concrete purpose, just presentation). I also created a graphs widget were the data is displayed using plotly and also there is a table so you can see the values. Another widget is the alarms one, where users can create or delete alarms. In that widget will appear The notifications that these alarms create. But its not implemented for the moment.

### Change log

2023-27-12:\
	Improved client auth widget: Now asks the server address and sends messages if there is an error\
	Improved client alarms widget: Added a fields where you can introduce the date after which you can display the notifications

### Future features

I want to experiment with machine learning forecasting so I will add a skforecast feature (I tried that library in the past so it will come soon). I would also like to implement an outliers detector system.
Finally I want to try paho mqtt lib so I may create a new data source using that protocol

## Installation

Create a new environment with "python -m venv my_env" and install requirements with "pip install -r requirements.txt". Then launch the env and open the server with "python server.py".
Lastly, launch the client with "python client.py"

