'''
(*)~----------------------------------------------------------------------------------

 Author: Carlos Picanco, Universidade Federal do Para.
 Hacked from Pupil - eye tracking platform (v0.3.7.4 .. v0.5x):

 seek_bar.py

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

# Python
from os import path
from ast import literal_eval

# OpenGL, glfw, pyglui, numpy
from pyglui.cygl.utils import RGBA,draw_points,draw_polyline
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from glfw import glfwGetWindowSize, glfwGetCurrentContext, GLFW_KEY_V, GLFW_KEY_COMMA
from pyglui import ui
import numpy as np

# Self
from plugin import Plugin

import logging

logger = logging.getLogger(__name__)

class Segmentation(Plugin):
    """
    Display vertical bars at the bottom seek bar
    in accord with external timestamped_events or
    custom user defined events.

    One should be able to auto-trim based on those events.

    """
    def __init__(self, g_pool, custom_events=[], session_type='A', mode='chain', keep_create_order=True):
        super(Segmentation, self).__init__(g_pool)
        self.trim_marks = g_pool.trim_marks

        # display layout
        self.padding = 20. #in screen pixel

        # Pupil Player system configs
        self.order = .8
        self.uniqueness = "unique"

        # Pupil Player data
        self.capture = g_pool.capture
        #self.current_frame_index = self.capture.get_frame_index()
        self.frame_count = self.capture.get_frame_count()
        self.frame_index = None

        # initialize empty menu
        self.menu = None
        self.session_type = 'A'
        self.mode = mode
        self.keep_create_order = keep_create_order

        # initialize empty Plugin Data containers
        self.idx_begin_trial = []
        self.idx_end_limited_hold = []
        self.idx_first_response = []
        self.pos_begin_trial = []
        self.pos_first_response = []
        self.pos_end_limited_hold = []
        self.pos_else = []
        
        self.custom_events_dir = path.join(self.g_pool.rec_dir,'custom_events.npy')
        try:
            self.custom_events = list(np.load(self.custom_events_dir))
        except:
            logger.warning("No custom events were found at: "+ self.custom_events_dir)
            self.custom_events = custom_events
            if not self.custom_events:
                logger.warning("No chached events were found.") 
 
        # load data
        self.timestamps = g_pool.timestamps

    def event_undo(self, arg):
        if self.custom_events:
            self.custom_events.pop()
            if not self.keep_create_order:
                self.custom_events = sorted(self.custom_events, key=int)


    def create_custom_event(self, arg):
        if self.frame_index:
            if self.frame_index not in self.custom_events:
                self.custom_events.append(self.frame_index)
                if not self.keep_create_order:
                    self.custom_events = sorted(self.custom_events, key=int)

    def save_custom_event(self):  
        np.save(self.custom_events_dir,np.asarray(self.custom_events))

    def auto_trim(self):
        # take defined sections and pass them to the trim_marks
        # self.trim_marks
        pass

    def load_events_to_draw(self):
        scapp_output_path = path.join(self.g_pool.rec_dir,'scapp_output')      
        self.scapp_output = [[]]
        with open(scapp_output_path, 'r') as scapp_output:
            for line in scapp_output:
                (trial_no, timestamp, event) = literal_eval(line)

                i = int(trial_no)

                if i > len(self.scapp_output):
                    self.scapp_output.append([])
                self.scapp_output[i - 1].append((timestamp, event))
        if self.session_type == 'A':
            for trial in self.scapp_output:
                # begin trial/show starter
                timestamp = trial[0][0]
                self.pos_begin_trial.append(np.abs(self.timestamps - float(timestamp)).argmin())

                # first response after starter
                timestamp = trial[1][0]
                self.pos_first_response.append(np.abs(self.timestamps - float(timestamp)).argmin())

                # consequence / end_limited_hold
                timestamp = trial[-1][0]             
                self.pos_end_limited_hold.append(np.abs(self.timestamps - float(timestamp)).argmin())
        
        elif self.session_type == 'B':
            pass

    def init_gui(self):
        # initialize the menu
        self.menu = ui.Scrolling_Menu('Segmentation')
        # add ui elements to the menu
        self.menu.append(ui.Button('Close', self.unset_alive))
        self.menu.append(ui.Info_Text('This plugin allows one to eye inspect events along pre-defined sessions. Select the type of session and click on "Load Events".'))
        self.menu.append(ui.Selector('session_type',self,label='Session Type',selection=['A','B', 'C'] )) 
        self.menu.append(ui.Button('Load Events',self.load_events_to_draw))
        self.menu.append(ui.Info_Text('It is possible to auto trim the video and data export using those events.'))
        self.menu.append(ui.Selector('mode',self,label='Trim Mode',selection=['chain','in out pairs'] )) 
        self.menu.append(ui.Button('Auto-trim',self.auto_trim))
        self.menu.append(ui.Info_Text('You can create custom events by pressing "v". To undo press ", (comma)". Remember to save them when your were done.'))
        self.menu.append(ui.Switch('keep_create_order',self,label="Keep Creation Order"))
        self.menu.append(ui.Hot_Key('create_event',setter=self.create_custom_event,getter=lambda:True,label='V',hotkey=GLFW_KEY_V))
        self.menu.append(ui.Hot_Key('event_undo',setter=self.event_undo,getter=lambda:True,label=',',hotkey=GLFW_KEY_COMMA))
        self.menu.append(ui.Button('Save Events',self.save_custom_event))

        # add menu to the window
        self.g_pool.gui.append(self.menu)
        self.on_window_resize(glfwGetCurrentContext(),*glfwGetWindowSize(glfwGetCurrentContext()))


    def cleanup(self):
        self.deinit_gui()

    def on_window_resize(self,window,w,h):
        self.window_size = w,h
        self.h_pad = self.padding * self.frame_count/float(w)
        self.v_pad = self.padding * 1./h

    def update(self,frame,events):
        self.frame_index = frame.index

    def gl_display(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(-self.h_pad,  (self.frame_count)+self.h_pad, -self.v_pad, 1+self.v_pad) # ranging from 0 to cache_len-1 (horizontal) and 0 to 1 (vertical)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        #Draw...............................................................................
        
        for pos_to_draw in self.pos_begin_trial:   
            draw_points([(pos_to_draw, 0)], size = 5, color = RGBA(.5, .5, .5, .5))
            draw_polyline( [(pos_to_draw,.05),(pos_to_draw,0)], color = RGBA(.5, .5, .5, .5))

        for pos_to_draw in self.pos_first_response:
            draw_points([(pos_to_draw, 0)], size = 5, color = RGBA(.0, .0, .5, 1.))    
            draw_polyline( [(pos_to_draw,.025),(pos_to_draw,0)], color = RGBA(.0, .0, .7, 1.))

        for pos_to_draw in self.pos_end_limited_hold:
            draw_points([(pos_to_draw, 0)], size = 5, color = RGBA(.5, .0, .0, 1.)) 
            draw_polyline( [(pos_to_draw,.025),(pos_to_draw,0)], color = RGBA(.7, .0, .0, 1.))
        
        for x, first_response in enumerate(self.pos_first_response):
            draw_polyline( [(self.pos_end_limited_hold[x],.025),(first_response,.025)], color = RGBA(1., .5, .0, 1.))    

        for e in self.custom_events:
            draw_polyline([(e,.05),(e,0)], color = RGBA(.8, .8, .8, .8))

        size = len(self.custom_events)
        if size > 1:
            for i, e in enumerate(self.custom_events):
                draw_points([(e, .025)], size = 5, color = RGBA(.1, .5, .5, 1.)) 

            i = 0
            while True:
                if i == 0:
                    draw_polyline([(self.custom_events[i],.025),(self.custom_events[i+1],0.025)], color = RGBA(.8, .8, .8, .8))
                elif (i > 0) and (i < (size-1)):
                    draw_polyline([(self.custom_events[i] +1,.025),(self.custom_events[i+1],0.025)], color = RGBA(.8, .8, .8, .8))

                if self.mode == 'chain':
                    i += 1
                elif self.mode == 'in out pairs':
                    i += 2

                if i > (size-1):
                    break
                    
        #Draw...............................................................................

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def deinit_gui(self):
        if self.menu:
            self.g_pool.gui.remove(self.menu)
            self.menu = None

    def unset_alive(self):
        self.alive = False

    def get_init_dict(self):
        return {'session_type':self.session_type,
                'custom_events':self.custom_events,
                'mode':self.mode,
                'keep_create_order':self.keep_create_order}

    def clone(self):
        return Segmentation(**self.get_init_dict())
