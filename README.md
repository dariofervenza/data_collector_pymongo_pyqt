[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/dariofervenza/data_collector_pymongo_pyqt">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Weather data collector client-server application</h3>

  <p align="center">
    An awesome application to gather data from weatherapi.com and check it with a pyqt5 GUI
    <br />
    <a href="https://github.com/dariofervenza/data_collector_pymongo_pyqt"><strong>Explore the code »</strong></a>
    <br />
    <br />
    <a href="https://github.com/dariofervenza/data_collector_pymongo_pyqt/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/dariofervenza/data_collector_pymongo_pyqt/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://www.linkedin.com/in/dario-fervenza-garcia-602051172/)

I wanted to try pyQt for months but I couldn´t find an oportunity in my job. So finally I decided to give it a try!  
This application is made to collect data from the WeatherAPI service and analyse it with machine learning.  
It has a server made with websockets and a client made with pyqt5!  
I want to experiment with different technologies and increase my coding experience. That said, If you see this and you want to help me, you are welcome!  
Project is in Spanish so you may not understand all the variable names.

Main components of my application:
* A RabbitMQ server to handle data from the API using a queue + another queue to schedule tasks with celery
* A celery server that periodically computes weather forecasting using skforecast and times series data
* A reddis container that stores the serialized figures with the historical data + forecasts
* A mongoDB server where weather data is stored and also where alarms created by the user are saved
* A websockets server that handles client GUI's requests, retrieves data from the database and sends it to the pyqt5 client
* A GUI client where the final user can check the weather data, filter it, set alarms, receive notifications and more!

Here you can see how I connected all these components in a diagram:

[![Product Name Screen Shot][product-diagram]]([https://www.linkedin.com/in/dario-fervenza-garcia-602051172/](https://github.com/dariofervenza/data_collector_pymongo_pyqt/blob/redis/images/DIAGRAMA.drawio.svg))

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With


* [![Python][Python]][Python-url]
* [![PyQt][PyQt]][PyQt-url]
* [![WebSockets][WebSockets]][WebSockets-url]
* [![RabbitMQ][RabbitMQ]][RabbitMQ-url]
* [![Celery][Celery]][Celery-url]
* [![Matplotlib][Matplotlib]][Matplotlib-url]
* [![Skforecast][Skforecast]][Skforecast-url]
* [![Redis][Redis]][Redis-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

1. Get a free API Key at [https://www.weatherapi.com/](https://www.weatherapi.com/)
2. Create the `src\data_collector\server\.env` file and insert your API key 
   ```sh
   API_KEY = "super_secret_key"
   ```

### Prerequisites

I couldn`t create yet the deployment process for a containerized solution so, for now, I only have instructions for Windows machines.

* mongoDB
   - Install mongo db on your pc
* redisContainer
   ```sh
   docker run --name redis-server -p 6379:6379 -d redis
   ```
* RabbitMQ
   - Install rabbitMq on your pc
* Python dependencies
   ```sh
   pip install -r requirements.txt
   ```

### Installation

_In order to launch the application you need to do the following:_

1. Download the repo with `git clone https://github.com/dariofervenza/data_collector_pymongo_pyqt.git`
2. Launch the api_simulator with `python src\data_collector\server\api_simulator.py`
3. Launch the server with `python src\data_collector\server\server.py`
4. Launch the celery beat with:
    1. Navigate to the tasks.py folder with `cd  src\data_collector\celery`
    2. Launch the beat with `celery -A tasks beat --loglevel=INFO `
5. Launch the celery worker with:
    1. Navigate to the tasks.py folder with `cd  src\data_collector\celery`
    2. Launch the worker with `celery -A tasks worker -l INFO -P solo`
6. Launch the client with `python src\data_collector\client\client.py`

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Once client.py is launched, insert server address in the first form and click "Aceptar".
![Server form][server-input]

Insert the default user and password. You can modify it in the `src\data_collector\server\config.py` file. Be aware that there is not a user creation or modification form yet.  
![User form][user-input]

Now you are logged in, here you can see a few images of my application, the first one in the alarm settings screen:  
![Alarms configuration][config-alarms]

Visualizing weather data in a tabular style:  
![Weather data][weather-data]

Checking the notifications triggered by the alarms:
![Alarm notifications][notifications]

Forecasting:
![Backtest][backtest]


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [x] Re-do readme.md
- [x] Create an application diagram
- [ ] Design and implement a user creation / modification window
- [ ] Add Docker implementation tutorial
- [ ] Jwt token expiration date 
- [ ] Jwt token refinement
    - [ ] Expiration date
    - [ ] Token storage in redis
- [ ] Data anomaly detection
- [ ] New alarm types
- [ ] New data sources (MQTT)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Darío Fervenza García - dario.fervenza.garcia@gmail.com

Project Link: [https://github.com/dariofervenza/data_collector_pymongo_pyqt](https://github.com/dariofervenza/data_collector_pymongo_pyqt)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Some useful resorces

* [Best README.md template](https://github.com/othneildrew/Best-README-Template/blob/main/README.md)
* [Choose an Open Source License](https://choosealicense.com)
* [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[license-shield]: https://img.shields.io/badge/LICENSE-MIT-blue
[license-url]: https://github.com/dariofervenza/data_collector_pymongo_pyqt/blob/redis/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/dario-fervenza-garcia-602051172/
[product-screenshot]: images/screenshot.png
[product-diagram]: images/DIAGRAMA.drawio.svg
[server-input]: images/server_input.png 
[user-input]: images/user_input.png
[backtest]: images/backtest.png
[config-alarms]: images/config_alarms.png
[weather-data]: images/weather_data.png
[notifications]: images/notifications.png
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[PyQt]: https://img.shields.io/badge/PyQt5-41CD52?style=for-the-badge&logo=qt&logoColor=white
[PyQt-url]: https://doc.qt.io/qtforpython-6/
[WebSockets]: https://img.shields.io/badge/WebSockets-00BFFF?style=for-the-badge&logo=websocket&logoColor=white
[WebSockets-url]: https://websockets.readthedocs.io/en/stable/index.html
[RabbitMQ]: https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white
[RabbitMQ-url]: https://www.rabbitmq.com/
[Celery]: https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white
[Celery-url]: https://docs.celeryq.dev/en/stable/getting-started/introduction.html
[Matplotlib]: https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=graphpad-prism&logoColor=white
[Matplotlib-url]: https://matplotlib.org/
[Skforecast]: https://img.shields.io/badge/Skforecast-4CAF50?style=for-the-badge&logo=scikit-learn&logoColor=white
[Skforecast-url]: https://skforecast.org/0.13.0/index.html
[Redis]: https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white
[Redis-url]: https://redis.io/
