import datetime

class LightProgram(object):
    """ Class to store light settings """

    sunriseMins = 0
    sunsetMins = 0

    #sunrise_time    = datetime.time (0, 0, 0) # Sun starts rising at this time 
    start_time      = datetime.time (0, 0, 0) # Full day starts at this time 
    end_time        = datetime.time (0, 0, 0) # Full day ends at this time, we go into sunset mode 
    #sunset_time     = datetime.time (0, 0, 0) # Sun sets at this time 

    startDateTime   = datetime.datetime.today()
    endDateTime     = startDateTime
    sunriseDateTime = startDateTime
    sunsetDateTime  = startDateTime

    parent_setting  = None
    myLogger        = None 

    def __init__(self, start_hour, start_min, end_hour, end_min, sunrise_min, sunset_min, parent_setting, logger):
        self.start_time     = datetime.time(start_hour, start_min, 0)
        self.end_time       = datetime.time(end_hour, end_min, 0)
        self.sunriseMins    = sunrise_min # sunrise starts x minutes before the start time 
        self.sunsetMins     = sunset_min  # sunset ends x minutes after the end  time 
        self.parent_setting = parent_setting
        self.myLogger       = logger

        self.calculate_start_end_date_time_for_the_day()

        return

    def calculate_start_end_date_time_for_the_day(self):
        """ Create start and end date object for the day """

        # What is currennt date and time?
        timeNow = datetime.datetime.today()

        # Determine start and end times for today
        self.startDateTime = datetime.datetime.combine(timeNow, self.start_time)
        self.endDateTime   = datetime.datetime.combine(timeNow, self.end_time)

        if self.endDateTime <= self.startDateTime:
            # End time is after midnight
            self.endDateTime += datetime.timedelta(1)

        self.sunriseDateTime = self.startDateTime - datetime.timedelta(minutes=self.sunriseMins)
        self.sunsetDateTime = self.endDateTime + datetime.timedelta(minutes=self.sunsetMins)

        self.myLogger.info ("Today's date set to " + str(timeNow))
        self.myLogger.info ("Sunrise starts at " + str(self.sunriseDateTime))
        self.myLogger.info ("Day will start at " + str(self.startDateTime))
        self.myLogger.info ("Sunset will happen at " + str(self.sunsetDateTime))

    def get_current_time (self):
        # What is currennt date and time?
        timeNow = datetime.datetime.today()

        # adjust date and time values if the day has changed since last time we measured ut
        if timeNow.date().day != self.startDateTime.date().day:
            self.calculate_start_end_date_time_for_the_day()
            # self.myLogger.info ("Today's date set to " + str(self.startDateTime))
            
        return timeNow

    def get_time_percentage(self, startTime, endTime, currentTime):
        percentage = 0.0
        total_time = endTime - startTime
        diff_time = currentTime - startTime
        percentage =  diff_time/ total_time 
        return percentage

    def get_current_color_value (self, minVal, maxVal):
        # assume that we start with minimun value
        val = minVal

        timeNow = self.get_current_time()

        if timeNow < self.startDateTime and self.sunriseMins > 0:
            if timeNow >= self.sunriseDateTime:
                # in surnrise
                sunrise_percent = self.get_time_percentage (self.sunriseDateTime, self.startDateTime, timeNow)
                range = maxVal - minVal  
                val = minVal + int(range * sunrise_percent)

        elif timeNow >= self.startDateTime and timeNow <= self.endDateTime:
            # within the day, use max values 
            val = maxVal

        elif timeNow > self.endDateTime and self.sunsetMins > 0:
            if timeNow <= self.sunsetDateTime:
                # in sunset 
                sunset_percent = self.get_time_percentage (self.sunsetDateTime, self.endDateTime, timeNow)
                range = maxVal - minVal
                val = minVal +  int(range * sunset_percent)

        return val


    def get_blue_value(self, local_time):
        """ Determine the value of blue color at this time """

        blue_val = self.get_current_color_value ( self.parent_setting.blue_settings.min_limit, 
                        self.parent_setting.blue_settings.max_limit)
        # # assume that we start with minimun value
        # blue_val = self.parent_setting.blue_settings.min_limit

        # timeNow = self.get_current_time()

        # if timeNow < self.startDateTime and self.sunriseMins > 0:
        #     if timeNow >= self.sunriseDateTime:
        #         # in surnrise
        #         sunrise_percent = self.get_time_percentage (self.sunriseDateTime, self.startDateTime, timeNow)
        #         blue_range = self.parent_setting.blue_settings.max_limit - self.parent_setting.blue_settings.max_limit  
        #         blue_val = self.parent_setting.blue_settings.min_limit +  (blue_range) * sunrise_percent

        # elif timeNow >= self.startDateTime and timeNow <= self.endDateTime:
        #     # within the day, use max values 
        #     blue_val = self.parent_setting.blue_settings.max_limit

        # elif timeNow > self.endDateTime and self.sunsetMins > 0:
        #     if timeNow <= self.sunsetDateTime:
        #         # in sunset 
        #         sunset_percent = self.get_time_percentage (self.sunsetDateTime, self.endDateTime, timeNow)
        #         blue_range = self.parent_setting.blue_settings.max_limit - self.parent_setting.blue_settings.max_limit  
        #         blue_val = self.parent_setting.blue_settings.min_limit +  (blue_range) * sunset_percent

        return blue_val

    def get_yellow_value(self, local_time):
        """ Determine the value of blue color at this time """

        yellow_val = self.get_current_color_value ( self.parent_setting.yellow_settings.min_limit, 
                        self.parent_setting.yellow_settings.max_limit)
        # # assume that we start with minimum value 
        # yellow_val = self.parent_setting.yellow_settings.min_limit

        # # What is current date and time?
        # timeNow = self.get_current_time()

        # if timeNow >= self.startDateTime:
        #     if timeNow <= self.endDateTime:
        #         yellow_val = self.parent_setting.yellow_settings.max_limit

        return yellow_val
