#!/usr/bin/python3
#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_i2c.py
#  LCD test script using I2C backpack.
#  Supports 16x2 and 20x4 screens.
#
# Author : Matt Hawkins
# Date   : 20/09/2015
#
# http://www.raspberrypi-spy.co.uk/
#
# Copyright 2015 Matt Hawkins
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#--------------------------------------
import smbus
import time
import datetime 
import socket
import platform
import netifaces
import spidev
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

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

# SPI interface for PWM 
SPI = spidev.SpiDev()
SPI.open (0,0)
intensity = 0
percent = int(0xffff/100)
stop_thread = 0

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def threaded_pwm (args):
  global intensity
  global percent
  print ("Thread started")
  data = [0x96, 0xDF, 0xFF, 0xFF] + [0 for i in range(24)]
  
  while 1:
    intensity = intensity + percent;

    if (intensity > 0xffff) or (intensity<0):
        percent = percent *-1;
        intensity = intensity + percent
        time.sleep(0.5) 

    
    data = [0x96, 0xDF, 0xFF, 0xFF] + [0 for i in range(24)]
    for i in range (4,28,2):
        lsb = intensity & 0xff
        msb = (intensity >> 8) & 0xff
        data[i] = msb;
        data[i+1] = lsb
       
        intensity = 0xffff-intensity;

        
    SPI.xfer2 (data)
    if stop_thread:
        return;

    time.sleep(0.01)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

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

def main():
  # Main program block

  # Initialise display
  lcd_init()
  print ("LCD Initialized")
  star = "*"

  get_host_info()

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
  
if __name__ == '__main__':

  thread = Thread (target = threaded_pwm, args=(10,))

  try:
    thread.start()
    main()
  except KeyboardInterrupt:
    pass
  finally:
    stop_thread = 1
    thread.join()
    lcd_byte(0x01, LCD_CMD)
    thread.join()
    SPI.close()


