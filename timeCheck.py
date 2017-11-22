#!/usr/bin/python3

import datetime
import time

start = datetime.time ( 7, 30, 0)
end   = datetime.time (11, 30, 0)

# Used to determine today's date 
timeNow = datetime.date.today ()

# Checktime 
checkTime = datetime.datetime.now().time()

# Adjust start and end time with date 
start   = datetime.datetime.combine (timeNow, start)
end     = datetime.datetime.combine (timeNow, end)
timeNow = datetime.datetime.combine (timeNow, checkTime)

print ("Start " + str(start)   )
print ("End   " + str(end)     )
print ("Now   " + str(timeNow) )

if start <= timeNow:
	print ("Start time passed")
	if end >= timeNow:
		print ("Waiting for end time")
	else:
		print ("End time passed as well")
else:
	print ("Waiting for start time")
