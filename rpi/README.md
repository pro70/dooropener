# Setup Raspberry Pi Zero for Dooropener

For the dooropener project I use a Raspberry Pi Zero W and Raspberry Pi OS Lite as operating system. 

## Headless setup

After flashing the Raspberry Pi OS Lite to the SD card I added an empty file `ssh` to the boot drive to enable the ssh service.
Further I added a file `wpa_supplicant.conf` (see file in this folder and update WiFi credentials) with my local WiFi credentials to allow the Pi to connect to my Wifi without further interaction.

For a detailed instruction how to setup a headless Raspberry Pi see https://www.raspberrypi.org/documentation/configuration/wireless/headless.md.

Now, I can plug the card to the Pi and power it up.

### First 5 minutes

After boot up, I can find the IP of the Pi in my local router webinterface.
I connect to the Pi using ssh with `ssh pi@<ip>` and login with password "raspberry".

My fist action on each Pi is to make some configuration and update the password, using `sudo raspi-config`:

* update password
* update hostname to "dooropenerpi"
* boot to console, since there is no GUI needed for headless mode
* disable all interfaces except SSH, since all other interfaces are not needed for this project
* update locale and timezone
* update the raspi-config tool

After upating the settings it's time for a reboot.

#### Secure system

Next it's time to setup some basic security.

First I update the system and install the used tools:
`apt update ; apt upgrade -y ; apt install -y ufw fail2ban unattended-upgrades`

When the command is finished, it's time for a reboot.

The tool "fail2ban" needs no further attention. It will block an IP for a few minutes if it is trying to login in with wrong SSH credentials too often.

The tool "ufw" is a firewall. For this project I need SSH access and port 9000:
```
ufw allow ssh
ufw allow 9000
ufw enable
```

Last, it's a good idea to install security updates automatically, especially in this embedded context. This is reaised with "unattended-upgrades".
I just enabled the tool using `dpkg-configure -plow unattended-upgrades`. For more details see  https://www.stqu.de/joomla/de/raspberry-pi/90-pi-automatische-updates-unattended-upgrades.

#### Install additional tools

After another reboot its time to install some additional usefull tools. I always install some common helper tools, even if they are not required for this project:
`apt install wicd-curses vim tmux`

#### Install project requirements

To run the app, we need Python 3 and some additional Python libraries, therefore we need also pip3.
```
apt install python3 python3-pip
```

#### Config additional WLANs

For my local setup, it is also useful to add some additional WiFis and we should also encrypt the WiFi passwords.

I add all needed WiFis using:

```
wpa_passphrase <Wifi SSID> >> /etc/wpa_supplicant/wpa_supplicant.conf
```

This will append the necessary lines to the config file, but hide the password request. After pressing enter type the WiFi password and press enter again.

Finally, I have to clean up the `wpa_supplicant.conf` and delete the configs containing the not encrypted passwords.

### Config groups

I will run the service as user "pi" and therefore have to give pi the necessary rights to access the GPIO pins:
```
sudo usermod -a -G gpio pi
```
