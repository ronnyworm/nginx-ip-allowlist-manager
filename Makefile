
check-venv:
	@if [ -z "$(VIRTUAL_ENV)" ]; then \
		echo "No virtual environment is active. Please activate it first."; \
		exit 1; \
	else \
		echo "Virtual environment is active at $(VIRTUAL_ENV)"; \
	fi

test: check-venv
	pytest --show-capture=no test_expire_ips.py -s
