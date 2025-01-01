#base from https://raspberrypi.stackexchange.com/questions/62523/always-on-security-camera-uploading-to-cloud-looping-video-recording-saving

import io
import os
import logging
import datetime as dt
import shutil
from subprocess import Popen, PIPE, DEVNULL
from picamera import PiCamera
from dirsync import sync

TRASHCAN='/home/logan/.local/share/Trash/files'
LOCAL_FOLDER = '/home/logan/Desktop/RollingRecordings'
REMOTE_FOLDER='/home/logan/Desktop/Recordings'
LOCAL_SIZE_LIMIT = 1024 * 1048576 * 17 # 17 GB
#LOCAL_SIZE_LIMIT = 1024 * 1048576 * 0.01 # 10mib # for troubleshooting

RESOLUTION = '1280x720' #1080p (camera max)
FRAMERATE = 10 # fps
BITRATE = 1000000 # bps
QUALITY = 15
CHUNK_LENGTH = 300 # seconds

class VideoFile:
    def __init__(self, dest=LOCAL_FOLDER):
        self._filename = os.path.join(
            dest, dt.datetime.utcnow().strftime('CAM-%Y%m%d-%H%M%S.mp4'))
        # Use a VLC sub-process to handle muxing to MP4
        self._process = Popen([
            'cvlc',
            'stream:///dev/stdin',
            '--demux', 'h264',
            '--h264-fps', str(FRAMERATE),
            '--play-and-exit',
            '--sout',
            '#standard{access=file,mux=mp4,dst=%s}' % self._filename,
            ], stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        logging.info('Recording to %s', self._filename)

    def write(self, buf):
        return self._process.stdin.write(buf)

    def close(self):
        self._process.stdin.close()
        self._process.wait()
        # If you want to add a cloud upload, I'd suggest starting it
        # in a background thread here; make sure it keeps an open handle
        # on the output file (self._filename) in case it gets deleted

    @property
    def name(self):
        return self._filename

    def remove(self):
        logging.info('Removing %s', self._filename)
        os.unlink(self._filename)
        self._filename = None

def outputs():
    while True:
        yield VideoFile()

def getFolderSize(path): 
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

def cleanupFolders():
    if getFolderSize(LOCAL_FOLDER) > LOCAL_SIZE_LIMIT: 
        files=sorted(os.listdir(LOCAL_FOLDER))
        i=0
        while getFolderSize(LOCAL_FOLDER) > LOCAL_SIZE_LIMIT:
            try: # hide in a try loop incase remote folder is not avail, or is busy.
                shutil.copyfile(os.path.join(LOCAL_FOLDER,files[i]),REMOTE_FOLDER) # copy to remote
                #print("Copy", files[i], "to remote")
            except:
                #print("did not copy..",files[i])
                #print("From:",os.path.join(LOCAL_FOLDER,files[i]))
                #print("to:", REMOTE_FOLDER)
                None
            os.remove(os.path.join(LOCAL_FOLDER,files[i]))                 # delete local copy
            i+=1
    trashcanFiles=os.listdir(TRASHCAN)
    for tf in trashcanFiles:
        os.remove(os.path.join(TRASHCAN,tf))

#start recording!
cleanupFolders()
logging.getLogger().setLevel(logging.INFO)
with PiCamera(resolution=RESOLUTION, framerate=FRAMERATE) as camera:
    camera.rotation=180
    last_output=None
    for output in camera.record_sequence(
            outputs(), format='h264',
            bitrate=BITRATE, quality=QUALITY, intra_period=5 * FRAMERATE):
        
        if last_output is not None:
            last_output.close()
        
        last_output=output
        camera.wait_recording(CHUNK_LENGTH)
        cleanupFolders()
