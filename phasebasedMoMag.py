from perceptual.filterbank import *

import cv2

# determine what OpenCV version we are using
try:
    import cv2.cv as cv
    USE_CV2 = True
except ImportError:
    # OpenCV 3.x does not have cv2.cv submodule
    USE_CV2 = False

import sys
import numpy as np

from pyr2arr import Pyramid2arr
from temporal_filters import IdealFilterWindowed, ButterBandpassFilter


def phaseBasedMagnify(vidFname, vidFnameOut, maxFrames, windowSize, factor, fpsForBandPass, lowFreq, highFreq):

    # initialize the steerable complex pyramid
    steer = Steerable(4)
    pyArr = Pyramid2arr(steer)

    print ("Reading:", vidFname,)

    # get vid properties
    vidReader = cv2.VideoCapture(vidFname)
    #print("open: "+str(vidReader.isOpened()))
    if USE_CV2:
        # OpenCV 2.x interface
        vidFrames = int(vidReader.get(cv.CV_CAP_PROP_FRAME_COUNT))    
        width = int(vidReader.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        height = int(vidReader.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        fps = int(vidReader.get(cv.CV_CAP_PROP_FPS))
        func_fourcc = cv.CV_FOURCC
    else:
        # OpenCV 3.x interface
        vidFrames = int(vidReader.get(cv2.CAP_PROP_FRAME_COUNT))    
        width = int(vidReader.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidReader.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(vidReader.get(cv2.CAP_PROP_FPS))
        func_fourcc = cv2.VideoWriter_fourcc

    if np.isnan(fps):
        fps = 30

    print (' %d frames' % vidFrames,)
    print (' (%d x %d)' % (width, height),)
    print (' FPS:%d' % fps)

    # video Writer
    fourcc = func_fourcc('M', 'J', 'P', 'G')
    vidWriter = cv2.VideoWriter(vidFnameOut, fourcc, int(fps), (width,height), 1)
    print ('Writing:', vidFnameOut)

    # how many frames
    nrFrames = min(vidFrames, maxFrames)

    # read video
    # print steer.height, steer.nbands

    # setup temporal filter
    filter = IdealFilterWindowed(windowSize, lowFreq, highFreq, fps=fpsForBandPass, outfun=lambda x: x[0])
    # filter = ButterBandpassFilter(3, lowFreq, highFreq, fps=fpsForBandPass)

    print ('FrameNr:', )
    for frameNr in range( nrFrames + windowSize ):
        print (frameNr,)
        sys.stdout.flush() 

        if frameNr < nrFrames:
            # read frame
            _, im = vidReader.read()
               
            if im is None:
                # if unexpected, quit
                #print("im is none")
                break
			
            # convert to gray image
            if len(im.shape) > 2:
                grayIm = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
            else:
                # already a grayscale image?
                grayIm = im

            # get coeffs for pyramid
            coeff = steer.buildSCFpyr(grayIm)
            # print("coeff:",np.array(coeff[1]).shape)
            # image pyramid to video array
            # NOTE: on first frame, this will init rotating array to store the pyramid coeffs                 
            arr = pyArr.p2a(coeff)
            # print("arr: ", arr, arr.shape)

            phases = np.angle(arr)
            print("phase: ",phases,phases.shape)

            # add to temporal filter
            filter.update([phases])

            # try to get filtered output to continue            
            try:
                filteredPhases = filter.next()
                #print("filtered: ",filteredPhases.shape,filteredPhases)
            except StopIteration:
                #print("Stop")
                continue

            print ('*',)
            
            # motion magnification
            #magnifiedPhases = (phases - filteredPhases) + filteredPhases*factor    #原始相位-滤波后相位+放大后滤波后相位
            magnifiedPhases = phases + factor*filteredPhases    

            # create new array
            newArr = np.abs(arr) * np.exp(magnifiedPhases * 1j)

            # create pyramid coeffs
            try:
                newCoeff = pyArr.a2p(newArr)
            except StopIteration:
                print("End")

            
            # reconstruct pyramid
            out = steer.reconSCFpyr(newCoeff)

            # clip values out of range
            out[out>255] = 255
            out[out<0] = 0
            
            # make a RGB image
            rgbIm = np.empty((out.shape[0], out.shape[1], 3))
            rgbIm[:,:,0] = out
            rgbIm[:,:,1] = out
            rgbIm[:,:,2] = out
            
            #write to disk
            res = cv2.convertScaleAbs(rgbIm)
            vidWriter.write(res)

    # free the video reader/writer
    vidReader.release()
    vidWriter.release() 


################# main script

#vidFname = 'eye/baby.mp4';
#vidFname = 'eye/WIN_20151208_17_11_27_Pro.mp4.normalized.avi'
#vidFname = 'eye/embryos01_30s.mp4'
vidFname = "test/guitar.mp4"

# maximum nr of frames to process
maxFrames = 60000       #60000
# the size of the sliding window    #筛选freq的列表长度
windowSize = 30         #30
# the magnifaction factor
factor = 30
# the fps used for the bandpass (use -1 for input video fps)
fpsForBandPass = 600 #600 #筛选freq的范围:[0,fps/2] 
# low ideal filter
lowFreq = 72  #110
# high ideal filter
highFreq = 92  #140
# output video filename
#vidFnameOut = vidFname[:-4] + '-PhaseMag%dIdeal-lo%.2f-hi%.2f-fps%d.avi' % (factor, lowFreq, highFreq,fpsForBandPass)
vidFnameOut = "mag_Videos/guitar/test.avi"

phaseBasedMagnify(vidFname, vidFnameOut, maxFrames, windowSize, factor, fpsForBandPass, lowFreq, highFreq)



