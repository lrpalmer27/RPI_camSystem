"""
This file is intended to make a timelapse for another project. 
I want to make a timelapse of this: https://github.com/lrpalmer27/MAPLIGHTS

"""

import io
import os
import time
import datetime
from datetime import timedelta
from picamera import PiCamera

# ----------------------- PREAMBLE ---------------------------------
SaveFolder='TimelapsePictures'

RESOLUTION = (1280,720) #1080p (camera max)
NumPics=100 #number of pics that will be saved over period of time
PeriodOfTime=18 #number of hours to record over
TimeDelay=(60*60*PeriodOfTime)/NumPics #time delay in seconds between pictures.

# ----------------------- INIT CAMERA ------------------------------
camera=PiCamera()
camera.resolution=RESOLUTION
camera.rotation=180 #camera is mounted upside down on rpi3b mount.

# ----------------------- START PICTURE TAKING ---------------------
StartingTime=datetime.datetime.now()
CurrentTime=datetime.datetime.now()

while StartingTime < (CurrentTime + timedelta(hours=PeriodOfTime)):
    CurrentTime=(datetime.datetime.now()).replace(microsecond=0)
    CurrentTime=str(CurrentTime).replace(':',"-")
    CurrentTime=CurrentTime.replace(" ","_")
    camera.capture(rf"{SaveFolder}/{CurrentTime}.png")
    print(f'Picture taken at {CurrentTime} & saved.')
    time.sleep(TimeDelay)
