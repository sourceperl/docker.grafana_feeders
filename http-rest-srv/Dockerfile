FROM python:3.9-buster

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
COPY app.py ./

CMD [ "python", "./app.py" ]
