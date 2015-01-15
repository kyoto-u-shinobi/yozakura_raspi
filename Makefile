all:
	zip -r ~/kagi.zip *.py */*.py
	echo "#!/usr/bin/python3" | cat - ~/kagi.zip > ~/start_robot
	chmod +x ~/start_robot
	rm ~/kagi.zip
