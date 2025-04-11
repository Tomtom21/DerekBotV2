# Use a Python 3.11 image as the base
FROM python:3.11-slim

WORKDIR /bot

COPY ../requirements.txt /bot

RUN pip install -r requirements.txt

COPY derek-bot /bot

COPY libs /bot/libs

CMD ["python", "derek_bot.py"]
