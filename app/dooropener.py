#!/usr/bin/python3
"""
This file implements the dooropener service.


The dooropener service is intended to run on a Raspberry Pi Zero W and extend
a Doorbird video door unit with a wireless door opener and bell, using Shelly
switches as actors.

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
"""

import requests
import time
import logging
import json
import urllib.parse
import os.path
import os
from flask import Flask, request, send_from_directory
from threading import Thread
from gpiozero import Button, LED
from waitress import serve


class Relais:
    """
    This class implements a relais input and its behavior.

    A relais listen to a GPIO pin and triggers a http action call when the
    input is triggered. After a cool down time another http action call is
    triggered and listening is started again.

    Parameters:
    -----------
    in_pin: int
        relais input pin
    signal_pin: int
        status LED pin
    name: string
        relais name for logging
    on_time: int, default 5
        hot time after input is triggered
    on_url: string, default is None
        http URL which is triggered on signal
    off_url: string, default is None
        http URL which is triggered after cool down time
    pull_up: boolean, default is False
        Use pull-up, see gpiozero doc for details. With default, buttons/input
        relais should be wired to +5V.
    """

    def __init__(self, in_pin, signal_pin, name, on_time=5,
                 on_url=None, off_url=None, pull_up=False):
        """
        Init the Relais object, using the given input pin, signal pin and name
        for logging.
        """
        self.on_time = on_time
        self.on_url = on_url
        self.off_url = off_url
        self.name = name
        self.run = True

        self.button = Button(in_pin, pull_up=pull_up)
        self.led = LED(signal_pin)

        self.led.off()

    def disable(self):
        """ Stop listening for input signals, after timeout ~1s. """
        self.run = False

    def _handler(self):
        """ Thread function to check for input. """
        logging.info(f"{self.name} - wait for press")
        while self.run:
            if self.button.wait_for_press(1):  # 1s timeout for run check
                self._button_pressed()
        logging.info(f"{self.name} - stopped")

    def _button_pressed(self):
        """ Handle input button pressed. """
        logging.info(f"{self.name} - pressed")
        if self.on_url:
            self._call(self.on_url)  # If on URL, trigger URL
        else:
            logging.warning(f"{self.name} - no on url")
        self.led.on()  # enable relais signal LED

        time.sleep(self.on_time)  # wait for cool down time

        if self.off_url:
            self._call(self.off_url)  # If on URL, trigger URL
        else:
            logging.warning(f"{self.name} - no off url")
        self.led.off()  # disable relais signal LED

        logging.info(f"{self.name} - cooled down")

    def _call(self, url):
        """ Call the action URL """
        r = requests.get(url)
        if r.status_code == 200:  # status code OK
            logging.info(f"{self.name} - call successful: {url}")
        else:
            logging.error(f"{self.name} - call failed: {url}")

    def enable(self):
        """ Start listening for input. """
        self.thread = Thread(target=self._handler)
        self.thread.start()  # listen using a thread to not block


class VirtualRelais:
    """
    This class implements a virtual relais.

    A virtual relais listen to a web action and triggers a http action
    call when the action URL is triggered. After a cool down time
    another http action call is triggered.

    Parameters:
    -----------
    name: string
        relais name for logging
    on_time: int, default 5
        hot time after input is triggered
    on_url: string, default is None
        http URL which is triggered on signal
    off_url: string, default is None
        http URL which is triggered after cool down time
    """

    def __init__(self, name, on_time=5, on_url=None, off_url=None):
        """
        Init the VirtualRelais object.
        """
        self.on_time = on_time
        self.on_url = on_url
        self.off_url = off_url
        self.name = name
        self.hot = False

    def _action(self):
        """ Handle action event. """
        logging.info(f"{self.name} - triggered")
        self.hot = True
        if self.on_url:
            self._call(self.on_url)  # If on URL, trigger URL
        else:
            logging.warning(f"{self.name} - no on url")

        time.sleep(self.on_time)  # wait for cool down time

        self.hot = False
        if self.off_url:
            self._call(self.off_url)  # If on URL, trigger URL
        else:
            logging.warning(f"{self.name} - no off url")

        logging.info(f"{self.name} - cooled down")

    def _call(self, url):
        """ Call the action URL """
        r = requests.get(url)
        if r.status_code == 200:  # status code OK
            logging.info(f"{self.name} - call successful: {url}")
        else:
            logging.error(f"{self.name} - call failed: {url}")

    def trigger(self):
        """ Process an action event. """
        if self.hot:
            logging.info(f"{self.name} - already hot, ingore event")
            return
        self.thread = Thread(target=self._action)
        self.thread.start()  # listen using a thread to not block


class Bell:
    """
    This class implements a bell and its behavior.

    A bell triggers a GPIO pin if "honk" is requested. It has a default honk
    time and also handles a signal LED.

    Parameters:
    -----------
    work_pin: int, default 16
        bell output pin
    signal_pin: int, default 26
        status LED pin
    honk_time: float, default 0.2
        default honk time
    """

    def __init__(self, work_pin=16, signal_pin=26, honk_time=0.2):
        """ Init bell with the given output pin and signal LED pin. """
        self.bell_on = LED(signal_pin)
        self.bell = LED(work_pin)
        self.honk_time = honk_time

    def _honk(self, honk_time=None):
        """
        Thread function to honk.

        Parameters:
        -----------
        honk_time: float or None, default None
            time to honk
        """
        if not honk_time:
            honk_time = self.honk_time

        logging.info(f'ringing the bell for {honk_time}s')
        self._on()
        time.sleep(honk_time)
        self._off()
        logging.info(f'bell ringed for {honk_time}s')

    def _on(self):
        """ turn on bell and signal LED """
        self.bell.on()
        self.bell_on.on()

    def _off(self):
        """ turn off bell and signal LED """
        self.bell.off()
        self.bell_on.off()

    def honk(self, time=None):
        """
        Ring th bell for the given time.

        Parameters:
        -----------
        time: float or None, default None
            honk time in seconds as float, None means use Bell default time
        """
        self.thread = Thread(target=self._honk, args=(time,))
        self.thread.start()


class LifeCheck:
    """
    This class implements the life check.

    The LifeChecks tests the online connection and signals the application and
    the online state.

    Parameters:
    -----------
    run_pin: int, default 5
        run LED pin
    wlan_pin: int, default 6
        WLAN LED pin
    online_time: float, default 60
        seconds between online check
    online_url: string, default "https://google.de"
        URL to call for online check
    """

    def __init__(self, run_pin=5, wlan_pin=6,
                 online_time=60, online_url="https://google.de"):
        """
        Init LifeCheck with the given pins, online time and online test URL.
        """
        self.online_time = online_time
        self.online_url = online_url
        self.running = LED(run_pin)
        self.wlan_ok = LED(wlan_pin)
        self.run = True
        self.offline_counter = 0

    def _life_check(self):
        """ Thread function for life check. """
        logging.info("Life check - started")
        while self.run:
            self.running.on()
            if self.online_url:
                self._online_check()
            else:
                logging.warning("WLAN check skipped")
                self.wlan_ok.off()

            time.sleep(self.online_time)

            # short off blink as life signal
            self.wlan_ok.off()
            self.running.off()
            time.sleep(.5)

        logging.info("Life check - stopped")

    def _online_check(self):
        """ execute the online check and update online status """
        logging.info("WLAN check ...")
        r = requests.get(self.online_url)
        if r.status_code == 200:
            logging.info("WLAN OK")
            self.wlan_ok.on()
        else:
            logging.error("WLAN failed!")
            self.offline_counter = self.offline_counter + 1
            self.wlan_ok.off()

        if self.offline_counter > 5:
            os.system('sudo reboot')

    def enable(self):
        """ Start life check. """
        self.thread = Thread(target=self._life_check)
        self.thread.start()

    def disable(self):
        """ Stop life check, after ~online check time. """
        self.run = False
        self.running.off()


class Dooropener:
    """
    This class groups the GPIO features of the dooropener.

    Components:
    -----------
    life_check: LifeCheck
        a LifeCheck instance
    relais1: Relais
        a Relais instance using pins 20 and 13
    relais2: Relais
        a Relais instance using pins 21 and 19
    bell: Bell
        a Bell instance
    bellAction: VirtualRelais
        a VirtualRelais to trigger a bell WLAN relais
    """

    def __init__(self):
        """ init Dooropener and all its components """
        self.life_check = LifeCheck()
        self.relais1 = Relais(20, 13, "Relais 1", on_time=3)
        self.relais2 = Relais(21, 19, "Relais 2", on_time=60)
        self.bell = Bell()
        self.bellAction = VirtualRelais("Bell Action", on_time=1)
        self.config_file = 'config.json'

        self._load_settings()

    def _load_settings(self):
        """ load settings from config file """
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file) as f:
                    data = json.loads(f.read())
                    for key, value in data.items():
                        self.update(key, value)
                        logging.info(f'Config: {key}={value}')
            except Exception as e:
                logging.error('Config load error!', e)
        else:
            logging.warning(f'Config file {self.config_file} not found.')

    def _save_settings(self):
        """ save settings to config file """
        try:
            with open(self.config_file, 'w') as f:
                f.write(json.dumps(self.config()))
        except Exception as e:
            logging.error('Config save error!', e)

    def start(self):
        """ enable all components """
        self.life_check.enable()
        self.relais1.enable()
        self.relais2.enable()

    def honk(self, honk_time=None):
        """ ring the bell """
        self.bell.honk(honk_time)

    def trigger_bell(self):
        """ trigger the bell action """
        self.bellAction.trigger()

    def stop(self):
        """ disable all components """
        print("Stop dooropener")
        self.life_check.disable()
        self.relais1.disable()
        self.relais2.disable()

    def config(self):
        return {
            'r1_on_url': self.relais1.on_url,
            'r1_off_url': self.relais1.off_url,
            'r1_time': self.relais1.on_time,
            'r2_on_url': self.relais2.on_url,
            'r2_off_url': self.relais2.off_url,
            'r2_time': self.relais2.on_time,
            'online_url': self.life_check.online_url,
            'online_time': self.life_check.online_time,
            'bell_time': self.bell.honk_time,
            'ba_on_url': self.bellAction.on_url,
            'ba_off_url': self.bellAction.off_url,
            'ba_time': self.bellAction.on_time,
        }

    def update(self, key, value):
        try:
            key = str(key)
            if value is not None:
                value = str(value)

            logging.info(f'update config value: {key}={value}')

            success = False
            if key == 'r1_on_url':
                self.relais1.on_url = value
                success = True
            elif key == 'r1_off_url':
                self.relais1.off_url = value
                success = True
            elif key == 'r1_time':
                self.relais1.on_time = float(value)
                success = True
            elif key == 'r2_on_url':
                self.relais2.on_url = value
                success = True
            elif key == 'r2_off_url':
                self.relais2.off_url = value
                success = True
            elif key == 'r2_time':
                self.relais2.on_time = float(value)
                success = True
            elif key == 'online_url':
                self.life_check.online_url = value
                success = True
            elif key == 'online_time':
                self.life_check.online_time = float(value)
                success = True
            elif key == 'bell_time':
                self.bell.honk_time = float(value)
                success = True
            elif key == 'ba_on_url':
                self.bellAction.on_url = value
                success = True
            elif key == 'ba_off_url':
                self.bellAction.off_url = value
                success = True
            elif key == 'ba_time':
                self.bellAction.on_time = float(value)
                success = True
            else:
                success = False

            if success:
                self._save_settings()

            return success
        except Exception as e:
            logging.error('Config update failed!', e)
            return False


# ---- Start of WEB API ----


def create_api(dooropener):
    app = Flask(__name__)

    @app.route('/api/status', methods=['GET'])
    def status():
        return json.dumps(dooropener.config())

    @app.route('/api/status/<key>', methods=['GET'])
    def get_value(key):
        values = dooropener.config()
        if key in values:
            if values[key] is None:
                return ''
            return f'{values[key]}'
        else:
            return 'not found', 404

    @app.route('/api/status/<key>', methods=['POST'])
    def update_value(key):
        try:
            if dooropener.update(key, str(request.data, 'utf-8')):
                return request.data
            else:
                return 'not found', 404
        except Exception as e:
            logging.error('update POST error', e)
            return 'not found', 404

    @app.route('/api/status/<key>/<value>', methods=['GET'])
    def get_update_value(key, value):
        value = urllib.parse.unquote(value)
        if dooropener.update(key, value):
            return value
        else:
            return 'not found', 404

    @app.route('/', defaults=dict(filename=None), methods=['GET'])
    @app.route('/<path:filename>', methods=['GET'])
    def index(filename):
        filename = filename or 'index.html'
        return send_from_directory('./static', filename)

    @app.route('/api/action/honk', defaults=dict(time=None), methods=['GET'])
    @app.route('/api/action/honk/<time>', methods=['GET'])
    def honk_action(time):
        if time:
            try:
                dooropener.honk(float(time))
                return f'beep {time}', 200
            except Exception as e:
                logging.error('honk action', e)
                return 'not found', 404
        dooropener.honk()
        return 'beep', 200

    @app.route('/api/action/bell', methods=['GET'])
    def bell_action():
        dooropener.trigger_bell()
        return 'ring', 200

    return app

# ---- End of WEB API ----


def mock_gpio():
    """ mock GPIO pins """
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory
    Device.pin_factory = MockFactory()
    logging.error("No GPIO detected! Mocking GPIO...")


def check_gpio():
    """ check if GPIO are available on the machine and use mocks if not """
    try:
        LED(16)
    except (ImportError, RuntimeError):
        mock_gpio()


def main_loop():
    """ starts app an loops forever """
    logging.basicConfig(level=logging.INFO)
    check_gpio()
    app = Dooropener()
    app.start()
    app.honk()

    # create Flask app and run web api
    api = create_api(app)
    serve(api, host='0.0.0.0', port=9000)  # this will block until "Ctrl + C"

    app.stop()


if __name__ == '__main__':
    main_loop()
