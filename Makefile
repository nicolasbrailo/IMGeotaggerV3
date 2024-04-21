
run:
	bin/python3 ./main.py

system_deps_install:
	sudo apt-get install virtualenv
	sudo apt-get install libgtk-3-dev

py_deps_install:
	# We need to use a py version that makes CEF happy, which now is 3.7
	virtualenv -p "$(shell which python3.7)" .
	bin/pip install attrdict3
	bin/pip install wxpython
	bin/pip install pyexiv2
	bin/pip install cefpython3
	#bin/pip install pygtk

py_deps_install_macos: py_deps_install
	bin/pip install pyobjc


