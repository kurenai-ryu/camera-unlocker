#!/usr/bin/python
# -*- coding: utf-8 -*-

# import the necessary packages
from __future__ import print_function

from flask import Flask, render_template, Response

from imutils.video import WebcamVideoStream
from imutils.video import FPS
import argparse
import imutils
import cv2
import time


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num-frames", type=int, default=100,
	help="# of frames to loop over for FPS test")
ap.add_argument("-d", "--display", type=int, default=-1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

"""
# grab a pointer to the video stream and initialize the FPS counter
print("[INFO] sampling frames from webcam...")
stream = cv2.VideoCapture(0)

print ("CV_CAP_PROP_BRIGHTNESS",stream.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS))
print ("CV_CAP_PROP_CONTRAST",stream.get(cv2.cv.CV_CAP_PROP_CONTRAST))
print ("CV_CAP_PROP_SATURATION",stream.get(cv2.cv.CV_CAP_PROP_SATURATION))
#print ("CV_CAP_PROP_HUE",stream.get(cv2.cv.CV_CAP_PROP_HUE))
print ("CV_CAP_PROP_GAIN",stream.get(cv2.cv.CV_CAP_PROP_GAIN))
print ("CV_CAP_PROP_EXPOSURE",stream.get(cv2.cv.CV_CAP_PROP_EXPOSURE))
print ("CV_CAP_PROP_FRAME_WIDTH",stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
print ("CV_CAP_PROP_FRAME_HEIGHT",stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))


stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,1.0)

time.sleep(2)
print ("CV_CAP_PROP_BRIGHTNESS",stream.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS))
print ("CV_CAP_PROP_CONTRAST",stream.get(cv2.cv.CV_CAP_PROP_CONTRAST))
print ("CV_CAP_PROP_SATURATION",stream.get(cv2.cv.CV_CAP_PROP_SATURATION))
#print ("CV_CAP_PROP_HUE",stream.get(cv2.cv.CV_CAP_PROP_HUE))
print ("CV_CAP_PROP_GAIN",stream.get(cv2.cv.CV_CAP_PROP_GAIN))
print ("CV_CAP_PROP_EXPOSURE",stream.get(cv2.cv.CV_CAP_PROP_EXPOSURE))


fps = FPS().start()
 
# loop over some frames
while fps._numFrames < args["num_frames"]:
	# grab the frame from the stream and resize it to have a maximum
	# width of 400 pixels
	(grabbed, frame) = stream.read()
	frame = imutils.resize(frame, width=400)
 
	# check to see if the frame should be displayed to our screen
	if args["display"] > 0:
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
 
	# update the FPS counter
	fps.update()
 
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
 
# do a bit of cleanup
stream.release()
cv2.destroyAllWindows()
"""

# created a *threaded* video stream, allow the camera sensor to warmup,
# and start the FPS counter
print("[INFO] sampling THREADED frames from webcam...")
vs = WebcamVideoStream(src=0).start()
vs.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,1.0)
fps = FPS().start()
 
# loop over some frames...this time using the threaded stream
while fps._numFrames < args["num_frames"]:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
 
	# check to see if the frame should be displayed to our screen
	if args["display"] > 0:
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
 
	# update the FPS counter
	fps.update()
 
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
 
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()

