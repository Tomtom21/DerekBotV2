BOTS := derek-bot

define build_template
build-$(1):
	@echo "Building $(1)"
	docker compose build $(1)
endef

# Generating custom build targets
$(foreach bot,$(BOTS),$(eval $(call build_template,$(bot))))

run-%:
	@echo "Running $*"
	docker compose up -d $*

stop-%:
	@echo "Stopping $*"
	docker compose stop $*

test-%: build-%
	@echo "Testing $*"
	docker compose up $*

cleanContainers:
	docker rm -vf $$(docker ps -aq)

cleanImages:
	docker rmi -f $$(docker images -aq)

secretScan:
	gitleaks detect --source=. --verbose
	trufflehog filesystem . --exclude_paths trufflehog-exclude-patterns.txt
