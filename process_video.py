import re
import subprocess as sp
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

# Timestamp so you can see how long it took
start_time = "Script started at " + time.strftime("%H:%M:%S")
print(start_time)

# input file (first argument)
filename = str(sys.argv[1])
outfilename = re.sub(r"\W+", "", filename) + ".png"

## Get the metadata for the file

FFPROBE_BIN = r"C:\Users\Nick\Documents\Programming\ffmpeg\bin\ffprobe.exe"
command = [
    FFPROBE_BIN,
    "-loglevel",
    "quiet",
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=width,height",
    "-show_format",
    "-of",
    "default=nk=1:nw=1",
    "1917.mkv",
]

output = sp.check_output(command).decode("utf-8")
metadata = output.split("\n")

# orig_width, orig_height = metadata[0], metadata[1]
runtime = int(float(metadata[8]))
total_frames = runtime * 24
every_n_frames = total_frames // 4096


print("Filename:", filename)
print("Duration (s): ", runtime)
print(f"Taking every {every_n_frames} frames")

###
### This section: credit to http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/

# Open the video file. In Windows you might need to use FFMPEG_BIN="ffmpeg.exe"; Linux/OSX should be OK.
FFMPEG_BIN = r"C:\Users\Nick\Documents\Programming\ffmpeg\bin\ffmpeg.exe"
command = [
    FFMPEG_BIN,
    "-threads",
    "16",
    "-i",
    filename,
    "-f",
    "image2pipe",
    "-pix_fmt",
    "rgb24",
    "-s",
    "320x200",  # downscale before processing for faster runtime
    "-vcodec",
    "rawvideo",
    "-",
]
pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8)

# get the average rgb value of a frame
def draw_next_frame_rgb_avg(raw_frame):
    frame = np.fromstring(raw_frame, dtype="uint8")
    frame = frame.reshape((320, 200, 3))
    rgb_avg = (
        int(np.average(frame[:, :, 0])),
        int(np.average(frame[:, :, 1])),
        int(np.average(frame[:, :, 2])),
    )
    return rgb_avg


# Go through the pipe one frame at a time until it's empty; store each frame's RGB values in rgb_list
rgb_list = []
x = 1  # optional; purely for displaying how many frames were processed
while True:  # as long as there's data in the pipe, keep reading frames
    try:
        next_frame = pipe.stdout.read(320 * 200 * 3)
    except:
        print(
            "No more frames to process (or error occurred). Number of frames processed:",
            x,
        )
        break

    if len(next_frame) < (320 * 200 * 3):
        break

    x = x + 1
    if x % every_n_frames == 0:
        rgb_list.append(draw_next_frame_rgb_avg(next_frame))


# create a new image width the same width as number of frames sampled,
# and draw one vertical line per frame at x=frame number
image_height = 2160  # set image height to whatever you want; you could use int(len(rgb_list)*9/16) to make a 16:9 image for instance
new = Image.new("RGB", (len(rgb_list), image_height))
draw = ImageDraw.Draw(new)
# x = the location on the x axis of the next line to draw
x_pixel = 1
for rgb_tuple in rgb_list:
    draw.line((x_pixel, 0, x_pixel, image_height), fill=rgb_tuple)
    x_pixel = x_pixel + 1
new.show()
new.save(outfilename, "PNG")

print("Script finished at " + time.strftime("%H:%M:%S"))
print("Frames" + str(len(rgb_list)))
