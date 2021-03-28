# Setup Dooropener RPI

## OS:

Raspberry Pi OS Lite on RPI Zero W

## Basic Setup:

Headless setup: https://www.raspberrypi.org/documentation/configuration/wireless/headless.md

### First 5 minutes

* Check Router for RPI IP
* ssh pi@y<ip>, password: raspberry
* sudo raspi-conifg
* update password
* update hostname: dooropenerpi
* boot to console
* disable all interfaces except SSH
* update locale
* update timezone
* expand filesystem
* update

Reboot

### Install basic server tools:

* ufw
* fail2ban
* unattended-updates: https://www.stqu.de/joomla/de/raspberry-pi/90-pi-automatische-updates-unattended-upgrades

### Install additional tools:

* wicd-curses
* python3

### Config additional WLANs

* edit wpa_supplicant conf
* encrypt all wlan passwords using wpa_passphrase

### Setup Python and libs
 
* sudo apt install python3-gpiozero
* sudo usermod -a -G gpio pi
* sudo apt install python3-requests






