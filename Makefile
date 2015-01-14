all:
	zip -r ~/kagi.zip *.py */*.py
	echo "#!/usr/bin/python3" | cat - ~/kagi.zip > ~/run
	chmod +x ~/run
	rm ~/kagi.zip
