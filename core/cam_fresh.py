from __future__ import print_function
import os
import sys
import time
import threading
import cv2 
import multiprocessing as mp
import numpy as np


# also acts (partly) like a cv.VideoCapture
class FreshestFrame(threading.Thread):
	def __init__(self, camera, name='FreshestFrame'):
		# self.capture = capture
		self.camera = camera
		self.capture = cv2.VideoCapture(self.camera)
		self.capture.set(cv2.CAP_PROP_FPS, 10)
		assert self.capture.isOpened()

		# this lets the read() method block until there's a new frame
		self.cond = threading.Condition()

		# this allows us to stop the thread gracefully
		self.running = False

		# keeping the newest frame around
		self.frame = None

		# passing a sequence number allows read() to NOT block
		# if the currently available one is exactly the one you ask for
		self.latestnum = 0

		# this is just for demo purposes		
		self.callback = None
		# self.event = threading.Event()
		
		super().__init__(name=name)
		self.start()

	def change_camera(self, camera):
		# self.running = False
		# self.release()
		# self.capture = capture

		self.camera = camera
		self.capture = cv2.VideoCapture(self.camera)

		self.capture.set(cv2.CAP_PROP_FPS, 10)
		assert self.capture.isOpened()
		# # self.running = True

		# try:
		# 	self.camera = camera
		# 	self.capture = cv2.VideoCapture(self.camera)

		# 	self.capture.set(cv2.CAP_PROP_FPS, 10)
		# 	if not self.capture.isOpened():
		# 		raise Exception("Failed to open the camera.")
		
		# except Exception as e:
		# 	print(f"Error while changing the camera: {str(e)}")
		
	def start(self):
		self.running = True
		super().start()

	def release(self, timeout=None):
		self.running = False
		self.join(timeout=timeout)
		self.capture.release()

	def run(self):
		counter = 0
		while self.running:
			# block for fresh frame
			(rv, img) = self.capture.read()
			assert rv
			counter += 1

			# if not rv:
			# 	# Handle the case where frame reading fails
			# 	# print("Error reading frame from camera.")
			# 	continue  # Skip this iteration and continue the loop
        
			# counter += 1

			# publish the frame
			with self.cond: # lock the condition for this operation
				self.frame = img if rv else None
				self.latestnum = counter
				self.cond.notify_all()

			if self.callback:
				self.callback(img)

	def read(self, wait=True, seqnumber=None, timeout=None):
		# with no arguments (wait=True), it always blocks for a fresh frame
		# with wait=False it returns the current frame immediately (polling)
		# with a seqnumber, it blocks until that frame is available (or no wait at all)
		# with timeout argument, may return an earlier frame;
		#   may even be (0,None) if nothing received yet

		# if self.event:
		# 	exit()

		with self.cond:
			if wait:
				if seqnumber is None:
					seqnumber = self.latestnum+1
				if seqnumber < 1:
					seqnumber = 1
				
				rv = self.cond.wait_for(lambda: self.latestnum >= seqnumber, timeout=timeout)
				if not rv:
					return (self.latestnum, self.frame)

			return (self.latestnum, self.frame)

