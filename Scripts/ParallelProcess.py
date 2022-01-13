import numpy as np
import cv2 as cv
import time

from multiprocessing import Process, Queue
import imutils
from imutils import contours
from imutils.perspective import four_point_transform
from scipy.signal import find_peaks

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

def find_level(img,threshold=50,show=False):
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    img_gray = cv.rotate(img_gray, cv.ROTATE_180)
    bi = cv.bilateralFilter(img_gray, 10, 75, 75)
    thresh = cv.inRange(bi, threshold, 255);

    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL,
    cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv.contourArea, reverse=True)
    displayCnt = None

    boundRect = [None]*len(cnts)

    for i,c in enumerate(cnts):
        boundRect[i] = cv.boundingRect(c)
    boundRect = boundRect[0]
    temp = img_gray.copy()

    if show:
        cv.rectangle(temp, (int(boundRect[0]), int(boundRect[1])), \
                  (int(boundRect[0]+boundRect[2]), int(boundRect[1]+boundRect[3])), 256, 2)
        # cv.imshow('Rectangle',temp)

    corners = np.array([[[int(boundRect[0]), int(boundRect[1])], \
          [int(boundRect[0]), int(boundRect[1]+boundRect[3])],\
          [int(boundRect[0]+boundRect[2]), int(boundRect[1])],\
          [int(boundRect[0]+boundRect[2]), int(boundRect[1]+boundRect[3])]]])

    output = four_point_transform(img_gray, corners.reshape(4, 2))
    l,w = output.shape
    output = output[int(l*0.2):int(l*0.8),0:w]
    l,w = output.shape

    offset = 0.1*w
    channel = output[0:l,int(w//2-offset):int(w//2+offset)]

    chan_means = np.mean(channel,axis=1)
    x = range(len(chan_means))

    smoothed = smooth(chan_means,10)
    smoothed = smoothed[5:-5]

    smooth_diffs = [-1*d for d in np.diff(smoothed)]

    reference = output[0:int(l),int(w//2-(4*offset)):int(w//2-(2*offset))]
    ref_mean = np.mean(reference)
    chan_mean = np.mean(channel)

    diff_ref = ((chan_mean-ref_mean)/ref_mean)*100

    try:
        peaks, prop = find_peaks(smooth_diffs, width=5, height=2)
        level = int(round(prop['right_ips'][0],0))
    except:
        # print(f'No level detected: ref {diff_ref}')
        if diff_ref > 50:
            level = l
        else:
            level = 0

    percent = 100 - (level / l *100)
    # print('Expected level:',percent)
    if show:
        temp = output.copy()
        cv.line(temp,(int(w//2-offset),0),(int(w//2-offset),l),255,1)
        cv.line(temp,(int(w//2+offset),0),(int(w//2+offset),l),255,1)
        cv.line(temp,(0,level),(w,level),255,3)
        cv.line(temp,(int(w//2-(4*offset)),0),(int(w//2-(4*offset)),l),0,1)
        cv.line(temp,(int(w//2-(2*offset)),0),(int(w//2-(2*offset)),l),0,1)
        cv.imshow('Annotated',temp)
    return percent

def level_tracker(queue,storage,port):
    while True:
        while True:
            try:
                # cv.namedWindow('Level_tracker')
                vid = cv.VideoCapture(port)
                if vid.isOpened():  # try to get the first frame
                    print('-----Level tracker cam found')
                    break
                else:
                    print('......Waiting for level_tracker......')
                    time.sleep(1)
            except:
                print('......level_tracker failed......')
                time.sleep(1)
        levels = []
        counter = 0
        while(True):
            storage = get_recent(queue,storage)

            try:
                ret, frame = vid.read()

                # cv.imshow('Level_tracker', frame)
                level = find_level(frame,show=True)


                if len(levels) < 5:
                    levels.append(level)
                else:
                    levels = levels[1:]
                    levels.append(i)

                storage.level = round(np.mean(level),0)
            except:
                counter += 1
                if counter > 50:
                    storage.level = 'unknown'
                    counter = 0
            queue.put(storage)
            time.sleep(0.01)

            if cv.waitKey(1) & 0xFF == ord('='):
                break

### Balance tracker code:

def find_screen(img):
    b,g,r = cv.split(img)
    #Identify the screen in the blue channel
    thresh = cv.inRange(b, 100, 255)
    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv.contourArea, reverse=True)
    displayCnt = None

    for c in cnts:
        # approximate the contour
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.02 * peri, True)
        # if the contour has four vertices, then we have found
        # the thermostat display
        if len(approx) == 4:
            displayCnt = approx
            break

    screen = four_point_transform(r, displayCnt.reshape(4, 2))
    l,w = screen.shape
    ## Cuts off the empty space on the sides of the screen
    screen = screen[l//10:(l*9)//10,w//10:(w*9)//10]
    return screen

def prepare_image(screen):
    img = 255-screen

    thresh = cv.inRange(img, 200, 255);
    cimg = cv.cvtColor(thresh,cv.COLOR_GRAY2BGR)
    return img,cimg

def find_decimal(img,param2):
    # print('Finding circle:',param2)
    circles = cv.HoughCircles(img,cv.HOUGH_GRADIENT,1,10,
                            param1=50,param2=param2,minRadius=0,maxRadius=7)
    try:
        circles = np.uint16(np.around(circles))
        # print(circles[0][0])
        return circles[0][0]
    except:
        if param2 == 0: return
        return find_decimal(img,param2-1)

def remove_decimal(img,cimg,param2=20):
    circle = find_decimal(img,param2)

    cv.circle(cimg,(circle[0],circle[1]),circle[2]+3,(0,0,0),-1)
    return img,cimg,circle

def outline_numbers(img,cimg,show=False):
    _,_,thresh = cv.split(cimg)

    # closing operation
    kernel_dilate = np.ones((5,5), np.uint8)
    kernel_erode = np.ones((3,3), np.uint8)
    iters = 3

    # dilate
    for a in range(iters):
        thresh = cv.dilate(thresh, kernel_dilate)

    # # erode
    for a in range(iters):
        thresh = cv.erode(thresh,kernel_erode)

    # start processing
    contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

    # draw
    number_cont = []
    for contour in contours:
        area = cv.contourArea(contour)
        if area > 300:
            cv.drawContours(img, [contour], 0, (255,0,0), 3)
            number_cont.append(contour)

    if show:
        cv.imshow("contours", img)
        cv.waitKey(1)
    return number_cont,thresh

def get_bounds(img,contour):
    # get res of each number
    h, w = img.shape[:2];
    left = w;
    right = 0;
    top = h;
    bottom = 0;
    for point in contour:
        point = point[0];
        x, y = point;
        if x < left:
            left = x;
        if x > right:
            right = x;
        if y < top:
            top = y;
        if y > bottom:
            bottom = y;
    tl = [left, top];
    br = [right, bottom]
    return [tl, br]

def reorder_contours(contours):
    bboxes = enumerate([cv.boundingRect(i) for i in contours])
    bboxes=sorted(bboxes, key=lambda x: x[1][0])
    new_order = [x[0] for x in bboxes]
    return [contours[i] for i in new_order]

def get_all_numbers(thresh,number_cont):
    bounds = []
    for contour in number_cont:
        bounds.append(get_bounds(thresh,contour))

    # crop out each number
    cuts = [];
    for bound in bounds:
        tl, br = bound;
        cut_img = thresh[tl[1]:br[1], tl[0]:br[0]];
        cuts.append(cut_img);

    lengths = []
    widths = []
    for cut in cuts:
        l,w = cut.shape
        lengths.append(l)
        widths.append(w)
    m_l = np.max(lengths)
    m_w = np.max(widths)

    pad_cuts = []
    for cut in cuts:
        l,w = cut.shape
        l_diff = m_l - l
        w_diff = m_w - w

        if w_diff > m_w/5 or l_diff > m_l/4:
            vert_padding = np.zeros([l_diff//2,w])
            padded = np.concatenate([vert_padding,cut,vert_padding])
            left_padding = np.zeros([padded.shape[0],w_diff])
            padded = np.hstack([left_padding,padded])
        else:
            padded = cut
        pad_cuts.append(padded)

    numbers = []
    for roi in pad_cuts:
        (roiH, roiW) = roi.shape
        (w,h) = roiW,roiH
        (dW, dH) = (int(roiW * 0.33), int(roiH * 0.15))
        dHC = int(roiH * 0.1)
        # define the set of 7 segments

        segments = [
            ((w//4, 0), ((3*w)//4, h//5)),	# top
            ((0, h//5), ((w*2)//5, (2*h) // 5)),	# top-left
            (((w*3)//5, h//5), (w, (2*h) // 5)),	# top-right
            ((w//4, (h // 2) - dHC) , ((w*3)//4, (h // 2) + dHC)), # center
            ((0, (h*3)//5), ((w*2)//5, (h*4)//5)),	# bottom-left
            (((w*3)//5, (h*3)//5), (w, (h*4)//5)),	# bottom-right
            ((w//6, (4*h)//5), ((w*5)//6, h))	# bottom
        ]

        names = ['top','tl','tr','center','bl','br','bot']

        on = []
        for name,(i, ((xA, yA), (xB, yB))) in zip(names,enumerate(segments)):
            # extract the segment ROI, count the total number of
            # thresholded pixels in the segment, and then compute
            # the area of the segment

            segROI = roi[yA:yB, xA:xB]
            total = cv.countNonZero(segROI)
            area = (xB - xA) * (yB - yA)
            # if the total number of non-zero pixels is greater than
            # 50% of the area, mark the segment as "on"
            if total / float(area) > 0.5:
                on.append(i)
        numbers.append(get_num(on))
    return numbers

def get_num(flags):
    if flags == [0,1,2,4,5,6]:
        return '0';
    elif flags == [2,5]:
        return '1';
    elif flags == [0,2,3,4,6]:
        return '2';
    elif flags == [0,2,3,5,6]:
        return '3';
    elif flags == [1,2,3,5]:
        return '4';
    elif flags == [0,1,3,5,6]:
        return '5';
    elif flags == [0,1,3,4,5,6]:
        return '6';
    elif flags == [0,2,5]:
        return '7';
    elif flags == [0,1,2,3,4,5,6]:
        return '8';
    elif flags == [0,1,2,3,5,6]:
        return '9';
    elif flags == [3]:
        return '-'
    else:
        return 'u'

def convert_to_float(lst):
    if 'u' in lst:
        return 'Unknown'
    lst = [l for l in lst]
    str_num = ''.join(lst)
    dec_num = float(str_num[:-1] + '.' + str_num[-1])
    return dec_num

def extract_all_numbers(img, show=False):
    screen = find_screen(img)
    img,cimg = prepare_image(screen)
    img,cimg,decimal = remove_decimal(img,cimg)
    number_cont,thresh = outline_numbers(img,cimg,show=show)
    number_cont = reorder_contours(number_cont)
    numbers = get_all_numbers(thresh,number_cont)
    final_number = convert_to_float(numbers)

    return final_number

def balance_tracker(queue, storage,port):
    while True:
        while True:
            try:
                # cv.namedWindow('Balance_tracker')
                vid = cv.VideoCapture(port)
                if vid.isOpened():  # try to get the first frame
                    print('-----balance tracker cam found')
                    break
                else:
                    print('......Waiting for balance_tracker......')
                    time.sleep(1)
            except:
                print('......balance_tracker failed......')
                time.sleep(1)

        masses = []
        counter = 0
        while(True):
            storage = get_recent(queue,storage)
            try:
                ret, frame = vid.read()

                # cv.imshow('Balance_tracker', frame)
                mass = extract_all_numbers(frame,show=True)

                if len(masses) < 5:
                    masses.append(mass)
                else:
                    masses = masses[1:]
                    masses.append(i)

                storage.mass = round(np.mean(mass),1)
            except:
                counter += 1
                if counter > 50:
                    storage.mass = 'unknown'
                    counter = 0
            queue.put(storage)
            time.sleep(0.01)

            if cv.waitKey(1) & 0xFF == ord('='):
                break