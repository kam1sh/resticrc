# init: dh_make -s -c MIT -p resticrc_0.1.0 -e <email> -i -y

.PHONY: build zipapp deb appimage

build:
	python3 setup.py bdist_wheel

zipapp: build
	rm -rf app
	pip3 install . --upgrade --target app
	python3 -m zipapp -p "/usr/bin/env python3" -m "resticrc.console:cli" app
	mv app.pyz dist/resticrc
	rm -r app 

deb: zipapp
	dpkg-buildpackage -b -uc -uc
	sh -c 'rm -rf resticrc_2019*'

appimage:
	@echo Not supported yet.

