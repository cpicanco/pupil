'''
(*)~----------------------------------------------------------------------------------

 Author: Carlos Picanco, Universidade Federal do Para.
 Hacked from Pupil - eye tracking platform (v0.3.7.4, v0.4x):

 seek_bar.py
 off_line_marker_detector.py

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

# Python
from os import path
from ast import literal_eval

# Open GL, glfw, pyglui, numpy
from gl_utils import draw_gl_polyline, draw_gl_point
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D
from glfw import glfwGetWindowSize, glfwGetCurrentContext, glfwGetCursorPos, GLFW_RELEASE,GLFW_PRESS
from pyglui import ui
import numpy as np

# Self
from plugin import Plugin

import logging

logger = logging.getLogger(__name__)

class Trial_Events_on_Seek_Bar(Plugin):
    """
    Displays vertical bars at the bottom seek bar
    in accord with external timestamped_events.

    """
    def __init__(self, g_pool, menu_conf={'pos':(300,300),'size':(300,300),'collapsed':False}):
        super(Trial_Events_on_Seek_Bar, self).__init__(g_pool)

        # Pupil Player system configs
        self.order = .8
        self.uniqueness = "unique"

        # Pupil Player data
        self.cap = g_pool.capture
        #self.current_frame_index = self.cap.get_frame_index()
        self.frame_count = self.cap.get_frame_count()

        # initialize empty menu
        self.menu = None

        # load menu configuration of last session
        self.menu_conf = menu_conf

        # initialize empty Plugin Data containers
        self.idx_begin_trial = []
        self.idx_end_limited_hold = []
        self.idx_first_response = []
        self.pos_begin_trial = []
        self.pos_first_response = []
        self.pos_end_limited_hold = []
        self.pos_else = []
 
        # load data
        self.timestamps = g_pool.timestamps
        self.load_events_to_draw()

        # display layout
        self.padding = 20. #in screen pixel

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

        for trial in self.scapp_output:
            # begin trial/show starter
            timestamp = trial[0][0]
            self.pos_begin_trial.append(np.abs(self.timestamps - float(timestamp)).argmin())

            # first response after starter
            timestamp = trial[1][0]
            self.pos_first_response.append(np.abs(self.timestamps - float(timestamp)).argmin())

            # consequence / end_limited_hold
            timestamp = trial[-1][0]
            print trial             
            self.pos_end_limited_hold.append(np.abs(self.timestamps - float(timestamp)).argmin())

    def init_gui(self):
        self.on_window_resize(glfwGetCurrentContext(),*glfwGetWindowSize(glfwGetCurrentContext()))

        # initialize the menu
        self.menu = ui.Scrolling_Menu('Trial Events on Seek Bar')

        # load the configuration of last session
        self.menu.configuration = self.menu_conf

        # add menu to the window
        self.g_pool.gui.append(self.menu)

        # add ui elements to the menu
        self.menu.append(ui.Button('Close', self.unset_alive))

    def cleanup(self):
        self.deinit_gui()

    def on_window_resize(self,window,w,h):
        self.window_size = w,h
        self.h_pad = self.padding * self.frame_count/float(w)
        self.v_pad = self.padding * 1./h

    def update(self,frame,events):
        pass

    def on_click(self,img_pos,button,action):
        pass


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
            draw_gl_point((pos_to_draw, 0), size = 5, color = (.5, .5, .5, .5))
            draw_gl_polyline( [(pos_to_draw,.05),(pos_to_draw,0)], color = (.5, .5, .5, .5))

        for pos_to_draw in self.pos_first_response:
            draw_gl_point((pos_to_draw, 0), size = 5, color = (.0, .0, .5, 1.))    
            draw_gl_polyline( [(pos_to_draw,.025),(pos_to_draw,0)], color = (.0, .0, .7, 1.))

        for pos_to_draw in self.pos_end_limited_hold:
            draw_gl_point((pos_to_draw, 0), size = 5, color = (.5, .0, .0, 1.)) 
            draw_gl_polyline( [(pos_to_draw,.025),(pos_to_draw,0)], color = (.7, .0, .0, 1.))
        
        for x, first_response in enumerate(self.pos_first_response):
            draw_gl_polyline( [(self.pos_end_limited_hold[x],.025),(first_response,.025)], color = (1., .5, .0, 1.))    

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
        return {'menu_conf':self.menu.configuration}

    def clone(self):
        return Trial_Events_on_Seek_Bar(**self.get_init_dict())
