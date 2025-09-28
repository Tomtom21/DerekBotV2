BOTS := derek-bot placeholder-bot derpods

build-base:
	docker build -f base.Dockerfile -t base:latest .

build-base-no-cache:
	docker build -f base.Dockerfile -t base:latest . --no-cache

define build_template
build-$(1): build-base
	@echo "Building $(1)"
	docker compose build $(1)
endef

define no_cache_build_template
no-cache-build-$(1): build-base-no-cache
	@echo "Building $(1), ignoring cache"
	docker compose build $(1)
endef

# Generating custom build targets
$(foreach bot,$(BOTS),$(eval $(call build_template,$(bot))))
$(foreach bot,$(BOTS),$(eval $(call no_cache_build_template,$(bot))))

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
