#!/usr/bin/python3

""" Aquarium Ligthing Controller """
import configparser
import os
import datetime
#import smbus
import time
import datetime 
import socket
import platform
import netifaces
#import spidev
from threading import Thread

HOSTNAME = ""
IPADDRESS = ""

# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 20   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

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
LCD_AVAILABLE = False

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
#bus = smbus.SMBus(1) # Rev 2 Pi uses 1

# SPI interface for PWM 
#SPI = spidev.SpiDev()
#SPI.open (0,0)
#intensity = 0
#percent = int(0xffff/100)
stop_thread = 0

def lcd_init():
    if LCD_AVAILABLE == False:
        return

    # Initialise display
    lcd_byte(0x33,LCD_CMD) # 110011 Initialise
    lcd_byte(0x32,LCD_CMD) # 110010 Initialise
    lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
    lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
    lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_byte(0x01,LCD_CMD) # 000001 Clear display
    time.sleep(E_DELAY)

# Send byte to data pins
# bits = the data
# mode = 1 for data
#        0 for command
def lcd_byte(bits, mode):

    if LCD_AVAILABLE == False:
        return

    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

    # High bits
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)

    # Low bits
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)

# Toggle enable
def lcd_toggle_enable(bits):

    if LCD_AVAILABLE == False:
        return 

    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
    time.sleep(E_DELAY)

# Send string to display
def lcd_string(message,line):

    if LCD_AVAILABLE == False:
        return 

    message = message.ljust(LCD_WIDTH," ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]),LCD_CHR)

# Run Background thread to control intensity 
def threaded_pwm (args):
    print ("Thread started")

    while 1:

        if stop_thread:
            return

        time.sleep(0.01)

# Get Hostname of the Rasperry Pi
def get_host_info():
    global HOSTNAME
    global IPADDRESS
    
    HOSTNAME = socket.getfqdn()

    PROTO = netifaces.AF_INET # Interested in IPv4 for now

    # Get list of all interfaces 
    interfaces = netifaces.interfaces()

    # Get addresses for all interfaces 
    if_addresses = [netifaces.ifaddresses(iface) for iface in interfaces]

    # find all interfaces with IPv4 addresses 
    if_inet_addresses = [addr[PROTO] for addr in if_addresses if PROTO in addr]

    # get list of all IPv4 addresses 
    if_ipv4 = [ s['addr'] for a in if_inet_addresses for s in a if 'addr' in s]

    IPADDRESS =  next ( ( x for x in if_ipv4 if x != '127.0.0.1'))

    return


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

    start_hour = 0
    start_minute = 0
    end_hour = 0
    end_minute = 0
    sunrise = 0
    sunset = 0

    start_time = datetime.time(0,0,0)
    end_time   = datetime.time(0,0,0)

    def __init__(self, start_hour, start_min, end_hour, end_min, sunrise_min, sunset_min):
        self.start_time = datetime.time (start_hour, start_min, 0)
        self.end_time   = datetime.time (end_hour, end_min, 0)
        self.sunrise = sunrise_min
        self.sunset  = sunset_min
        return

    def get_blue_value(self, local_time):
        """ Determine the value of blue color at this time """

        blue_val = BLUE.min_limit # assume that we start with zero

        # What i present date and time? 
        timeNow = datetime.datetime.today()

        # Determine start and end times for today 
        startDateTime = datetime.datetime.combine (timeNow, self.start_time)
        endDateTime = datetime.datetime.combine (timeNow, self.end_time)

        if endDateTime <= startDateTime:
            endDateTime += datetime.timedelta(1) # End time is after midnight 

        if timeNow >= startDateTime:
            if timeNow <= endDateTime:
                blue_val = BLUE.max_limit
        return blue_val

def create_default_settings_file():
    """Create a new configuration file with default settings"""
    new_config = configparser.SafeConfigParser()

    new_config[BLUE_SECTION_NAME] = {}
    new_config[BLUE_SECTION_NAME][MAX_VALUE] = "90"
    new_config[BLUE_SECTION_NAME][MIN_VALUE] = "10"

    new_config[YELLOW_SECTION_NAME] = {}
    new_config[YELLOW_SECTION_NAME][MAX_VALUE] = "100"
    new_config[YELLOW_SECTION_NAME][MIN_VALUE] = "1"

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

#
# Main Program Entry Point 
if __name__ == "__main__":
    # Initialise display
    lcd_init()
    print ("LCD Initialized")
    star = "*"

    get_host_info()

    YELLOW = ColorSetting(YELLOW_SECTION_NAME)
    BLUE = ColorSetting(BLUE_SECTION_NAME)

    read_config(YELLOW, BLUE)

    morningProgram = LightProgram(7, 15, 23, 0, 15, 0)
    eveningProgram = LightProgram(4,30,21,0,15,45)

    # Start background thread to control light intensity 
    pwmThread = Thread (target = threaded_pwm, args=(10,))
    
    now = datetime.datetime(2017,9,20,13,00,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,00,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,15,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,50,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,1,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,17,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,46,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,22,15,00)
    print("Value at " + str(now) + " is " + str(morningProgram.get_blue_value(now)))

    pwmThread.start()

    while True:
        try:
            now = datetime.datetime.now()
            time_str = now.strftime ("%X")
            date_str = now.strftime ("%x")

            star = "*" * ((now.second % 20)+1)
            rev_star = " " * (20-len(star)) + star

            # Send some test
            lcd_string(HOSTNAME + " (" + IPADDRESS + ")", LCD_LINE_1)
            lcd_string(time_str + " " + date_str, LCD_LINE_2)    
            lcd_string(star, LCD_LINE_3)
            lcd_string(rev_star, LCD_LINE_4)

            time.sleep(0.5)

        except IOError:
            print ("I/O Error at " + time_str + " on " + date_str)
            print ("retrying in 5 seconds")
            time.sleep(5)
            lcd_init()

        except KeyboardInterrupt:
            pass

        #finally:
        #    stop_thread = 1
         #   pwmThread.join()
            #SPI.close()
