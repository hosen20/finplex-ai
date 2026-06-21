.PHONY: infra-up infra-down infra-reset api admin model-server guardrails workers health lint test evals quality

infra-up:
	./infra/scripts/start-infra.sh

infra-down:
	./infra/scripts/stop-infra.sh

infra-reset:
	./infra/scripts/reset-infra.sh

api:
	./scripts/dev-api.sh

admin:
	./scripts/dev-admin.sh

model-server:
	./scripts/dev-model-server.sh

guardrails:
	./scripts/dev-guardrails.sh

workers:
	./scripts/dev-workers.sh

health:
	./scripts/check-health.sh

lint:
	./scripts/lint.sh

test:
	./scripts/test.sh

evals:
	./scripts/run-evals.sh

quality:
	./scripts/check-secrets.sh
	./scripts/lint.sh
	./scripts/test.sh
	./scripts/run-evals.sh
