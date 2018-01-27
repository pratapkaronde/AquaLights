import os 
import configparser
import logging

from ColorSetting import ColorSetting
from LightProgram import LightProgram

class StoredSettings(object):
    # Constants for configuration settings
    SETTINGS_FILE_NAME = "settings.ini"
    BLUE_SECTION_NAME = "Blue"
    YELLOW_SECTION_NAME = "Yellow"
    MAX_VALUE_NAME = "Max"
    MIN_VALUE_NAME = "Min"
    START_TIME_NAME = "Start"
    STOP_TIME_NAME = "Stop"
    SUNRISE_DURATION_NAME = "Sunrise"
    SUNSET_DURATION_NAME = "Sunset"

    yellow_settings = ColorSetting(YELLOW_SECTION_NAME)
    blue_settings = ColorSetting(BLUE_SECTION_NAME)
    programList = []
    myLogger = None 

    def __init__ (self, logger):
        self.myLogger = logger

    def create_default_settings_file(self, filename):
        """Create a new configuration file with default settings"""
        new_config = configparser.SafeConfigParser()

        new_config[self.BLUE_SECTION_NAME] = {}
        new_config[self.BLUE_SECTION_NAME][self.MAX_VALUE_NAME] = "50"
        new_config[self.BLUE_SECTION_NAME][self.MIN_VALUE_NAME] = "20"

        new_config[self.YELLOW_SECTION_NAME] = {}
        new_config[self.YELLOW_SECTION_NAME][self.MAX_VALUE_NAME] = "70"
        new_config[self.YELLOW_SECTION_NAME][self.MIN_VALUE_NAME] = "0"

        new_config["Program_1"] = {}
        new_config["Program_1"][self.START_TIME_NAME] = "7:30"
        new_config["Program_1"][self.STOP_TIME_NAME] = "9:00"
        new_config["Program_1"][self.SUNRISE_DURATION_NAME] = "15"
        new_config["Program_1"][self.SUNSET_DURATION_NAME] = "0"

        new_config["Program_2"] = {}
        new_config["Program_2"][self.START_TIME_NAME] = "16:30"
        new_config["Program_2"][self.STOP_TIME_NAME] = "21:30"
        new_config["Program_2"][self.SUNRISE_DURATION_NAME] = "0"
        new_config["Program_2"][self.SUNSET_DURATION_NAME] = "30"

        with open(filename, "w") as configfile:
            new_config.write(configfile)

        self.myLogger.info ("Default Configuration File created at " + filename)

        return filename

    def get_setting_file_name(self):
        """ Determine location of configuration file"""

        dirname, filename = os.path.split(os.path.abspath(__file__))

        filename = dirname + "/" + self.SETTINGS_FILE_NAME

        # Make sure the file exists 
        if os.path.isfile(filename) != True:
            self.myLogger.warn ("Settings file name not found. Creating new one with default settings at " + filename)
            self.create_default_settings_file ( filename )

        return filename

    # Read Configuration File from SETTINGS.INI
    def read_config(self):
        """ Read Configuration """
        config = configparser.SafeConfigParser()

        config_file_name = self.get_setting_file_name()

        self.myLogger.info ("Reading Configuration File " + config_file_name)
        config.read(config_file_name)

        self.programList = []

        # Hard coded programs for now
        #morningProgram = LightProgram(7, 30, 9, 30, 15, 0, self)
        #self.programList.append (morningProgram)

        #eveningProgram = LightProgram(16, 30, 21, 45, 15, 45, self)
        #self.programList.append (eveningProgram)

        for section in config.sections():
            
            if section == self.YELLOW_SECTION_NAME:
                # processing yellow settings
                if config[section][self.MAX_VALUE_NAME]:
                    self.yellow_settings.set_max_limit(
                        int(config[section][self.MAX_VALUE_NAME]))

                if config[section][self.MIN_VALUE_NAME]:
                    self.yellow_settings.set_min_limit(
                        int(config[section][self.MIN_VALUE_NAME]))

            elif section == self.BLUE_SECTION_NAME:
                # processing blue settings
                if config[section][self.MAX_VALUE_NAME]:
                    self.blue_settings.set_max_limit(
                        int(config[section][self.MAX_VALUE_NAME]))

                if config[section][self.MIN_VALUE_NAME]:
                    self.blue_settings.set_min_limit(
                        int(config[section][self.MIN_VALUE_NAME]))

            elif section.lower().startswith ("program_"):
                # Found a Program section, get program details 
                try:
                    start_time = config[section][self.START_TIME_NAME]
                    stop_time = config[section][self.STOP_TIME_NAME]
                    sunrise_duration = int(config[section][self.SUNRISE_DURATION_NAME])
                    sunset_duration = (config[section][self.SUNSET_DURATION_NAME])

                    time_numbers = start_time.split(":")
                    start_hour = int(time_numbers[0])
                    start_min = int (time_numbers[1])

                    time_numbers = stop_time.split(":")
                    stop_hour = int (time_numbers[0])
                    stop_min = int (time_numbers[1])
                    
                    newProgram = LightProgram ( start_hour, start_min, stop_hour, stop_min, sunrise_duration, sunset_duration, self, self.myLogger)
                    self.programList.append(newProgram)

                except: 
                    self.myLogger.error  ("Error Processing Section " + section)

                
            else:
                # processing programs
                for setting in config[section]:
                    self.myLogger.debug (setting + " = " + config[section][setting])
