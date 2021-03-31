# Dooropener app

The dooropener app is intended to run as a service on a Raspberry Pi Zero which is wired with the relais outputs of a Doorbird video door station.

## Install the app on the Pi

Follow these steps to install the app and setup the service.

* Clone the git repo

```
git clone ...
```

* Check your paths in <repo>/app/doorbird.service
* Install the service file

```
sudo cp <repo>/app/doorbird.service /etc/systemd/system
```

* Test the service

```
sudo systemctl start doorbird
sudo systemctl status doorbird
```

and the web interface: http//<ip>:9000
  
* Enable the service

```
sudo systemctl enable doorbird
```


