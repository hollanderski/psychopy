#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function

from builtins import str

import numpy as np
import cv2
from PIL import Image
import pyglet
import time, random

import psychopy  # so we can get the __path__
from psychopy import logging, core, event, visual
from psychopy.constants import *
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.visual.basevisual import MinimalStim
from psychopy.visual.basevisual import (ContainerMixin, ColorMixin,
                                       TextureMixin)

# https://www.socsci.ru.nl/wilberth/nocms/psychopy/print.php

font = cv2.FONT_HERSHEY_SIMPLEX 
fontScale = 1
thickness = 1
color = (255, 255, 255)  
radius=15
screen_res = 1280, 720
size=1000
img = np.full((size,size, 3), 127, np.uint8) 
height, width, channels = img.shape 
margin = 300 #250 
topLeft=(0+margin,0+margin)
topRight = (width-margin, 0+margin)  
downRight = (width-margin, height-margin)  
downLeft = (0+margin, height-margin) 
x = np.round(width/2).astype("int")
y = np.round(height/2).astype("int")
center=(x,y)


pos = [(topLeft,(0,1)), (topRight,(1,1)), (downRight,(1,0)), (downLeft, (0,0)), (center,(0.5,0.5))]
# /!\ "We use a normalized coordinate system with the origin 0,0 at the bottom left and 1,1 at the top right"
# (0,1)                (1,1)
#     +----world-frame---+
#     |                  |
#     |         +---+    |
#     |         | s |    |
#     |         +---+    |
#     +------------------+
# (0,0)                (1,0)


def normalize_coordinates(row, col, img):
    num_rows, num_cols = img.shape[:2]

    row=num_rows-row
    x = (col)/(num_cols - 1.)
    y = (row)/(num_rows - 1.)

    return x,y
    


def pixel_coordinates(row, col, img):
    num_rows, num_cols = img.shape[:2]    
    x = (col)*(num_cols - 1.)
    y=row*(num_rows - 1.)
    c=normalize_coordinates(center[1], center[0], img)
    y=num_rows-y
        
    return x, y


class VRDisplay:

    def __init__(self, win, name, image, duration):

        self.stim=cv2.imread(image)
        self.distance=149
        self.name=name
        win.fullsrc=True
        self.win=win
        self.duration=duration
        self.clock=core.Clock()

            
    def display(self, img, s=2, compensation=False):
        """
        Display an image img in the HMD during s seconds.
        """
    
        # Compensate chromatic aberration :
        if(compensation):
            self.image=self.aberrationCompensation(img)
        else :
            self.image=img # the original image is saved before opencv manipulation

        # Set stereoscopic view (binocular + distance from screen borders):
        im_h = cv2.hconcat([self.image, self.image])
        img_margin=cv2.copyMakeBorder(im_h, self.distance, self.distance, self.distance, self.distance, cv2.BORDER_CONSTANT)

        # Convert opencv image to PIL image (PsychoPy requirement for ImageStim) :
        pil_image=Image.fromarray(cv2.cvtColor(img_margin, cv2.COLOR_BGR2RGB))

        # Visual stimulus creation (PsychoPy) :
        self.currentFrame= visual.ImageStim(self.win, image = pil_image, size=(1.8,1))#(2,2))
        self.currentFrame.setAutoDraw(True)

        self.clock.reset()
        # Change frame after s seconds or when a key is pressed :
        while True:
            self.win.flip()
            theKey = event.getKeys()
            if len(theKey) != 0 or self.clock.getTime()>=s:
                self.currentFrame.setAutoDraw(False)
                break
     

    def calibration(self):
    
        """
        Calibration of the Pupil Lab gaze tracker :
        - Display dots every 2s at reference positions(posRef) on the screen
        - Send the timestamp of the observation of the pupils at ref_pos to the tracker
        cf https://github.com/pupil-labs/hmd-eyes/blob/master/python_reference_client/hmd_calibration_client.py
        """
        
        thickness = 1
        radius=15
        color = (255, 0, 0)  
        txt='Please follow the dots'
        size= cv2.getTextSize(txt, font, 1, 2)[0]
        x = np.round(width/2-size[0]/2).astype("int")
        y = np.round(height/2).astype("int")
        center2 = (x,y)
        self.image=np.full((1000, 1000, 3), 127, np.uint8)
        cv2.putText(self.image, txt, center2, font, fontScale, color, thickness, cv2.LINE_AA) 
        #color = (0,0,255)   
        self.display(self.image, 10, False)


        try: pupil
        except NameError: print("The tracker is undefined. Abort calibration.")
        else: pupil.start_calib()


        self.image=np.full((1000, 1000, 3), 127, np.uint8)
        #self.image[:] = (255, 255, 255)

        
        ref_data=[]
        
        for posView, posRef in pos :
            self.image=np.full((1000, 1000, 3), 127, np.uint8) #reset
            #self.image[:] = (255, 255, 255) #reset
            cv2.circle(self.image, posView, radius, color, -1)
            self.display(self.image, 2, False)
            
            posRef=normalize_coordinates(posView[1]+self.distance, posView[0]+self.distance, img)
            print('subject now looks at position:', posRef, posView)
            
            try: pupil
            except NameError: print("The tracker is undefined.")
            else: pupil.add_ref(posRef)
        
        try: pupil
        except NameError: print("No data will be sent.")
        else:
            pupil.send_ref()
            pupil.stop_calib()
            
        
    def validation(self, maxDots=10):
        
        print("Start validation")
        radius=15
        color = (255, 0,0)   

         
        for i in range(maxDots):
            point=(random.randint(0+margin, width-margin), random.randint(0+margin, height-margin))
            self.image=np.full((1000, 1000, 3), 127, np.uint8)
            cv2.circle(self.image, point, radius, color, -1)
            self.display(self.image, 2, False)
            xnorm, ynorm = normalize_coordinates(point[1], point[0], self.image)

            try: pupil
            except NameError: print("The tracker is undefined.")
            else:
                ellipse = pupil.get_tracker_data('ellipse')
                print('2d coordinates :', point[0], point[1])
                print('\ntracker thinks :', ellipse['center'])
                xp=ellipse['center'][0]-self.distancese
                yp=ellipse['center'][1]-self.distance
                xp = np.round(xp).astype("int")
                yp = np.round(yp).astype("int")
                cv2.circle(self.image, (xp,yp), radius, (0,0,255), -1)
                self.display(self.image, 2, False)

        
    def aberrationCompensation(self,src):

        # Split RGB channels :
        b1,g1,r1=cv2.split(src)
        num_rows, num_cols = src.shape[:2]

        dist=1
        
        btemp=b1.copy()
        rtemp=r1.copy()

        distance=3 #maximum pixel offset
       
        def distancec(x,y):
            distance=np.sqrt(np.power(num_rows/2-y,2)+np.power(num_cols/2-x,2))
            distance = (distance)/(num_cols - 1.) 
            distance[distance>0.2]*=4
            distance=np.round(distance).astype("int")
            return distance
        
        # Matrix of pixel offset :
        result=np.fromfunction(lambda i, j: distancec(i,j),(num_rows,num_cols), dtype=int)
        rr=np.zeros((len(r1)+2*distance,len(r1[0])+2*distance))
        bb=np.zeros((len(b1)+2*distance,len(b1[0])+2*distance))
        

        for decalage in range(0,distance+1):
            row,col=np.where(result==decalage)
            a=np.where(np.logical_and(row<= 503, col<= 506))[0]
            b=np.where(np.logical_and(row<= 503, col>= 503))[0]
            c=np.where(np.logical_and(row>= 500, col>= 500))[0]
            d=np.where(np.logical_and(row>= 500, col<= 503))[0]
             
            bb[row[np.array(a)] +distance+decalage,col[np.array(a)] +distance+decalage]=b1[row[np.array(a)],col[np.array(a)]]
            rr[row[np.array(a)] +distance-decalage*0,col[np.array(a)] +distance-decalage*0]=r1[row[np.array(a)] ,col[np.array(a)] ]
            
            bb[row[np.array(b)] +distance+decalage,col[np.array(b)] +distance-decalage]=b1[row[np.array(b)] ,col[np.array(b)] ]
            rr[row[np.array(b)] +distance-decalage*0,col[np.array(b)] +distance+decalage*0]=r1[row[np.array(b)] ,col[np.array(b)] ]

            bb[row[np.array(c)] +distance-decalage,col[np.array(c)] +distance-decalage]=b1[row[np.array(c)] ,col[np.array(c)] ]
            rr[row[np.array(c)] +distance+decalage*0,col[np.array(c)] +distance+decalage*0]=r1[row[np.array(c)] ,col[np.array(c)] ]
            
            bb[row[np.array(d)] +distance-decalage,col[np.array(d)] +distance+decalage]=b1[row[np.array(d)] ,col[np.array(d)] ]
            rr[row[np.array(d)] +distance+decalage*0,col[np.array(d)] +distance-decalage*0]=r1[row[np.array(d)] ,col[np.array(d)] ]


        gg=np.zeros((len(g1)+2*distance,len(g1[0])+2*distance))
        gg[distance:-distance,distance:-distance]=g1
   
        return cv2.merge((bb,gg,rr))
   
    
    def test(self):
        
        if self.clock.getTime() - self.start_time > self.dot_display_time:
            self.start_time = self.clock.getTime()
            self.win.flip()
            self.currentFrame.draw()
            self.win.flip()
            print("time=", self.start_time )
        

    def GUIControls(self):
        cv2.createTrackbar('distance','window',0,255,lambda x : self.spaceBetweenEyesCallback(x))
        cv2.setTrackbarPos('distance','window',149)

    def spaceBetweenEyesCallback(self, x):
        self.spaceBetweenEyes=x
        self.distance=x
        self.image=self.currentFrame
        im_h = cv2.hconcat([self.image, self.image])
        img_margin=cv2.copyMakeBorder(im_h, self.distance, self.distance, self.distance, self.distance, cv2.BORDER_CONSTANT)
        cv2.imshow("window", img_margin); 


