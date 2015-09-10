CURRENT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

all:
	zip -r ~/kagi.zip *.py */*.py
	echo "#!/usr/bin/python3" | cat - ~/kagi.zip > ~/start_robot
	chmod +x ~/start_robot
	rm ~/kagi.zip

doc:
	cd docs && make html

pages:
	git checkout master
	make doc
	cp -r docs/_build /tmp/master-build
	git checkout gh-pages
	cp -r /tmp/master-build/* .
	rm -rf /tmp/master-build
	git commit -am "Update documentation."
	git push
	git checkout $(CURRENT_BRANCH)
