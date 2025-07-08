# Using our base image with everything installed
FROM base:latest

COPY bots/derek-bot /bot

RUN mkdir /bot/tts_files

CMD ["python", "derek_bot.py"]
