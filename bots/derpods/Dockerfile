# Use a Python 3.11 image as the base
FROM python:3.11-slim

WORKDIR /bot

RUN apt update && apt install -y ffmpeg

COPY ../requirements.txt /bot

RUN pip install -r requirements.txt

COPY bots/derpods /bot

COPY shared /bot/shared

RUN mkdir /bot/music_files

CMD ["python", "derpods.py"]
