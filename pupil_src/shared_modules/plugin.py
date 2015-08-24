'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''
import os,sys
import logging
logger = logging.getLogger(__name__)
import importlib


'''
A simple example Plugin: 'display_recent_gaze.py'
It is a good starting point to build your own plugin.
'''


class Plugin(object):
    """docstring for Plugin
    plugin is a base class
    it has all interfaces that will be called
    instances of this class usually get added to a plugins list
    this list will have its members called with all methods invoked.

    """
    # if you have a plugin that can exist multiple times make this false in your derived class
    uniqueness = 'by_class'
    # uniqueness = 'not_unique'
    # uniqueness = 'by_base_class'

    def __init__(self,g_pool):
        self._alive = True
        self.g_pool = g_pool
        self.order = .5
        # between 0 and 1 this indicated where in the plugin excecution order you plugin lives:
        # <.5  are things that add/mofify information that will be used by other plugins and rely on untouched data.
        # You should not edit frame if you are here!
        # == .5 is the default.
        # >.5 are things that depend on other plugins work like display , saving and streaming

    def init_gui(self):
        '''
        if the app allows a gui, you may initalize your part of it here.
        '''
        pass


    @property
    def alive(self):
        """
        This field indicates of the instance should be detroyed
        Writing False to this will schedule the instance for deletion
        """
        if not self._alive:
            if hasattr(self,"cleanup"):
                self.cleanup()
        return self._alive

    @alive.setter
    def alive(self, value):
        if isinstance(value,bool):
            self._alive = value

    def on_click(self,pos,button,action):
        """
        gets called when the user clicks in the window screen
        """
        pass

    def on_window_resize(self,window,w,h):
        '''
        gets called when user resizes window.
        window is the glfw window handle of the resized window.
        '''
        pass

    def update(self,frame,events):
        """
        gets called once every frame
        if you plan to update data inplace, note that this will affect all plugins executed after you.
        Use self.order to deal with this appropriately
        """
        pass



    def gl_display(self):
        """
        gets called once every frame when its time to draw onto the gl canvas.
        """
        pass


    def cleanup(self):
        """
        gets called when the plugin get terminated.
        This happens either voluntarily or forced.
        if you have an gui or glfw window destroy it here.
        """
        pass



    def on_click(self,pos,button,action):
        """
        gets called when the user clicks in the window screen
        """
        pass

    @property
    def this_class(self):
        '''
        this instance's class
        '''
        return self.__class__


    @property
    def class_name(self):
        '''
        name of this instance's class
        '''
        return self.__class__.__name__

    @property
    def base_class(self):
        '''
        rightmost base class of this instance's class
        this way you can inherit from muliple classes and use the rightmost as your plugin group classifier
        '''
        return self.__class__.__bases__[-1]

    @property
    def base_class_name(self):
        '''
        base class name of this instance's class
        '''
        return self.base_class.__name__

    @property
    def pretty_class_name(self):
        return self.class_name.replace('_',' ')


    ### if you want a session persistent plugin implement this function:
    # def get_init_dict(self):
    #     d = {}
    #     # add all aguments of your plugin init fn with paramter names as name field
    #     # do not include g_pool here.
    #     return d

    def __del__(self):
        pass
        # print 'Goodbye',self

# Derived base classes:
# If you inherit from these your plugin property base_class will point to them
# This is good because we can categorize plugins.
class Calibration_Plugin(Plugin):
    '''base class for all calibration routines'''
    uniqueness = 'by_base_class'


class Gaze_Mapping_Plugin(Plugin):
    '''base class for all calibration routines'''
    uniqueness = 'by_base_class'
    def __init__(self,g_pool):
        super(Gaze_Mapping_Plugin, self).__init__(g_pool)
        self.order = 0.1



class Plugin_List(object):
    """This is the Plugin Manager
        It is a self sorting list with a few functions to manage adding and removing Plugins and lacking most other list methods.
    """
    def __init__(self,g_pool,plugin_by_name,plugin_initializers):
        self._plugins = []
        self.g_pool = g_pool

        for initializer in plugin_initializers:
            name, args = initializer
            logger.debug("Loading plugin: %s with settings %s"%(name, args))
            try:
                self.add(plugin_by_name[name],args)
            except (AttributeError,TypeError,KeyError) as e:
                logger.warning("Plugin '%s' failed to load from settings file. Because of Error:%s" %(name,e))

    def __iter__(self):
        for p in self._plugins:
            yield p

    def __str__(self):
        return 'Plugin List: %s'%self._plugins

    def add(self,new_plugin,args={}):
        '''
        add a plugin instance to the list.
        '''
        if new_plugin.uniqueness == 'by_base_class':
            for p in self._plugins:
                if p.base_class == new_plugin.__bases__[-1]:
                    logger.debug("Plugin %s of base class %s will be replaced by %s."%(p,p.base_class_name,new_plugin.__name__))
                    p.alive = False
                    self.clean()

        elif new_plugin.uniqueness == 'by_class':
            for p in self._plugins:
                if p.this_class == new_plugin:
                    logger.warning("Plugin '%s' is already loaded . Did not add it."%new_plugin.__name__)
                    return

        plugin_instance = new_plugin(self.g_pool,**args)
        self._plugins.append(plugin_instance)
        self._plugins.sort(key=lambda p: p.order)
        if self.g_pool.app in ("capture","player") and plugin_instance.alive: #make sure the plugin does not want to be gone already
            plugin_instance.init_gui()
            logger.info("Loaded: %s"%new_plugin.__name__)
        self.clean()


    def clean(self):
        '''
        plugins may flag themselves as dead or are flagged as dead. We need to remove them.
        '''
        for p in self._plugins[:]:
            if not p.alive: # reading p.alive will trigger the plug-in cleanup fn.
                logger.debug("Unloaded Plugin: %s"%p)
                self._plugins.remove(p)

    def get_initializers(self):
        initializers = []
        for p in self._plugins:
            try:
                p_initializer = p.class_name,p.get_init_dict()
                initializers.append(p_initializer)
            except AttributeError:
                #not all plugins want to be savable, they will not have the init dict.
                # any object without a get_init_dict method will throw this exception.
                pass
        return initializers



def import_runtime_plugins(plugin_dir):
    runtime_plugins = []
    if os.path.isdir(plugin_dir):
        sys.path.append(plugin_dir)
        for d in os.listdir(plugin_dir):
            logger.debug('Scanning: %s'%d)
            try:
                d =  d.rsplit(".", 1 )[ 0 ]
                module = importlib.import_module(d)
                logger.debug('Imported: %s'%module)
                for name in dir(module):
                    member = getattr(module, name)
                    if isinstance(member, type) and issubclass(member, Plugin) and member.__name__ != 'Plugin':
                        logger.info('Added: %s'%member)
                        runtime_plugins.append(member)
            except:
                pass
    return runtime_plugins
