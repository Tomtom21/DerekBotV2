# Use a Python 3.11 image as the base
FROM python:3.11-slim
WORKDIR /bot

# Install ffmpeg and git (temporarily)
RUN apt-get update && apt-get install -y ffmpeg git
COPY ../requirements.txt /bot
RUN pip install -r requirements.txt

# Adding temporary build of discord.py to resolve some issues
RUN git clone https://github.com/Rapptz/discord.py /bot/discord-py-build-dir
WORKDIR /bot/discord-py-build-dir
RUN pip install -U .[voice]
WORKDIR /bot

# Adding the shared files
COPY shared /bot/shared
