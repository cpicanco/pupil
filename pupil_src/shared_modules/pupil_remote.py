'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''


from plugin import Plugin

from pyglui import ui
import zmq

import logging
logger = logging.getLogger(__name__)



class Pupil_Remote(Plugin):
    """pupil server plugin
    send messages to control Pupil Capture functions:

    'R' toggle recording
    'R rec_name' toggle recording and name new recording rec_name
    'T' set timebase to 0
    'C' start currently selected calibration
    """
    def __init__(self, g_pool,address="tcp://*:50020",menu_conf = {'collapsed':True,}):
        super(Pupil_Remote, self).__init__(g_pool)
        self.menu_conf = menu_conf
        self.order = .9 #excecute late in the plugin list.
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.address = address
        self.set_server(self.address)


    def set_server(self,new_address):
        try:
            self.socket.bind(new_address)
            self.address = new_address
        except zmq.ZMQError:
            logger.error("Could not set Socket.")


    def init_gui(self):
        help_str = 'Pupil Remote using REQ RREP schemme'
        self.menu = ui.Growing_Menu('Pupil Remote')
        self.menu.append(ui.Info_Text(help_str))
        self.menu.append(ui.Text_Input('address',self,setter=self.set_server,label='Address'))
        self.menu.append(ui.Button('Close',self.close))
        self.menu.configuration = self.menu_conf
        self.g_pool.sidebar.append(self.menu)

    def deinit_gui(self):
        if self.menu:
            self.menu_conf = self.menu.configuration
            self.g_pool.sidebar.remove(self.menu)
            self.menu = None


    def update(self,frame,events):
        try:
            msg = self.socket.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError :
            msg = None
        if msg:
            if msg[0] == 'R':
                rec_name = msg[2:]
                if rec_name:
                    self.g_pool.rec_name = rec_name
                for p in g_pool.plugins:
                    if p.class_name == 'Recorder':
                        p.toggle()
                        break
            elif msg == 'T':
                self.g_pool.timebase.value = self.g_pool.capture.get_now()
                logger.info("New timebase set to %s all timestamps will count from here now."%g_pool.timebase.value)
            elif msg == 'C':
                for p in g_pool.plugins:
                    if p.base_class_name == 'Calibration_Plugin':
                        p.toggle()
                        break


    def get_init_dict(self):
        d = {}
        d['address'] = self.address
        if self.menu:
            d['menu_conf'] = self.menu.configuration
        else:
            d['menu_conf'] = self.menu_conf
        return d


    def close(self):
        self.alive = False

    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either volunatily or forced.
        """
        self.deinit_gui()
        self.context.destroy()

