PROJECT := backup

install:
	mkdir -p /root/scripts/$(PROJECT)
	cp ./main.py /root/scripts/$(PROJECT)/
	cp ./$(PROJECT).service /etc/systemd/system/
	cp ./$(PROJECT).timer /etc/systemd/system/
	systemctl daemon-reload

uninstall:
	rm -f /etc/systemd/system/$(PROJECT).service
	rm -f /etc/systemd/system/$(PROJECT).timer
	rm -rf /root/scripts/$(PROJECT)
	systemctl daemon-reload
	

