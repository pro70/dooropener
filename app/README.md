# Dooropener app

The dooropener app is intended to run as a service on a Raspberry Pi Zero which is wired with the relais outputs of a Doorbird video door station.

## Install the app on the Pi

Follow these steps to install the app and setup the service.

* Clone the git repo

```
git clone ...
```

* Check your paths in <repo>/app/dooropener.service
* Install the service file

```
sudo cp <repo>/app/dooropener.service /etc/systemd/system
```

* Test the service

```
sudo systemctl start dooropener
sudo systemctl status dooropener
```

and the web interface: http//<ip>:9000
  
* Enable the service

```
sudo systemctl enable dooropener
```

## Issues and mitigations

### Lost WiFi connection

I had the issue that my Pi lost the WiFi connection over night. As mitigatiom measure I added a
offline counter to the dooropener service and trigger a system reboot when the app detects a
WiFi failure for more than 5 minutes.
