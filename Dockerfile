FROM python:3-alpine

WORKDIR /usr/opt/tyd_bot

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ADD  cipher.py /usr/local/lib/python3.11/site-packages/pytube/cipher.py

COPY . .

EXPOSE 8080

CMD ["python3", "./main.py"]
