import datetime

class LightProgram(object):
    """ Class to store light settings """

    sunrise = 0
    sunset = 0

    start_time = datetime.time(0, 0, 0)
    end_time = datetime.time(0, 0, 0)

    startDateTime = datetime.datetime.today()
    endDateTime = startDateTime
    parent_setting = None
    myLogger = None 

    def __init__(self, start_hour, start_min, end_hour, end_min, sunrise_min, sunset_min, parent_setting, logger):
        self.start_time = datetime.time(start_hour, start_min, 0)
        self.end_time = datetime.time(end_hour, end_min, 0)
        self.sunrise = sunrise_min
        self.sunset = sunset_min
        self.calculate_start_end_date_time_for_the_day()
        self.parent_setting = parent_setting
        self.myLogger = logger
        return

    def calculate_start_end_date_time_for_the_day(self):
        """ Create start and end date object for the day """

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

        # assume that we start with zero
        blue_val = self.parent_setting.blue_settings.min_limit

        # What is currennt date and time?
        timeNow = datetime.datetime.today()

        if timeNow.date().day != self.startDateTime.date().day:
            self.calculate_start_end_date_time_for_the_day()
            self.myLogger.info ("Today's date set to " + str(self.startDateTime))

        if timeNow >= self.startDateTime:
            if timeNow <= self.endDateTime:
                blue_val = self.parent_setting.blue_settings.max_limit

        return blue_val

    def get_yellow_value(self, local_time):
        """ Determine the value of blue color at this time """

        # assume that we start with zero
        yellow_val = self.parent_setting.yellow_settings.min_limit

        # What is current date and time?
        timeNow = datetime.datetime.today()

        if timeNow.date().day != self.startDateTime.date().day:
            self.calculate_start_end_date_time_for_the_day()
            self.myLogger.info ("Todays date set to " + str(self.startDateTime))

        if timeNow >= self.startDateTime:
            if timeNow <= self.endDateTime:
                yellow_val = self.parent_setting.yellow_settings.max_limit
        return yellow_val
