FROM sourceperl/py3-scipy-np:arm32v6-latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./check-pid-learning.py" ]
