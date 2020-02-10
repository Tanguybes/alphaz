#!/usr/bin/python3
# -*- coding: Utf-8 -*-

import numpy as np
import cv2, glob, os, re, pickle, copy, traceback, random, time
from itertools import cycle

from geopy.distance import geodesic
from geopy.geocoders import Nominatim

geolocator  = Nominatim(user_agent="Mobba")
location    = geolocator.geocode("25 rue Aimé Requet Grenoble")
ORIGIN = None
if location is not None:
    ORIGIN = (location.latitude, location.longitude)

ORIGINS = {}
location = geolocator.geocode('France')
if location is not None:
    ORIGINS['France'] = (location.latitude, location.longitude)

proxies     = io_lib.get_proxies()
proxy_pool  = cycle(proxies)

if __name__ == '__main__':
    print(proxies)
    pass
    