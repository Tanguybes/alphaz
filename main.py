#!/usr/bin/python3
# -*- coding: Utf-8 -*-

from Libs import io_lib, search_lib

import numpy as np
import cv2, glob, os, re, pickle, copy, traceback, random, time


from geopy.distance import geodesic
from geopy.geocoders import Nominatim

try:
    geolocator  = Nominatim(user_agent="Mobba")
    location    = geolocator.geocode("Grenoble")
    ORIGIN = None
    if location is not None:
        ORIGIN = (location.latitude, location.longitude)

    ORIGINS = {}

    location = geolocator.geocode('France')
    if location is not None:
        ORIGINS['France'] = (location.latitude, location.longitude)
except:
    pass

def mobba():
    title   = "JBL Charge 4 Enceinte Bluetooth Portable avec USB - Robuste et Étanche pour Piscine et Plage - Son Puissant - Autonomie 20 hrs, Noir"
    url     = "https://www.amazon.fr/JBL-Charge-Enceinte-Bluetooth-Autonomie/dp/B07HGHRYCY?ref_=s9_apbd_otopr_hd_bw_b4y0NoV&pf_rd_r=ZFBP8SFGYSGYKWGHNMKQ&pf_rd_p=b7fa8523-feab-54f5-a704-5a43986890e4&pf_rd_s=merchandised-search-11&pf_rd_t=BROWSE&pf_rd_i=4551203031"

    search      = search_lib.GoogleSearch()
    return_dict = search.scrap(title)

    #search.scrap_api(title)
    #print(search.words)

if __name__ == '__main__':
    print(proxies)
    pass
    
