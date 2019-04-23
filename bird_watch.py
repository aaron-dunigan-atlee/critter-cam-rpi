"""
bird_watch.py by Aaron Dunigan AtLee
August 2017

Using a Raspberry Pi with camera module, we wanted to catch birds on camera
at our bird feeder.  We fixed the camera in place, then ran this program
which takes photos at a regular interval (approx 1 second).
It compares two consecutive photos and subtracts the R,G,B values of their
pixels.  If the R,G,and/or B have changed
by a significant amount (THRESHOLD), we consider the pixel to have changed.
If enough pixels (greater than BIRD_SIZE) have changed, we assume that
an object has entered the scene (i.e. a bird, although we also caught people
and cars passing by).  If an object is detected, the second photo is kept;
otherwise it is discarded.

The original comparison algorithm is in birds.py.  That algorithm did the
subtraction 'by hand' and ran slowly (20 seconds to process); this version
uses the math module 'numpy' to speed things up, though this makes the math
a little more opaque.  This one processes in about 1 second.
"""

from PIL import Image
from picamera import PiCamera
from shutil import copy2 as filecopy
from os import rename, path, mkdir
from time import sleep, time
from numpy import asarray, int_, sign
from numpy import sum as npsum

# Global constants
THRESHOLD = 30 # Cut-off for determining 'empty' pixels.
BIRD_SIZE = 25000 # Number of different pixels needed to save image.
DELAY = 0 # Time in seconds between photos.  Doesn't include processing time.  Can be 0.

def get_pic(filename):
    """
    Open image file and convert to numpy array.
    Array is 3D containing [r,g,b] at each [x,y] coordinate.
    """
    return int_(asarray(Image.open(filename,'r')))

def count_pixels(rgb_diff):
    """
    Count non-empty (non-zero) pixels in rgb array.
    rgb_diff is the array of rgb difference triples.  
    """
    # Summing rgb_diff along 'axis 2' (i.e., in its third dimension)
    # sums the 3 rgb differences and creates a 2D [x,y] array of
    # single values:
    diffs = npsum(rgb_diff,axis=2)
    
    # We want to count how many of these values are greater than THRESHOLD.
    # diffs//THRESHOLD returns 0 if diffs<THRESHOLD and a positive integer
    # if diffs>=THRESHOLD.  Therefore sign(diffs//THRESHOLD) returns 1 if
    # diffs>=THRESHOLD and 0 otherwise.  Add these up to get our count.
    count = npsum(sign(diffs//THRESHOLD))
    return count

def get_img_path():
    m = 1
    while path.isdir(path.expanduser("~/critters{}".format((str(m).zfill(4))))):
        m += 1
    img_path = path.expanduser("~/critters{}/".format((str(m).zfill(4))))
    mkdir(img_path)
    return img_path 

# Main code
camera = PiCamera()
n = 1 # Image number to be appended to image filename.
# expanduser expands the ~ shortcut to the home directory.
img_path = get_img_path()

try:
    # Start camera and get initial image.
    camera.start_preview()
    # Allow camera to adjust to light.
    sleep(2)
    camera.capture('image1.jpg')
    array1 = get_pic('image1.jpg')
    while True:
        # start = time() # Used for measuring processing time.

        # Get second image for comparison:
        camera.capture('image2.jpg')
        array2 = get_pic('image2.jpg')

        # Subtract rgb values (numpy arrays make this easy; standard arrays
        # don't allow for pairwise subtraction and iterating abs() over the
        # result like this):
        diff = abs(array2-array1)

        # If a bird was found, save image and increment image number.
        if count_pixels(diff) > BIRD_SIZE:
            filecopy('image2.jpg', img_path + 'critter{}.jpg'.format((str(n).zfill(4))))
            n += 1 

        # Transfer image2 to image1 to prepare for the next comparison:
        rename('image2.jpg', 'image1.jpg')
        array1 = array2

        # print(time()-start) # Print processing time.

        # Pause before taking next photo:
        sleep(DELAY)
except KeyboardInterrupt:
    # Use CTRL + C to stop photographing.
    print('Canceled.')
finally:
    # Camera preview is full screen, so we need to shut it off
    # before exiting:
    camera.stop_preview()
