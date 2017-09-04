"""
birds.py by Aaron Dunigan AtLee
August 2017

Using a Raspberry Pi with camera module, we wanted to catch birds on camera
at our bird feeder.  We fixed the camera and took photos at a specified time
interval (1 second).  This program compares two consecutive photos
and subtracts the R,G,B values of their pixels.  If the R,G,and/or B have changed
by a significant amount (THRESHOLD), we consider the pixel to have changed.
If enough pixels (greater than BIRD_SIZE) have changed, we assume that
an object has entered the scene (i.e. a bird, although we also caught people
and cars passing by).  If an object is detected, the difference between the
two photos is written to a new file, which shows a photo of the object on a black
background.

This program is meant to be run from the command line with the following arguments:
python birds.py pic1 pic2 [threshold bird_size]
pic1 and pic2 are the files containing images to be compared.
threshold and bird_size are optional and if not given will be set to their defaults.
"""

from PIL import Image
from sys import argv

# Global constants
if len(argv)>3:
    THRESHOLD = int(argv[3]) # Cut-off for determining 'empty' pixels.
else:
    THRESHOLD = 30 # Default
if len(argv)>4:
    BIRD_SIZE = int(argv[4]) # Number of 'changed' pixels needed to detect a bird.
else:
    BIRD_SIZE = 25000 # Default

def get_pic(filename):
    """
    Convert a picture file (usually .jpg) to a 3D array of rgb colors
    ([R,G,B] at each [x,y] coordinate).
    """
    global mode
    global size
    pic = Image.open(filename,'r')
    rgb = list(pic.getdata())
    mode, size = pic.mode, pic.size
    return rgb

def subtract_pics(pic1,pic2):
    """
    pic1 and pic2 are arrays of rgb tuples.  Subtract corresponding tuples
    and return the resulting array of tuples.
    """
    # One-liner using nested list comprehension.
    # zip([a,b,c],[1,2,3]) returns [(a,1),(b,2),(c,3)]
    # so zip(pic1,pic2) returns a list of pairs containing corresponding
    # rgb tuples, i.e. [((r1,g1,b1),(r2,g2,b2)),...].
    # zip(i,j) takes each of those pairs and pairs colors,
    # i.e. [(r1,r2),(g1,g2),(b1,b2)] and then we subtract these pairs and put
    # it all back together with tuple(), so we have [[(r1-r2,g1-g2,b1-b2),...]].
    return [tuple(abs(x-y) for x, y in zip(i, j)) for i,j in zip(pic1,pic2)]

def write_new_pic(rgb,filename):
    """ Convert an rgb array to a picture and save as a file. """
    new_pic = Image.new(mode, size)
    new_pic.putdata(rgb)
    new_pic.save(filename)

def count_pixels(rgb):
    """ Count non-empty (non-zero) pixels in rgb array. """
    count = 0
    for pixel in rgb:
        if sum(pixel) > 0:
            count += 1
    return count

def has_object(rgb):
    """
    Determine whether there are enough changed pixels to decide that an
    object (bird, car, etc.) has been detected.
    rgb is the array of rgb differences between the two pics.
    """
    if count_pixels(rgb) > BIRD_SIZE:
        return True
    else:
        return False

# Main code.    
img1 = get_pic(argv[1])
img2 = get_pic(argv[2])
diff = subtract_pics(img2,img1)
new = [(img2[i] if sum(pixel)>THRESHOLD else (0,0,0)) for i,pixel in enumerate(diff)]
write_new_pic(new,'new.bmp')
diffs = count_pixels(new)
print('There are {} pixels that are different in the two files.'.format(str(diffs)))
if diffs > BIRD_SIZE:
    print('There seems to be an object in the second file.')
else:
    print('There is probably NO object in the second file.')
