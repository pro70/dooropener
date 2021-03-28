#!/usr/bin/python3

"""
Dooropener

This file implements a dooropener service. It listens for web actions and two relais pins,
signals it's state with status LEDs and controls WLAN relais actors.
"""
from threading import Thread
from gpiozero import Button, LED
import requests
import time
import logging


class Relais:
    """
    This class implements one relais. It listens at one GPIO pin, signals it's state using
    an GPIO pin and triggers WLAN actions. 
    """

    def __init__(self, in_pin, signal_pin, name, on_time=5, on_url=None, off_url=None, pull_up=False):
        """ Init the Relais object, using the given input pin, signal pin and name for logging. """
        self.on_time = on_time
        self.on_url = on_url
        self.off_url = off_url
        self.name = name
        self.run = True

        self.button = Button(in_pin, pull_up=pull_up)
        self.led = LED(signal_pin)

        self.led.off()

    def disable(self):
        """ Stop listening for input signals. """
        self.run = False
    
    def _handler(self):
        logging.info(f"{self.name} - wait for press")
        while self.run:
            if self.button.wait_for_press(1):
                self._button_pressed()
        logging.info(f"{self.name} - stopped")

    def _button_pressed(self):
        logging.info(f"{self.name} - pressed")
        if self.on_url:
            self._call(self.on_url)
        else:
            logging.warning(f"{self.name} - no on url")
        self.led.on()
        time.sleep(self.on_time)
        if self.off_url:
            self._call(self.off_url)
        else:
            logging.warning(f"{self.name} - no off url")
        self.led.off()
        logging.info(f"{self.name} - cooled down")

    def _call(self, url):
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            logging.info(f"{self.name} - call successful: {url}")
        else:
            logging.error(f"{self.name} - call failed: {url}")

    def enable(self):
        """ Start listening for input. """
        self.thread = Thread(target=self._handler)
        self.thread.start()


class Bell:
    """ A bell is a local connected gong. """

    def __init__(self, work_pin=16, signal_pin=26, honk_time=0.2):
        """ Init bell with the given output pin and signal LED pin. """
        self.bell_on = LED(signal_pin)
        self.bell = LED(work_pin)
        self.honk_time = honk_time

    def _honk(self):
        self._on()
        time.sleep(self.honk_time)
        self._off()

    def _on(self):
        self.bell.on()
        self.bell_on.on()

    def _off(self):
        self.bell.off()
        self.bell_on.off()

    def honk(self):
        """ Ring th bell. """
        self.thread = Thread(target=self._honk)
        self.thread.start()


class LifeCheck:
    """ The LifeChecks tests the online connection and signals the application 
    and the online state. """

    def __init__(self, run_pin=5, wlan_pin=6, online_time=60, online_url="https://google.de"):
        self.online_time = online_time
        self.online_url = online_url
        self.running = LED(run_pin)
        self.wlan_ok = LED(wlan_pin)
        self.run = True

    def _life_check(self):
        logging.info("Life check - started")
        while self.run:
            self.running.on()
            if self.online_url:
                logging.info("WLAN check ...")
                r = requests.get(self.online_url)
                if r.status_code == requests.codes.ok:
                    logging.info("WLAN OK")
                    self.wlan_ok.on()
                else:
                    logging.error("WLAN failed!")
                    self.wlan_ok.off()
            else:
                logging.warning("WLAN check skipped")
                self.wlan_ok.off()
            time.sleep(self.online_time)
            self.wlan_ok.off()
            self.running.off()
            time.sleep(.5)
        logging.info("Life check - stopped")

    def enable(self):
        """ Start life check. """
        self.thread = Thread(target=self._life_check)
        self.thread.start()

    def disable(self):
        self.run = False
        self.running.off()


class Dooropener:
    """ The dooropener consists of two relais inputs, a life check and a local bell. """

    def __init__(self):
        self.life_check = LifeCheck()
        self.relais1 = Relais(20, 13, "Relais 1", on_time=3)
        self.relais2 = Relais(21, 19, "Relais 2", on_time=60)
        self.bell = Bell()

    def start(self):
        self.life_check.enable()
        self.relais1.enable()
        self.relais2.enable()

    def honk(self):
        self.bell.honk()

    def stop(self):
        print("Stop dooropener")
        self.life_check.disable()
        self.relais1.disable()
        self.relais2.disable()


def main_loop():
    logging.basicConfig(level=logging.INFO)
    app = Dooropener()
    app.start()
    app.honk()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        app.stop()

if __name__ == '__main__':
    main_loop()
