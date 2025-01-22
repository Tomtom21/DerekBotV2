@echo off

:: Setting variables
set IMAGE_NAME=derek-bot-image
set CONTAINER_NAME=derek-bot-container

:: Building the image
echo Building the Docker image...
docker build -t %IMAGE_NAME% -f derek-bot/Dockerfile .

:: Running the container
echo Running Docker container...
docker run -e PYTHONUNBUFFERED=1 --env-file .env %IMAGE_NAME%
