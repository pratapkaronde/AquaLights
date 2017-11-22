""" Aquarium Ligthing Controller """

import configparser
import os
import datetime

# Constants for configuration settings
SETTINGS_FILE_NAME = "settings.ini"
BLUE_SECTION = "Blue"
YELLOW_SECTION = "Yellow"
MAX_VALUE = "Max"
MIN_VALUE = "Min"
START_TIME = "Start"
STOP_TIME = "Stop"
SUNRISE_DURATION = "Sunrise"
SUNSET_DURATION = "Sunset"

class ColorSetting(object):
    """ Class to hold the color setting """

    color_name = ""
    max_limit = 100
    min_limit = 0

    def __init__(self):
        self.color_name = ""
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

    def __init__(self):
        return

    def set_start_hour(self, hour):
        """ Program starts at this hour """
        self.start_hour = hour

        if self.start_hour < 0:
            self.start_hour = 0
        elif self.start_hour > 23:
            self.start_hour = 23


    def set_start_minute(self, minute):
        """ Program starts at this minute """
        self.start_minute = minute

        if self.start_minute < 0:
            self.start_minute = 0
        elif self.start_minute > 59:
            self.start_minute = 59

    def set_end_hour(self, hour):
        """ Program ends at this hour  """

        self.end_hour = hour

        if self.end_hour < 0:
            self.end_hour = 0
        elif self.end_hour > 23:
            self.end_hour = 23

    def set_end_minute(self, minute):
        """ Program ends at this minute """
        self.end_minute = minute

        if self.end_minute < 0:
            self.end_minute = 0
        elif self.end_minute > 59:
            self.end_minute = 59

    def get_blue_value(self, local_time):
        """ Determine the value of blue color at this time """

        blue_val = BLUE.min_limit # assume that we start with zero

        #local_time = datetime.datetime.now()

        if self.start_hour <= self.end_hour:
            #normal day time program
            if local_time.hour >= self.start_hour and local_time.hour <= self.end_hour:
                if local_time.hour == self.start_hour:
                    #in first hour, check start minute
                    if local_time.minute >= self.start_minute:
                        blue_val = BLUE.max_limit
                elif local_time.hour == self.end_hour:
                    #in last hour, check end minute
                    if local_time.minute <= self.end_minute:
                        blue_val = BLUE.max_limit
                else:
                    #for all other hours, lights stay on between start hour and end hour
                    blue_val = BLUE.max_limit
        else:
            #night time program
            if self.start_hour == local_time.hour:
                # first hour, check start minute
                if self.start_minute >= local_time.minute:
                    blue_val = BLUE.max_limit
            elif self.start_hour < local_time.hour:
                # program started previous hour, no need to check minutes
                blue_val = BLUE.max_limit
            elif self.start_hour > local_time.hour:
                #past midnight
                if local_time.hour == self.end_hour:
                    #last hour, check minutes
                    if local_time.minutes <= self.end_minute:
                        blue_val = BLUE.max_limit
                elif local_time.hour < self.end_hour:
                    # not the last hour and not the first hour
                    blue_val = BLUE.max_limit
            else:
                assert "What happned here " + self + " @ " + local_time

        #if self.sunrise > 0:
        #    start_time = datetime.datetime(0, 0, 0, self.start_hour, self.start_minute)
        #    delta = local_time - start_time
        #    print(delta)

        return blue_val

def create_default_settings_file():
    """Create a new configuration file with default settings"""
    new_config = configparser.SafeConfigParser()

    new_config[BLUE_SECTION] = {}
    new_config[BLUE_SECTION][MAX_VALUE] = "90"
    new_config[BLUE_SECTION][MIN_VALUE] = "10"

    new_config[YELLOW_SECTION] = {}
    new_config[YELLOW_SECTION][MAX_VALUE] = "100"
    new_config[YELLOW_SECTION][MIN_VALUE] = "1"

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

def read_config(yellow, blue):
    """ Read Configuration """
    config = configparser.SafeConfigParser()

    config_file_name = get_setting_file_name()

    print(config_file_name)
    config.read(config_file_name)

    for section in config.sections():
        print(section)

        if section == YELLOW_SECTION:
            # processing yellow settings
            if config[section][MAX_VALUE]:
                yellow.set_max_limit(int(config[section][MAX_VALUE]))

            if config[section][MIN_VALUE]:
                yellow.set_min_limit(int(config[section][MIN_VALUE]))

        elif section == BLUE_SECTION:
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

if __name__ == "__main__":
    YELLOW = ColorSetting()
    BLUE = ColorSetting()

    YELLOW.set_color(YELLOW_SECTION)
    BLUE.set_color(BLUE_SECTION)

    read_config(YELLOW, BLUE)

    prog1 = LightProgram()
    prog1.sunrise = 15
    prog1.sunset = 20
    prog1.set_start_hour(16)
    prog1.set_start_minute(15)
    prog1.set_end_hour(17)
    prog1.set_end_minute(45)

    
    now = datetime.datetime(2017,9,20,13,00,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,00,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,15,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,16,50,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,1,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,17,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,17,46,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))

    now = datetime.datetime(2017,9,20,18,15,00)
    print("Value at " + str(now) + " is " + str(prog1.get_blue_value(now)))
