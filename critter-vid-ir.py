"""
critter-vid-ir.py by Aaron Dunigan AtLee
May 2019

Similar to critter-cam-ir, but this one records video
when it detects a critter in view.
"""

# Imports
from PIL import Image
from picamera import PiCamera
from shutil import copy2 as filecopy
from os import rename, path, mkdir
from time import sleep, time
from numpy import asarray, int_, sign, std, reshape
from numpy import sum as npsum  

# Global constants

DEBUGGING = True # For debugging: print processing time for each image.
THRESHOLD = 50 # Cut-off for determining 'empty' pixels.
CRITTER_SIZE = 2000 # Number of different pixels needed to save image.
# THRESHOLD = 50 and CRITTER_SIZE = 2000 seems to remove flickering but catch actual changes.
TEMPFILE1, TEMPFILE2 = 'image1.jpg', 'image2.jpg' # Filenames for image files.
VIDEO_TIME = 10 # Time in seconds to record video.

DELAY = 0 # Time in seconds between photos.  Doesn't include processing time.  Can be 0.

def get_pic(filename):
    """
    Open image file and convert to numpy array.
    Array is 3D containing [r,g,b] at each [x,y] coordinate.
    """
    return int_(asarray(Image.open(filename,'r')))

def count_pixels(rgb_diff):
    """
    Count non-empty (non-'zero') pixels in rgb_diff array.
    rgb_diff is the array of rgb difference triples.  
    """
    # To filter out differences due to changing light conditions,
    # we find the std deviation of the rgb_diff for each color dimension.
    # Pixels only count as "changed" (non-zero difference) if they 
    # exceed this std deviation by the global THRESHOLD value.

    # Reduce 3D array to 2D n x 3 where each row is [R,G,B]
    # (i.e. reduce to list of pixels insted of 2D matrix of pixels) 
    flat_diffs = reshape(rgb_diff, (-1,3))
    # Then find std deviations. Using 'axis=0' returns array of 3 values,
    # one for each color dimension.  We make these ints to reduce the calculation
    # in the next step. 
    std_devs = int_(std(flat_diffs, axis=0))
    # Now subtract each rgb minus its std dev. 
    # (Numpy subraction will subtract std_devs from each RGB triple).
    # .clip(min=0) converts negatives to 0
    flat_diffs = (flat_diffs - std_devs).clip(min=0)

    # Summing flat_diffs along 'axis 1' (i.e., in its second dimension)
    # sums the 3 rgb differences and creates a 1D array of
    # single values:
    diffs = npsum(flat_diffs,axis=1)
    
    # We want to count how many of these values are greater than THRESHOLD.
    # diffs//THRESHOLD returns 0 if diffs<THRESHOLD and a positive integer
    # if diffs>=THRESHOLD.  Therefore sign(diffs//THRESHOLD) returns 1 if
    # diffs>=THRESHOLD and 0 otherwise.  Add these up to get our count.
    count = npsum(sign(diffs//THRESHOLD))

    if DEBUGGING:
        print(count)

    return count


def calculate_file_diffs(file1, file2):
    """ Get arrays of rgb values for two files and subtract them. """

    array1 = get_pic(file1)
    array2 = get_pic(file2)
    
    # Subtract rgb values (numpy arrays make this easy; standard arrays
    # don't allow for pairwise subtraction and iterating abs() over the
    # result like this).

    return abs(array2-array1)

def calculate_diffs(array1, array2):
    """ Get arrays of rgb values for two files and subtract them. """

    # Subtract rgb values (numpy arrays make this easy; standard arrays
    # don't allow for pairwise subtraction and iterating abs() over the
    # result like this).

    return abs(array2-array1)

def get_img_path():
    m = 1
    # expanduser expands the ~ shortcut to the user's home directory.
    while path.isdir(path.expanduser("~/critters{}".format((str(m).zfill(4))))):
        m += 1
    img_path = path.expanduser("~/critters{}/".format((str(m).zfill(4))))
    mkdir(img_path)
    return img_path 

def main():
    # Main code
    camera = PiCamera()
    n = 1 # Image number to be appended to image filename.
    img_path = get_img_path()

    try:
        # Start camera and get initial image.
        camera.start_preview()
        # Make preview transparent so we can still do other stuff.
        camera.preview.alpha = 0
        # Allow camera to adjust to light.
        sleep(2)
        camera.capture(TEMPFILE1)
        array1 = get_pic(TEMPFILE1)
        while True:
            if DEBUGGING:
                start = time() # Used for measuring processing time.

            # Get second image for comparison:
            camera.capture(TEMPFILE2)
            array2 = get_pic(TEMPFILE2)

            # If a "critter" was found, save image and increment image number.
            diff = calculate_diffs(array1, array2)
            if count_pixels(diff) > CRITTER_SIZE:
                camera.start_recording( img_path + 'critter{}.h264'.format((str(n).zfill(4))))
                camera.wait_recording(VIDEO_TIME)
                camera.stop_recording()
                n += 1 
                array2 = get_pic(TEMPFILE2)

            # Transfer image2 to image1 to prepare for the next comparison:
            rename(TEMPFILE2, TEMPFILE1)
            array1 = array2

            if DEBUGGING:
                print(time()-start) # Print processing time.

            # Pause before taking next photo:
            sleep(DELAY)
    except KeyboardInterrupt:
        # Use CTRL + C to stop photographing.
        print('Canceled.')
    finally:
        # Camera preview is full screen, so we need to shut it off
        # before exiting:
        camera.stop_preview()

if __name__ == '__main__':
    main()
