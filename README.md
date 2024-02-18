# DATA COLLECTOR V2

Hello this is my second attempt to solve a problem I was asked. I wanted to try pyQt for months but I couldn´t find an oportunity in my job. So finally I decided to give it a try!

Project is in Spanish so you may not understand all the variable names. I usually mix english with spanish when naming objects and variables.

## Purpose of the project

This application is made to collect data from the WeatherAPI service and analyse it with machine learning\
It has a server made with websockets and a client
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

The client has a tool bar to display the different widgets. For the moment, I created a mainwidget which is the default page (It does not have a concrete purpose, just presentation). I also created a graphs widget were the data is displayed using plotly and also there is a table so you can see the values. Another widget is the alarms one, where users can create or delete alarms. In that widget it will appear The notifications that these alarms create. But its not implemented for the moment.

### Change log

2023-27-12:\
	Improved client auth widget: Now it asks the server address and it sends messages if there is an error\
	Improved client alarms widget: Added a field where you can introduce the date after which you can display the notifications\
2023-28-12:\
	Added forecasting single series widget (client)\
2023-29-12:\
	Added backtesting single series widget (client)\
2024-14-01:\
	Changed design to fluent design (not finished yet though)\
	Redesigned Graphs widget - now you can add, remove and resize plots\
	Solved a bug where you couldn't move the vertical scroll bar\
2024-21-01:\
	Switched to weatherapi.com API\
        Continued implementing fluentDesign (not finished)\
        More UI changes\
2024-11-02:\
	Patched some bugs\
	Improved UI\
	Added dotenv to protect the secret key\
	Added rabitMQ to decouple api response from the server\
	Now the analytics figures are stored in a redis db\
	Now alarm notifications are created when the data is added to the db\
	Some other minor changes\
2024-18-02:\
	Added filter functions to graphs widget
	Improved code with pylint
	Added MIT license
	


### Future features


Add a diagram to explain the app functionality in the github page + some images of the app in the readme.md file\
Add a tutorial to deploy the app in docker\
Add a new feature in the server that checks the expiration date of the token that is sent to the client (added but its not working yet)\
Change user feature + show user data + create new user\
Add qthreads to prevent app from freezing when reloading data\
Outliers detection system\
New alarms based on the forecasting results and the outliers detector\
Finally I want to try paho mqtt lib so I may create a new data source using that protocol

## Installation

Create a new environment with "python -m venv my_env" and install requirements with "pip install -r requirements.txt". Then launch the env and open the server with "python server.py".
Lastly, launch the client with "python client.py"

