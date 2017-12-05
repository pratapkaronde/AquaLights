#!/usr/bin/python3.5
""" Aquarium Ligthing Controller """
import configparser
import os
import datetime
import time
import socket
import platform
from threading import Thread

import netifaces
#import spidev


HOSTNAME = ""
IPADDRESS = ""


# Constants for configuration settings
SETTINGS_FILE_NAME = "settings.ini"
BLUE_SECTION_NAME = "Blue"
YELLOW_SECTION_NAME = "Yellow"
MAX_VALUE = "Max"
MIN_VALUE = "Min"
START_TIME = "Start"
STOP_TIME = "Stop"
SUNRISE_DURATION = "Sunrise"
SUNSET_DURATION = "Sunset"

BLUE_VALUE = 0
YELLOW_VALUE = 0


# SPI interface for PWM
#SPI = spidev.SpiDev()
#SPI.open (0,0)
#intensity = 0
#percent = int(0xffff/100)
stop_thread = 0


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


class LCDManager(object):

    # Define some device parameters
    I2C_ADDR = 0x27  # I2C device address
    LCD_WIDTH = 20   # Maximum characters per line

    # Define some device constants
    LCD_CHR = 1  # Mode - Sending data
    LCD_CMD = 0  # Mode - Sending command

    LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
    LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
    LCD_LINE_3 = 0x94  # LCD RAM address for the 3rd line
    LCD_LINE_4 = 0xD4  # LCD RAM address for the 4th line

    LCD_BACKLIGHT = 0x08  # On
    # LCD_BACKLIGHT = 0x00  # Off

    ENABLE = 0b00000100  # Enable bit

    # Timing constants
    E_PULSE = 0.0005
    E_DELAY = 0.0005

    lcd_available = True
    bus = 0

    def __init__(self, lcd_available):
        self.lcd_available = lcd_available
        if self.lcd_available:
            import smbus
            # Open I2C interface
            # self.bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
            self.bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
        self.lcd_init()
        return

    # Toggle enable
    def lcd_toggle_enable(self, bits):

        if self.lcd_available == False:
            return

        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR, (bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)

    # Send byte to data pins
    # bits = the data
    # mode = 1 for data
    #        0 for command
    def lcd_byte(self, bits, mode):

        if self.lcd_available == False:
            return

        bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | self.LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_init(self):

        if self.lcd_available == False:
            return

        # Initialise display
        self.lcd_byte(0x33, self.LCD_CMD)  # 110011 Initialise
        self.lcd_byte(0x32, self.LCD_CMD)  # 110010 Initialise
        self.lcd_byte(0x06, self.LCD_CMD)  # 000110 Cursor move direction
        # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x0C, self.LCD_CMD)
        # 101000 Data length, number of lines, font size
        self.lcd_byte(0x28, self.LCD_CMD)
        self.lcd_byte(0x01, self.LCD_CMD)  # 000001 Clear display
        time.sleep(self.E_DELAY)

        print("LCD Initialized")

    # Send string to display
    def lcd_string(self, message, line):

        if self.lcd_available == False:
            return

        message = message.ljust(self.LCD_WIDTH, " ")

        self.lcd_byte(line, self.LCD_CMD)

        for i in range(self.LCD_WIDTH):
            self.lcd_byte(ord(message[i]), self.LCD_CHR)


class ColorSetting(object):
    """ Class to hold the color setting """

    color_name = ""
    max_limit = 100
    min_limit = 0

    def __init__(self, color_name):
        self.color_name = color_name
        self.max_limit = 100
        self.min_limit = 0
        return

    def set_color(self, color_name):
        """ Set color name """
        self.color_name = color_name

    def set_max_limit(self, max_value):
        """ Set max limit for color """
        self.max_limit = max_value

        if self.max_limit < 0:
            self.max_limit = 0
        elif self.max_limit > 100:
            self.max_limit = 100

    def set_min_limit(self, min_value):
        """ set min limit for color """
        self.min_limit = min_value

        if self.min_limit < 0:
            self.min_limit = 0
        elif self.min_limit > 100:
            self.min_limit = 100


class LightProgram(object):
    """ Class to store light settings """

    sunrise = 0
    sunset = 0

    start_time = datetime.time(0, 0, 0)
    end_time = datetime.time(0, 0, 0)

    startDateTime = datetime.datetime.now()
    endDateTime = startDateTime

    def __init__(self, start_hour, start_min, end_hour, end_min, sunrise_min, sunset_min):
        self.start_time = datetime.time(start_hour, start_min, 0)
        self.end_time = datetime.time(end_hour, end_min, 0)
        self.sunrise = sunrise_min
        self.sunset = sunset_min
        self.calculate_start_end_date_time_for_the_day()
        return

    def calculate_start_end_date_time_for_the_day(self):
        # What is currennt date and time?
        timeNow = datetime.datetime.today()

        # Determine start and end times for today
        self.startDateTime = datetime.datetime.combine(
            timeNow, self.start_time)
        self.endDateTime = datetime.datetime.combine(timeNow, self.end_time)

        if self.endDateTime <= self.startDateTime:
            # End time is after midnight
            self.endDateTime += datetime.timedelta(1)

    def get_blue_value(self, local_time):
        """ Determine the value of blue color at this time """

        blue_val = BLUE.min_limit  # assume that we start with zero

        # What is currennt date and time?
        timeNow = datetime.datetime.today()

        if timeNow >= self.startDateTime:
            if timeNow <= self.endDateTime:
                blue_val = BLUE.max_limit
        return blue_val

    def get_yellow_value(self, local_time):
        """ Determine the value of blue color at this time """

        yellow_val = YELLOW.min_limit  # assume that we start with zero

        # What is current date and time?
        timeNow = datetime.datetime.today()

        if timeNow >= self.startDateTime:
            if timeNow <= self.endDateTime:
                yellow_val = YELLOW.max_limit
        return yellow_val


def create_default_settings_file():
    """Create a new configuration file with default settings"""
    new_config = configparser.SafeConfigParser()

    new_config[BLUE_SECTION_NAME] = {}
    new_config[BLUE_SECTION_NAME][MAX_VALUE] = "100"
    new_config[BLUE_SECTION_NAME][MIN_VALUE] = "20"

    new_config[YELLOW_SECTION_NAME] = {}
    new_config[YELLOW_SECTION_NAME][MAX_VALUE] = "70"
    new_config[YELLOW_SECTION_NAME][MIN_VALUE] = "0"

    new_config["Program_1"] = {}
    new_config["Program_1"][START_TIME] = "06:00"
    new_config["Program_1"][STOP_TIME] = "09:00"
    new_config["Program_1"][SUNRISE_DURATION] = "15"
    new_config["Program_1"][SUNSET_DURATION] = "0"

    new_config["Program_2"] = {}
    new_config["Program_2"][START_TIME] = "16:00"
    new_config["Program_2"][STOP_TIME] = "21:30"
    new_config["Program_2"][SUNRISE_DURATION] = "0"
    new_config["Program_2"][SUNSET_DURATION] = "30"

    with open(SETTINGS_FILE_NAME, "w") as configfile:
        new_config.write(configfile)

    return SETTINGS_FILE_NAME


def get_setting_file_name():
    """ Determine location of configuration file"""

    if os.path.isfile(SETTINGS_FILE_NAME):
        return SETTINGS_FILE_NAME
    elif os.path.isfile("..\\settings.ini"):
        return "..\\settings.ini"
    else:
        """File does not exist in known paths, create a new file with
            default values in current directory"""
        return create_default_settings_file()

# Read Configuration File from SETTINGS.INI


def read_config(yellow, blue):
    """ Read Configuration """
    config = configparser.SafeConfigParser()

    config_file_name = get_setting_file_name()

    print(config_file_name)
    config.read(config_file_name)

    for section in config.sections():
        print(section)

        if section == YELLOW_SECTION_NAME:
            # processing yellow settings
            if config[section][MAX_VALUE]:
                yellow.set_max_limit(int(config[section][MAX_VALUE]))

            if config[section][MIN_VALUE]:
                yellow.set_min_limit(int(config[section][MIN_VALUE]))

        elif section == BLUE_SECTION_NAME:
            # processing blue settings
            if config[section][MAX_VALUE]:
                blue.set_max_limit(int(config[section][MAX_VALUE]))

            if config[section][MIN_VALUE]:
                blue.set_min_limit(int(config[section][MIN_VALUE]))

        else:
            # processing programs
            for setting in config[section]:
                print(setting + " = " + config[section][setting])

        print("")


# Run Background thread to control intensity
def threaded_pwm(programList):
    print("PWM Thread started")

    old_blue_val = 0
    old_yellow_val = 0

    global BLUE_VALUE
    global YELLOW_VALUE

    if IsRaspberryPi():

        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)

        channel_b = GPIO.PWM(11, 500)
        channel_y = GPIO.PWM(13, 500)

        # Start with 100% to shut down MOSFETs
        channel_b.start(100)
        channel_y.start(100)
        

        print("GPIO Ready")

    while stop_thread == 0:

        nowTime = datetime.datetime.now()

        blue_val = 0
        yellow_val = 0

        for program in programList:
            b = program.get_blue_value(nowTime)
            if blue_val < b:
                blue_val = b

            y = program.get_yellow_value(nowTime)
            if yellow_val < y:
                yellow_val = y

        if old_blue_val != blue_val:
            print("Blue value changed from " + str(old_blue_val) +
                  " to " + str(blue_val) + " at " + str(nowTime))
            old_blue_val = blue_val
            BLUE_VALUE = blue_val
            if IsRaspberryPi():
                channel_b.ChangeDutyCycle(100 - BLUE_VALUE)

        if old_yellow_val != yellow_val:
            print("Yellow value changed from " + str(old_yellow_val) +
                  " to " + str(yellow_val) + " at " + str(nowTime))
            old_yellow_val = yellow_val
            YELLOW_VALUE = yellow_val
            if IsRaspberryPi():
                channel_y.ChangeDutyCycle(100 - YELLOW_VALUE)

        if stop_thread:
            channel_b.ChangeDutyCycle(100)
            channel_y.ChangeDutyCycle(100)
            GPIO.cleanup()
            return

        time.sleep(1)

# Background thread for LCD Updates


def threaded_lcd_update():
    print("LCD Thread started")

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

            time.sleep(0.5)
            count = count + 1
            if count == 10:
                print(time_str + " " + date_str + " " + str(stop_thread))
                count = 0
                print(color_str)

        except IOError:
            print("I/O Error at " + time_str + " on " + date_str)
            print("retrying in 5 seconds")
            time.sleep(5)
            lcdManager.lcd_init()

        # Exit thread on thread stop signal
        if stop_thread:
            return


#
# Main Program Entry Point
if __name__ == "__main__":

    YELLOW = ColorSetting(YELLOW_SECTION_NAME)
    BLUE = ColorSetting(BLUE_SECTION_NAME)

    read_config(YELLOW, BLUE)

    morningProgram = LightProgram(7, 30, 9, 30, 15, 0)
    eveningProgram = LightProgram(16, 30, 17, 15, 15, 45)

    programList = [morningProgram, eveningProgram]

    # Start background thread to control light intensity
    pwmThread = Thread(target=threaded_pwm, args=(programList,))
    pwmThread.start()

    lcdThread = Thread(target=threaded_lcd_update, args=())
    lcdThread.start()

    while stop_thread == 0:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            print("Stopping threads")
            stop_thread = 1
            lcdThread.join()
            pwmThread.join()
