# Use a Python 3.11 image as the base
FROM python:3.11-slim

WORKDIR /bot

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

COPY ../requirements.txt /bot

RUN pip install -r requirements.txt

COPY bots/derek-bot /bot

COPY shared /bot/shared

RUN mkdir /bot/tts_files

CMD ["python", "derek_bot.py"]
