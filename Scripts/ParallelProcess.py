import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import time

from multiprocessing import Process, Queue
import matplotlib.pyplot as plt
import imutils
from imutils import contours
from imutils.perspective import four_point_transform
from utils import *

class QueueStorage():
    def __init__(self):
        self.level = 0
        self.mass = 0

def get_recent(queue,storage):
    halt = True
    while halt:
        if queue.empty():
            time.sleep(0.01)
        else:
            halt = False
    while not queue.empty():
        storage = queue.get()
    queue.put(storage)
    return storage

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def find_level(img,threshold=70,show=False):
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    bi = cv.bilateralFilter(img_gray, 10, 75, 75)

    thresh = cv.inRange(bi, threshold, 255);
    kernel_dilate = np.ones((5,5), np.uint8)
    kernel_erode = np.ones((10,10), np.uint8)
    iters = 3
    for a in range(iters):
        thresh = cv.dilate(thresh, kernel_dilate)
    for a in range(iters):
        thresh = cv.erode(thresh,kernel_erode)

    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv.contourArea, reverse=True)
    displayCnt = None

    for c in cnts:
        # approximate the contour
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.02 * peri, True)
        # if the contour has four vertices, then we have found chip
        if len(approx) == 4:
            displayCnt = approx
            break

    output = four_point_transform(img_gray, displayCnt.reshape(4, 2))
    l,w = output.shape

    offset = 0.05 * w
    channel = output[0:l,int(w//2-offset):int(w//2+offset)]
    chan_means = np.mean(channel,axis=1)

    x = range(len(chan_means))
    smoothed = smooth(chan_means,10)
    smoothed = smoothed[5:-5]

    smooth_diffs = np.diff(smoothed)
    level = np.where(smooth_diffs == np.min(smooth_diffs))[0][0]

    low_mean = np.mean(smoothed[0:20])
    level_mean = np.mean(smoothed[level:level+10])
    diff_internal = (level_mean - low_mean) / low_mean * 100

    reference = output[0:int(l),int(w//2-(4*offset)):int(w//2-(2*offset))]
    chan_mean = np.mean(channel)
    ref_mean = np.mean(reference)
    diff_ref = ((chan_mean-ref_mean)/ref_mean)*100

    if diff_internal < -5:
        level = level
    elif diff_ref > 80:
        level =  l
    else:
        level = 0

    if show:
        temp = output.copy()
        cv.line(temp,(w//3,level),(2*w//3,level),255,10)
        cv.imshow('level', temp)
        cv.waitKey(1)

    return level,diff_internal,diff_ref,l

def level_tracker(queue,storage):
    vid = cv.VideoCapture(1)

    while(True):
        storage = get_recent(queue,storage)
        ret, frame = vid.read()

        cv.imshow('frame', frame)
        try:
            level = find_level(frame,show=True)[0]
            storage.level = level
        except:
            storage.level = 'unknown'
        queue.put(storage)
        time.sleep(0.01)

        if cv.waitKey(1) & 0xFF == ord('='):
            break
