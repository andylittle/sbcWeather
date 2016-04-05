# Simple demo of reading each analog input from the ADS1x15 and printing it to
# the screen.
# Author: Tony DiCola
# License: Public Domain
import time

# Import the ADS1x15 module.
import Adafruit_ADS1x15
import datetime
ti = datetime.datetime.now()

# Create an ADS1115 ADC (16-bit) instance.
adc = Adafruit_ADS1x15.ADS1115()

# Note you can change the I2C address from its default (0x48), and/or the I2C
# bus by passing in these optional parameters:
#adc = Adafruit_ADS1x15.ADS1015(address=0x49, bus=1)

# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
GAIN = 1

inONE = adc.read_adc(0, gain=GAIN)
#inTWO = adc.read_adc(1, gain=GAIN)
#inTHR = adc.read_adc(2, gain=GAIN)
#inFUR = adc.read_adc(3, gain=GAIN)

in_min = 0
in_max = 32767
out_min = 0
out_max = 360

Direction =  (inONE - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


#print inONE
print Direction
