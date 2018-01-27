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
