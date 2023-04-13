from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps
import pycountry
import requests
import json
from geopy.geocoders import Nominatim
import datetime 
from datetime import date
import geonamescache
import os

def get_coords(city):
    geolocator = Nominatim(user_agent='myapplication')
    location = geolocator.geocode(city)
    if location:
        return (location.latitude, location.longitude)
    else:
        return (181, 181)

def get_weather_dict(lat, lon):
    api_key = os.environ["owm_key"]

    url = "https://api.openweathermap.org/data/2.5/onecall?lat=%s&lon=%s&appid=%s&units=metric" % (lat, lon, api_key)
    response = requests.get(url)
    data = json.loads(response.text)
    #print(type(data)) #this is ALL the weather data lol. Literally all of it #very messy json. There are online formatters if you wish to view it
    return data

def process_weather_dict(wd, city):
    new_wd = {}
    wd = wd["daily"]

    for i in range(6):
        wdtemp = wd[i]
        cur = {}
        cur["city"] = city[0].upper() + city[1:len(city)].lower() #just for formatting capitalization so toronto becomes Toronto
        cur["date"] = datetime.datetime.fromtimestamp(wdtemp["dt"])
        cur["temp"] = wdtemp["temp"]["day"]
        cur["humidity"] = wdtemp["humidity"]
        cur["wind"] = round((wdtemp["wind_speed"] * 60 * 60) / 1000) #now this is kmph
        cur["uv"] = wdtemp["uvi"]
        cur["icon_code"] = wdtemp["weather"][0]["icon"]
        new_wd[i] = cur
    return new_wd

prev_searches = []

#put in a city name string and it'll spit out the weather data for today and the 5 after it.
def get_weather_data(city): #basically this function calls the 3 above it. 
    #wd = weather dictionary, keys are the offset from today (0-5)
    coords = get_coords(city)
    if coords == (181, 181):
        return None
    else:
        if city[0].upper() + city[1:len(city)].lower() not in prev_searches:
            #print("not in")
            prev_searches.append(city[0].upper() + city[1:len(city)].lower())
        else:
            #print("in")
            pass
        #print("ps: " , prev_searches)
        if len(prev_searches) > 5:
            prev_searches.pop(0)
        wd = get_weather_dict(coords[0], coords[1])
        wd = process_weather_dict(wd, city)
        return wd
        
def get_prev_searches():
    return prev_searches

#good for debugging and viewing our data in a decent format
""" 
for key in wd: #the key is the offset from the first day so it goes from 0-5 (0 being today and 5 being 5 days from today)
    day = wd[key]
    print("day: " , day)
    for key in day:
        print(key, ": " , day[key])
    print()
"""
