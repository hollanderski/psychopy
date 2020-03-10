#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, getInitVals

from psychopy.localization import _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'image.png')
tooltip = _translate('Image: present images (bmp, jpg, tif...)')

# only use _localized values for label values, nothing functional:
_localized = {'image': _translate('Image'),
              'ipd': _translate('IPD'),
              'mask': _translate('Mask'),
              'texture resolution': _translate('Texture resolution'),
              'flipVert': _translate('Flip vertically'),
              'flipHoriz': _translate('Flip horizontally'),
              'interpolate': _translate('Interpolate')}


class VRDisplayComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    categories = ['Stimuli']
    def __init__(self, exp, parentName, name='vrdisplay', image='kotek.jpg', ipd='0',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(VRDisplayComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'VRDisplay'
        self.targets = ['PsychoPy', 'PsychoJS']
        self.url = "http://www.psychopy.org/builder/components/image.html"
        self.exp.requirePsychopyLibs(['visual'])
        # params
        self.order += ['image', 'ipd', 'chroma']

        msg = _translate(
            "The image to be displayed - a filename, including path")
        self.params['image'] = Param(
            image, valType='str', allowedTypes=[],
            hint=msg,
            label=_localized["image"])

        msg = _translate(
            "The interpupillary distance - a value between 60 and 75mm")
        self.params['ipd'] = Param(
            ipd, valType='str', allowedTypes=[],
            hint=msg,
            label=_localized["ipd"])

        self.params['chroma'] = Param(
            False, valType='bool', updates='constant',
            hint=_translate(
                  "Add correction for chromatic aberration caused by Fresnel lenses"),
            label=_translate('Color correction'))

        
    def writeInitCode(self, buff):
        # build up an initialization string:
        #Behaviour of the component
        _in = "%(name)s = visual.VRDisplay(win=win, name='%(name)s', image=%(image)s, duration=%(stopVal)s"
        init_str = _in % self.params
        init_str += ")\n"
        buff.writeIndentedLines(init_str)

    def writeFrameCode(self, buff):
        _in = "%(name)s.display(%(name)s.stim, %(name)s.duration)\n"
        init_str = _in % self.params
        print(_in % self.params)
        buff.writeIndentedLines(init_str)

    #def writeRoutineStartCode(self,buff):
    #def writeRoutineEndCode(self,buff):
    

   
