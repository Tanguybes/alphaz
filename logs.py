# -*- coding: utf-8 -*-
import glob

files = glob.glob('WSsrvWebService/*')

for file in files:
    if not '.log' in file: continue
    
    with open(file,'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'GS38' in line:
                print(line)