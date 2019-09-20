.PHONY: build deb appimage

build:
	@python3 setup.py bdist_wheel
	@pip3 install . --upgrade --target app
	@python3 -m zipapp -p "/usr/bin/env python3" -m "resticrc.console:cli" app

deb:
	make build
	@cp app.pyz deb/usr/bin/resticrc
	@sh -c 'dpkg-deb --build deb'

appimage:
	@echo Not supported yet.

