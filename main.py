import network
import machine
import gc
from machine import RTC
import ntptime
from neopixel import Neopixel
import constants
import time
from time import sleep, sleep_ms

numpix = 50
pixels = Neopixel(numpix, 0, 28, "GRB")
pixels.brightness(255)

led = machine.Pin("LED", machine.Pin.OUT)

off = (0,0,0)
on = (255,255,255)

mywifi=network.WLAN(network.STA_IF)
mywifi.active(True)
mywifi.connect('NETGEAR12','chummycoconut492')

rtc = machine.RTC()
utc_offset = -6 * 60 * 60

wakeup_hour = 6
minutes_buildup = 5

testing = False
testing1 = False



def is_dst(raw_time):
    if((raw_time[1] < 11 and raw_time[1] > 3) or
       ((raw_time[1] == 3 and raw_time[2] >= constants.dst_dates[raw_time[0]-2020][0]) or
        (raw_time[1] == 11 and raw_time[2] <= constants.dst_dates[raw_time[0]-2020][1]))):
        return True
    else:
        return False

def set_lights(color, duration):
    pixels.fill(color)
    pixels.show()
    sleep_ms(duration)

def pre_wakeup(mins):
    milliseconds_to_use = mins * 60 * 1000
    milliseconds_per_step = int(milliseconds_to_use / 256)
    power_level = 0
    while(power_level <= 255):
        set_lights((constants.gamma8[power_level],0,0),milliseconds_per_step)
        power_level += 1
    return

def post_wakeup(mins):
    milliseconds_to_use = mins * 60 * 1000
    milliseconds_per_step = int(milliseconds_to_use / 256)
    power_level = 0
    while(power_level <= 255):
        set_lights((255,constants.gamma8[power_level],constants.gamma8[power_level]),milliseconds_per_step)
        power_level += 1
    return

def flicker_lights(mins):
    duration = int(mins * 120)
    for x in range(duration):
        if(x%2 == 0):
            print("On!")
            led.on()
            set_lights(on,500)
        else:
            print("Off!")
            led.off()
            set_lights(off,500)
    set_lights(off,0)
    return

def circle_lights(mins):
    print("Circling...")
    duration = int(mins * 60 * 24)
    div = len(constants.circle_index)
    y_offset = duration%div
    x_offset = numpix%div
    t=0
    i=0
    for x in range(duration):
        t = x%div
        for p in range(numpix):
            i = ((p+div)-t)%div
            pixels.set_pixel(p,(constants.circle_index[i] if (p > (x-(duration - numpix)) and (p < x or x >= numpix)) else off))
        pixels.show()
        if(x%3>0):
            sleep_ms(1)
        sleep_ms(41)
    gc.collect()
    return

def refresh_RTC():
    utc_offset = -6 * 60 * 60
    time_set = False
    while not time_set:
        try:
            ntptime.settime()
            time_set = True
        except:
            time_set = False
    if(is_dst(time.localtime(time.time() + utc_offset))):
        utc_offset -= 60 * 60

def time_dif(now,target):
    time_target = (target[0] * 3600) + (target[1] * 60)
    time_now = (now[3] * 3600) + (now[4] * 60) + now[5]
    difference = ((time_target + 86400) - time_now) % 86400
    return difference
    

def wait_until(hour, minute):
    refresh_RTC()
    raw_time = time.localtime(time.time() + utc_offset)
    time_to_sleep = time_dif(raw_time,[hour,minute])
    sleep_hour, remainder = divmod(time_to_sleep,3600)
    sleep_minute, sleep_second = divmod(remainder,60)
    clock_time = str(((raw_time[3]-1)%12)+1)+":"+str(raw_time[4])+":"+str(raw_time[5])+" "+("AM" if raw_time[3] < 12 else "PM")
    print("It is "+clock_time+". I will now sleep for "+str(sleep_hour)+" hours, "+str(sleep_minute)+" minutes, and "+str(sleep_second)+" seconds.")
    print("I will begin to brighten the lights at "+str(hour)+":"+str(minute)+".")
    while not (raw_time[3] == hour and raw_time[4] == minute):
        if(time_to_sleep/3600 >= 1.5):
            sleep(3600)
        elif(time_to_sleep/60 >= 3):
            sleep(60)
        else:
            sleep(1)
        
        refresh_RTC()
        raw_time = time.localtime(time.time() + utc_offset)
        time_to_sleep = time_dif(raw_time,[hour,minute])
    return

flicker_lights(1/12)
circle_lights(1/12)

while(True):
    gc.collect()
    set_lights(off,0)
    wait_until(wakeup_hour-1,(60-minutes_buildup))
    pre_wakeup(minutes_buildup)
    post_wakeup(minutes_buildup)
    flicker_lights(1)
    circle_lights(1/3)
    while(True):
        flicker_lights(1/6)
        circle_lights(1/12)
        gc.collect()