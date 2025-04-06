FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install --no-cache-dir python-telegram-bot==20.7 moviepy==1.0.3

WORKDIR /app
COPY . /app

CMD ["python", "main.py"]
