import pycron, time, datetime, os

os.system("logsPROD")

while True:
    if pycron.is_now('5,20,35,50 * * * *'):
        print('Running at %s'%datetime.datetime.now())
        os.system("logsPROD")
        time.sleep(60)
    