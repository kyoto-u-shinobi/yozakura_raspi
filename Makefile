CURRENT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

all:
	zip -r ~/kagi.zip *.py */*.py
	echo "#!/usr/bin/python3" | cat - ~/kagi.zip > ~/start_robot
	chmod +x ~/start_robot
	rm ~/kagi.zip

docs:
	cd docs
	make html

pages:
	git checkout master
	make docs
	cp -r docs/build /tmp/master-build
	git checkout gh-pages
	cp -r /tmp/master-build/* .
	git commit -m "Update documentation."
	git checkout $(CURRENT_BRANCH)
