# Use a Python 3.11 image as the base
From python:3.11-slim

WORKDIR /bot

COPY ../requirements.txt .

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

