#!/usr/bin/python3

import datetime

start = datetime.time ( 7, 30, 0)
end   = datetime.time (11, 30, 0)

timeNow = datetime.date.today ()

# Adjust start and end time with date 
start   = datetime.datetime.combine (timeNow, start)
end     = datetime.datetime.combine (timeNow, end)
timeNow = datetime.datetime.combine (timeNow, datetime.time(7,31,0))

print ("Start " + str(start)   )
print ("End   " + str(end)     )
print ("Now   " + str(timeNow) )
