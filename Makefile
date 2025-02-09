IMAGE_NAME=derek-bot-image
CONTAINER_NAME=derek-bot-container

cleanContainers:
	docker rm -vf `docker ps -aq`

cleanImages:
	docker rmi -f `docker images -aq`

buildDerekBot:
	echo "Building derek-bot"
	docker build -t ${IMAGE_NAME} -f derek-bot/Dockerfile .

runDerekBot:
	echo "Running derek-bot"
	docker run -e PYTHONUNBUFFERED=1 --env-file ../DerekBotV2Creds/.env ${IMAGE_NAME}

testDerekBot: buildDerekBot runDerekBot


