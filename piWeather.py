#!/usr/bin/python
# This datalogger script is responsible for collecting meteorological
# information from the following sensors and  creating a named pipe that
# streams that information over to the weewx driver.
# Installed sensors:
#  SHT25 (Temperature/Humidity sensor) [i2c]
#  BMP180 (Pressure) [i2c]
#  wxunderweatherstation Wind direction (inspeed) [ADC]
#  wxunderweatherstation Wind sensor (Inspeed) [GPIO, pulse]
#  Rainwise RAINEW 111 Tipping Bucket Rain Gauge [pulse]

# Last updated: 2015-04-28
# Created by Nickolas McColl
# Updated 2106-4-4 by Andy Little

import math
import spidev
import RPi.GPIO as GPIO
import time
import datetime
from time import strftime, localtime
import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT
#import sht21
import Adafruit_ADS1x15

# Global variables
wind_start_time = time.time()
wind_pulse_cnt = 0
peak_3s_wind = []
precip_pulse_cnt = 0
lightning_cnt = 0
distance_sum = 0
adc = Adafruit_ADS1x15.ADS1115() # Create an ADS1115 ADC (16-bit) instance.
GAIN = 1
wind_dir_adc_min = 0
wind_dir_adc_max = 32767
current_time = time.time()
temp = None
rh = None
precip_pulse_start_time = 0
precip_pulse_stop_time = 0

# ------------------CONFIGURATION--------------------------
# temp humidity
temp_humi_GPIO_port = 4
temp_sensor = Adafruit_DHT.DHT22
# pressure
#pres_mode = 1  # (0 ultralow power, 1 std, 2 high res, 3 ultrahigh res)
#bmp = BMP085(0x77, pres_mode)  # BMP085 and BMP180 are identical


# Wind speed
#wind_10m_multiplier = float(4.02336) / float(8)  # km/h
wind_10m_multiplier = float(4.02336) / float(1)  # km/h
wind_10m_GPIO_port = 24

# Wind Direction
wind_dir_channel = 0
wind_dir_offset = 0  # Degrees to rotate CC to equal actual direction.


# Precipitation
precip_port = 23
precip_multi = 0.000393701  # @@ Davis is .01mm or 0.000393701 inches per tip

# ------------------END OF CONFIGURATION --------------------

# Configure the GPIO for the RPi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT)  # Rain activity (Blue)
GPIO.setup(18, GPIO.OUT)  # Status activity (green)
GPIO.setup(wind_10m_GPIO_port, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.setup(precip_port, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(precip_port, GPIO.IN)

# Function that counts pulses from 10m wind sensor
def callback_windsp_10m(channel):
    global wind_pulse_cnt
    wind_pulse_cnt += 1


# Function that counts rain
def callback_precip(channel):

    global precip_pulse_cnt
    precip_pulse_cnt = precip_pulse_cnt + 1  # each tip 1/100 inch
    #f = open('/home/weewx/bin/rain.log', 'a')
    #datetime = strftime("%Y-%m-%d %H:%M:%S ", localtime())
    #f.write(datetime + ' Precip detected 0.01 \n')
    #f.close()

    # turn off precip until error fixed. Make sure to turn it on below as well 
    #precip_pulse_cnt = 0


# monitor GPIO for pulses from wind sensor
GPIO.add_event_detect(wind_10m_GPIO_port,
                      GPIO.FALLING,
                      callback=callback_windsp_10m,
                      bouncetime=1)


# Monitor GPIO for Rain
GPIO.add_event_detect(precip_port,
                      #GPIO.FALLING,
                      GPIO.RISING,
                      callback=callback_precip,
                      bouncetime=300)


# function to get data from SHT25.
def get_sfc_temprh():
    global temp, rh
    rh, ctemp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, temp_humi_GPIO_port)
    temp = 9.0/5.0 * ctemp + 32
    return temp, rh


# Function to get data from Pressure sensor
def get_sfc_pres():
    global bmp
    if bmp:
        pres = bmp.readPressure()
        pres = (pres / float(100))  # Converts to hPa
    else:
        pres = None
    return pres


# Function to get data from Rain Gauge
def get_precip():
    global precip_pulse_cnt
    precip = precip_pulse_cnt * precip_multi
    precip_pulse_cnt = 0
#    precip = None   
    return precip


# Function to get data from Wind Speed Sensor
# Wind speed sends 8 pulses per revolution. Time is need to complete
# calculations. Normally this is one second but delays in program
# run time can change that. We use wind_end_time and wind_start_time
# to correctly get the time inverval between obs.
def get_10m_wind_speed():
    global wind_pulse_cnt
    global wind_start_time
    global peak_3s_wind
    wind_end_time = time.time()
    wind_speed = ((wind_pulse_cnt * wind_10m_multiplier) /
                  (wind_end_time - wind_start_time))
    wind_pulse_cnt = 0  # reset counter
    wind_start_time = wind_end_time  # Reset timer for winds
    peak_3s_wind.insert(0, wind_speed)
    if len(peak_3s_wind) == 4:
        peak_3s_wind.pop()
    avg_peak_wind = 0
    for peak_wind in peak_3s_wind:
        avg_peak_wind = avg_peak_wind + peak_wind
    avg_peak_wind = float(avg_peak_wind / len(peak_3s_wind))
    return wind_speed, avg_peak_wind


# Function to get data from Wind Vane Sensor
def get_10m_wind_dir():
    global wind_dir_adc_min, wind_dir_adc_max
    r1 = adc.read_adc(wind_dir_channel, gain=GAIN)
    wind_dir =  (r1 - wind_dir_adc_min) * (360 - 0) // (wind_dir_adc_max - wind_dir_adc_min) + 0


    # Apply offset
    wind_dir = wind_dir + wind_dir_offset
    if wind_dir > 360:
        wind_dir = wind_dir - 360
    return wind_dir


# Function to get RPi's temperature
def get_pi_temp():
    f = open('/sys/class/thermal/thermal_zone0/temp', 'r')
    input = f.readline()
    if input:
        s_temp = float(input) / 1000
    else:
        system_temp = None
    system_temp = 9.0/5.0 * s_temp + 32
    return system_temp


# Main Program. Sample all the sensors and created data file.
# This data file can then be picked up by ingester (WEEWX)
while True:
    GPIO.output(18, True)  # turn led status light on.
    GPIO.output(17, False)  # turn lightning status light off.
    # Get time
    start_time = time.time()
    datetime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    # Get Temperature and Humidity
    temperature_sfc, humidity_sfc = get_sfc_temprh()
    # Get Pressure
    ##pressure_sfc = get_sfc_pres()
    # Get Wind Direction
    winddir_10m = get_10m_wind_dir()
    # Get wind speed and three second peak. (WMO standard)
    windspd_10m, windspd_peak_10m = get_10m_wind_speed()
    if windspd_10m < 0.01:  # Wind speed is zero
        winddir_10m = winddir_10m # set to None to have 0 dir
    # Get Precip
    precip_sfc = get_precip()
    # Get System temperature
    system_temp = get_pi_temp()

    # Get End Times and calculate program pause to next collection
    end_time = time.time()
    proc_time = round(end_time - start_time, 4)
    if (proc_time > 1) or (math.ceil(end_time) > math.ceil(start_time)):
        sleep_time = 0  
    else:
        sleep_time = math.ceil(end_time) - end_time

#   Build data string
    
    pressure_sfc = 0
    solar_sfc = 0
    total_lightning = 0
    lightning_distance = 0	


    data = "datetime=%s \nbarometer=%s \nwindSpeed=%s \nwindDir=%s \noutTemp=%s \noutHumidity=%s \nrain=%s \ntotal_lightning=%s \nlightning_distance=%s \nUV=%s \nproc_time=%s \ninTemp=%s \nwindGust=%s \n" % (
           datetime, pressure_sfc, windspd_10m,
           winddir_10m, temperature_sfc, humidity_sfc,
           precip_sfc, total_lightning, lightning_distance,
           solar_sfc, proc_time, system_temp, windspd_peak_10m)


#   data = "%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
#           datetime, windspd_10m,
#           winddir_10m, temperature_sfc, humidity_sfc,
#           precip_sfc, proc_time, 
#           system_temp, windspd_peak_10m)
    filename = time.strftime("%Y-%m-%d")

##    print data

    #print round(temperature_sfc, 1) round to one place
    #Write data to archive
    log = open('/root/' + filename + '.csv', 'a')
    log.write(data)
    log.close()

    #Write current data
    log2 = open('/root/wxdata.csv', 'w')
    log2.write(data)
    log2.close()

    GPIO.output(18, False)  # turn led status light off
    time.sleep(sleep_time)  # Sleep until beginning of next second


