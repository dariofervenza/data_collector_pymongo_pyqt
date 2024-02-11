FROM python:3.11
WORKDIR /server
COPY /src/data_collector/server /server
COPY /requirements.txt /server
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8765
CMD ["python", "server.py"]
