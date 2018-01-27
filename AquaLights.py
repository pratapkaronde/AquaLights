#!/usr/bin/python3.5
""" Aquarium Ligthing Controller """

import os
import datetime
import time
import socket
import platform

import logging
from logging.handlers import RotatingFileHandler
from threading import Thread

from LCDManager import LCDManager
from StoredSettings import StoredSettings

import netifaces
#import spidev

HOSTNAME = ""
IPADDRESS = ""

BLUE_VALUE = 0
YELLOW_VALUE = 0

# SPI interface for PWM
#SPI = spidev.SpiDev()
#SPI.open (0,0)
#intensity = 0
#percent = int(0xffff/100)
stop_thread = 0


filePath, fileName  = os.path.split(os.path.abspath(__file__))
logFileName = filePath + "/" + "AquaLights.log"

myLogger = logging.getLogger ("AqauLogger")
formatter = logging.Formatter ("%(asctime)s - %(name)-12s - %(levelname)-8s -%(message)s")
handler = RotatingFileHandler (logFileName, mode='a',maxBytes=2*1024*1024,backupCount=2)
handler.setFormatter (formatter)
myLogger.addHandler (handler)
streamHandler = logging.StreamHandler ()
myLogger.addHandler(streamHandler)
myLogger.setLevel(logging.DEBUG)

def get_host_info():
    # Get Hostname of the Rasperry Pi

    global HOSTNAME
    global IPADDRESS

    HOSTNAME = socket.getfqdn()

    PROTO = netifaces.AF_INET  # Interested in IPv4 for now

    # Get list of all interfaces
    interfaces = netifaces.interfaces()

    # Get addresses for all interfaces
    if_addresses = [netifaces.ifaddresses(iface) for iface in interfaces]

    # find all interfaces with IPv4 addresses
    if_inet_addresses = [addr[PROTO] for addr in if_addresses if PROTO in addr]

    # get list of all IPv4 addresses
    if_ipv4 = [s['addr'] for a in if_inet_addresses for s in a if 'addr' in s]

    IPADDRESS = next((x for x in if_ipv4 if x != '127.0.0.1'))

    return


def IsRaspberryPi():
    import sys
    if sys.platform == "linux":
        if os.uname()[4].startswith("arm"):
            return True
        else:
            return False
    else:
        return False


def select_button_handler(channel):
    global stop_thread

    myLogger.debug ("Select button pressed. Exiting");
    myLogger.debug (channel)
    stop_thread = 1

def threaded_pwm(settings):
    """ Thread to control LCD intensity """
    myLogger.info ("PWM Thread started")

    global BLUE_VALUE
    global YELLOW_VALUE

    old_blue_val = 0
    old_yellow_val = 0

    if IsRaspberryPi():
        """ Determine if we are running on Raspberry Pi or not """
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)

        # Select button 
        GPIO.setup(31, GPIO.IN) 

        GPIO.add_event_detect (31, GPIO.RISING, callback=select_button_handler, bouncetime=300)

        channel_b = GPIO.PWM(11, 500)
        channel_y = GPIO.PWM(13, 500)

        # Start with 100% to shut down MOSFETs
        channel_b.start(100)
        channel_y.start(100)
        myLogger.info ("GPIO Ready")

    while stop_thread == 0:

        nowTime = datetime.datetime.now()

        blue_val = 0
        yellow_val = 0

        for program in settings.programList:
            b = program.get_blue_value(nowTime)
            if blue_val < b:
                blue_val = b

            y = program.get_yellow_value(nowTime)
            if yellow_val < y:
                yellow_val = y

        if old_blue_val != blue_val:
            myLogger.info ("Blue value changed from " + str(old_blue_val) +
                  " to " + str(blue_val) + " at " + str(nowTime))
            old_blue_val = blue_val
            BLUE_VALUE = blue_val
            if IsRaspberryPi():
                channel_b.ChangeDutyCycle(100 - BLUE_VALUE)

        if old_yellow_val != yellow_val:
            myLogger.info("Yellow value changed from " + str(old_yellow_val) +
                  " to " + str(yellow_val) + " at " + str(nowTime))
            old_yellow_val = yellow_val
            YELLOW_VALUE = yellow_val
            if IsRaspberryPi():
                channel_y.ChangeDutyCycle(100 - YELLOW_VALUE)

        if stop_thread:
            myLogger.debug ("Stopping PWM Thread")
            channel_b.ChangeDutyCycle(100)
            channel_y.ChangeDutyCycle(100)
            GPIO.cleanup()
            return

        time.sleep(1)


def threaded_lcd_update():
    """ Thread to paint LCD """
    myLogger.info ("LCD Thread started")

    # Initialise display
    lcdManager = LCDManager(IsRaspberryPi())

    lcdManager.lcd_init()
    star = "*"

    get_host_info()

    count = 0

    while stop_thread == 0:
        try:
            now = datetime.datetime.now()
            time_str = now.strftime("%X")
            date_str = now.strftime("%x")

            star = "*" * ((now.second % 20) + 1)
            rev_star = " " * (20 - len(star)) + star

            color_str = "B:" + str(BLUE_VALUE) + ", Y: " + str(YELLOW_VALUE)
            color_str = color_str + " " * (20 - len(color_str))

            # Send some test
            lcdManager.lcd_string(
                HOSTNAME + " (" + IPADDRESS + ")", lcdManager.LCD_LINE_1)
            lcdManager.lcd_string(
                time_str + " " + date_str, lcdManager.LCD_LINE_2)
            lcdManager.lcd_string(star, lcdManager.LCD_LINE_3)
            lcdManager.lcd_string(color_str, lcdManager.LCD_LINE_4)

            time.sleep(1)
            count = count + 1
            if count == 100:
                myLogger.debug (time_str + " " + date_str + " " + str(stop_thread))
                count = 0
                myLogger.debug (color_str)

        except IOError:
            myLogger.error ("I/O Error at " + time_str + " on " + date_str)
            myLogger.info  ("retrying in 5 seconds")
            time.sleep(5)
            lcdManager.lcd_init()

        # Exit thread on thread stop signal
        if stop_thread:
            myLogger.debug("Stopping LCD Update Thread")
            return


#
# Main Program Entry Point
if __name__ == "__main__":

    myLogger.info ("Program Started")
    settings = StoredSettings(myLogger)
    settings.read_config()

    # Start background thread to control light intensity
    pwmThread = Thread(target=threaded_pwm, args=(settings,))
    pwmThread.start()

    lcdThread = Thread(target=threaded_lcd_update, args=())
    lcdThread.start()

    while stop_thread == 0:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            myLogger.info ("Stopping threads")
            stop_thread = 1
            lcdThread.join()
            pwmThread.join()
            myLogger.info ("Exiting ... ")
