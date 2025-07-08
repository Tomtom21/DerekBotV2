# Using our base image with everything installed
FROM base:latest

COPY bots/derpods /bot

RUN mkdir /bot/music_files

CMD ["python", "derpods.py"]
