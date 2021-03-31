# Dooropener

Doorbird WiFi dooropener with RPI zero and Shelly switches

* Prepare Raspberry Pi: [Rasperry Pi Setup](rpi/README.md)
* Install the app: [App Setup](app/README.md)

![hardware](https://github.com/pro70/dooropener/blob/main/images/IMG_1427.jpeg?raw=true)

![wiring](https://raw.githubusercontent.com/pro70/dooropener/main/images/IMG_1419.jpeg)

## The Dooropener service

The dooropener service is a Python script implementing a dooropener extension
for a Doorbird video door station.

The dooropener service is intended to run on a Raspberry Pi Zero W and is using
Shelly switches as actors.

The dooropener has two relais inputs, for the two Doorbird relais outputs, an
output as bell trigger and a set of status LEDs. When a relais input is
triggered, a http on call is triggered and a status LED is switched on. After
a cool down time a http off call is triggered, the status led is turned off
and input listening starts again.

In addition, the dooropener offers a web API and a status page. The API can be
used to trigger the bell output. The API URL can be configured in the Doorbird
app to be triggered when the bell button is pressed.

The dooropener operates also two status LEDs showing if the service is running
and if an online connection is available.

The config page of the dooropener service is reachable as http://<pi ip>:9000.
The api of the dooropener service is reachable as http://<pi ip>:9000/api.
  
The api offers the following services:

* status: http://<pi ip>:9000/api/status
* single config value: http://<pi ip>:9000/api/status/<name>
* update config value: 
  * POST: http://<pi ip>:9000/api/status/<name>
  * GET: http://<pi ip>:9000/api/status/<name>/<value>
* trigger door bell virtual relais: http://<pi ip>:9000/api/action/bell
* trigger door bell output (beeper):
  * http://<pi ip>:9000/api/action/honk
  * http://<pi ip>:9000/api/action/honk/<time>


