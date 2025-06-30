BOTS := derek-bot luca

define build_template
build-$(1):
	@echo "Building $(1)"
	docker build -t $(1)-image -f bots/$(1)/Dockerfile .
endef

# Generating custom build targets
$(foreach bot,$(BOTS),$(eval $(call build_template,$(bot))))

run-%:
	@echo "Running $*"
	docker run -e PYTHONUNBUFFERED=1 --env-file ../DerekBotV2Creds/.env $*-image

test-%: build-% run-%
	@:

cleanContainers:
	docker rm -vf $$(docker ps -aq)

cleanImages:
	docker rmi -f $$(docker images -aq)

secretScan:
	gitleaks detect --source=. --verbose
	trufflehog filesystem . --exclude_paths trufflehog-exclude-patterns.txt
