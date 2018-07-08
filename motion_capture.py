# Adapted from http://picamera.readthedocs.io/en/release-1.12/recipes2.html?highlight=motion

import io
import random
import picamera
#from PIL import Image
import numpy as np
import datetime
from skimage.measure import compare_ssim as ssim

prior_image = None

THRESHOLD = 10000

def get_time_string():
    return datetime.datetime.now().isoformat()

def detect_motion(camera):
    global prior_image
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg', use_video_port=True)
    stream.seek(0)
    if prior_image is None:
        prior_image = np.empty((camera.resolution[0], camera.resolution[1], 3), dtype=np.uint8)
        camera.capture(prior_image, 'rgb')
        return False
    else:
        current_image = np.empty((camera.resolution[0], camera.resolution[1], 3), dtype=np.uint8)
        camera.capture(current_image, 'rgb')

        # Compare current_image to prior_image to detect motion. This is
        # left as an exercise for the reader!
        result = ssim(prior_image, current_image, data_range=prior_image.max() - prior_image.min()) > THRESHOLD
        
        # Once motion detection is done, make the prior image the current
        prior_image = current_image
        return result

with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    stream = picamera.PiCameraCircularIO(camera, seconds=10)
    camera.start_recording(stream, format='h264')
    try:
        while True:
            camera.wait_recording(1)
            if detect_motion(camera):
                print('Motion detected!')
                # As soon as we detect motion, split the recording to
                # record the frames "after" motion
                # camera.split_recording('after.h264')
                # Write the 10 seconds "before" motion to disk as well
                seconds_to_include = 5
                # Wait until motion is no longer detected, then split
                # recording back to the in-memory circular buffer
                while detect_motion(camera):
                    camera.wait_recording(1)
                    seconds_to_include += 1
                stream.copy_to("/home/pi/rpi-sync/videos/" + get_time_string() + ".h264", seconds=seconds_to_include)
                stream.clear()                
                print('Motion stopped!')
                camera.split_recording(stream)
    finally:
        camera.stop_recording()
