.PHONY: install clean venv test-install test

PORT=8008

clean:
	rm -rf venv

venv:
	virtualenv venv

install: venv
	. venv/bin/activate; pip install . --upgrade --download-cache /tmp/pipcache
	@echo "\033[95m\n\nInstalled! Add ${PWD}/venv/bin to your \$$PATH to use the http command.\n\033[0m"

test-install: venv
	# Stupidly httpbin stopped including a setup.py file two months ago making
	# the normal pip install process impossible with HEAD. Until then install
	# the last git commit that works. For more see 
	# https://github.com/kennethreitz/httpbin/pull/111#issuecomment-24450148
	if [ ! -d venv/build/httpbin ]; then \
		git clone https://github.com/kennethreitz/httpbin.git venv/build/httpbin; \
		. venv/bin/activate; pip install -r venv/build/httpbin/requirements.txt \
			--download-cache /tmp/pipcache; \
	fi
	. venv/bin/activate; pip install -r requirements-dev.txt \
		--download-cache /tmp/pipcache

test:
	. venv/bin/activate; python venv/build/httpbin/manage.py runserver -p $(PORT) &
	- . venv/bin/activate; HTTPBIN_URL=http://127.0.0.1:$(PORT) python setup.py test
	- . venv/bin/activate; HTTPBIN_URL=http://127.0.0.1:$(PORT) tox
	@# We need to kill the django process as well as its subprocesses.
	kill -9 `pgrep -f "venv/build/httpbin/manage.py runserver -p $(PORT)"`
