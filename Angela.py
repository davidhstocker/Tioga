#!/usr/bin/env python2
"""Angela RML Interpreter - Plugin Class
Created by the project angela team
    http://sourceforge.net/projects/projectangela/
    http://www.projectangela.org"""
    
__license__ = "GPL"
__version__ = "$Revision: 0.1 $"
__author__ = 'David Stocker'


# ***** BEGIN GPL LICENSE BLOCK *****
#
# Module copyright (C) David Stocker 
#
# This module is part of the Angela RML Engine.

# Angela is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Angela is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Angela.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

import threading
from types import ModuleType

import Graphyne.Graph as Graph
#import Engine



moduleName = 'Angela'
logType = Graph.logTypes.CONTENT
logLevel = Graph.LogLevel()


#classes


class ScriptFunction(ModuleType):

    def __init__(self, module):
        ModuleType.__init__(self, module.__name__)
        self._call = None
        if hasattr(module, '__call__'):
            self._call = module.__call__
        self.__dict__.update(module.__dict__)


    def __call__(self, *args, **keywargs):
        if self._call is not None:
            self._call(*args, **keywargs)
            
            

class ServicePlugin(threading.Thread):
    '''The generic Angela Plugin.  Usable for engine services, intit services and services.
    NOTE!  This extends threading.Thread, so run() and join() should also be implemented.
    override and implement execute() for specific behavior
    run() to run it.
    join() to close it'''

    def initialize(self, dtParams = None, rtParams = None):
        method = self.className + '.' + moduleName + '.' + 'initialize'
        
        
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , u"Design Time Parameters = %s" %(dtParams)])
        self.pluginName = rtParams['moduleName']
        try:
            name = dtParams['queue']
            self.queueName = name
        except:
            self.queueName = None
            errorMessage = "Possible Error: Plugin %s is unable acquire queue name from the configuration.  If it is supposed to have a queue, please check the configuration.  Otherwise Ignore!" %self.pluginName
            Graph.logQ.put( [logType , logLevel.ERROR , method , errorMessage])
        
        heatbeatTick = 5.0    
        try:
            heatbeatTick = float(dtParams['heatbeatTick'])
        except: pass
            
        self._stopevent = threading.Event()
        self._sleepperiod = heatbeatTick
        threading.Thread.__init__(self, name = rtParams['moduleName'])
        
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])



    def run(self):
        while not self._stopevent.isSet():
            try:
                self.execute()
                pass
            except:
                # loader plugins run as services sleep for the duration of heatbeatTick and retry the queue.
                self._stopevent.wait(self._sleepperiod)
        
    
    def join(self,timeout=None):
        """
        Stop the thread
        """
        self._stopevent.set()
        threading.Thread.join(self, timeout)
        
    def killServers(self):
        '''
            Implement this method if the plugin is spawning SimpleXMLRPCServer servers.
            If there is a server running, the thread won't be able to close when join is
            called and shutdown will hang.  These servers need to be stopped so that the
            thread can be closed and the interpreter server can be shut down
             
            It only needs to call server.server_close() and shut the server down.
        '''
        pass
        
    def execute(self):
        ''' method template of abstract class.  Override for specific behavior'''
        return True
    
    
class Plugin(ServicePlugin):
    '''The generic Angela Plugin.  Usable for engine services, intit services and services.
    NOTE!  This extends threading.Thread, so run() and join() should also be implemented.
    override and implement execute() for specific behavior
    join() to close it'''
    
    def run(self):
        while not self._stopevent.isSet():
            try:
                self.execute()
            except:
                # loader plugins run as services sleep for the duration of heatbeatTick and retry the queue.
                self._stopevent.wait(self._sleepperiod)


    
    
    
class NonThreadedPlugin(object):
    '''
        A non-threaded plugin
    '''
    
    def __init__(self, dtParams = None, rtParams = None):
        self.dtParams = dtParams
        self.rtParams = rtParams
    
        
    def execute(self, params = None):
        #override with desired behavior
        return None



class ActionRequest(object):
    """
        A class for creating action messages
    """    
    def __init__(self, actionMemeName, insertionType, rtparams, subjectID, objectID = None, controllerID = None):
        try:
            actionEntityID = Graph.api.createEntityFromMeme(actionMemeName)
            actionEntity = Graph.api.getEntity(actionEntityID)
            
            self.actionID = None
            self.action = None
            self.actionMeme = actionEntity.memePath
            self.insertionType = insertionType
            self.rtParams = rtparams
            self.subjectID = subjectID
            self.objectID= objectID
            self.controllerID= controllerID
            self.shutdownBlockID = None
        except Exception as e:
            raise e
            
        
class ActionInsertionType(object):
    APPEND = 0
    HEAD = 1
    HEAD_CLEAR = 2
    
    
    
class StimulusMessage(object):
    """ A class for messaging stimuli on the internal (SiQ) side.  This is the object type that is placed in the SiQ"""
    def __init__(self, stimulusID, argumentMap, targetAgents = []):
        self.stimulusID = stimulusID
        self.targetAgents = targetAgents
        self.argumentMap = argumentMap

    
    
class StimulusReport(object):
    """ A class for messaging stimuli on the external (broadcaster) side.  
        This is the object type that is placed in the various broadcaster queues
    """
    def __init__(self, stimulusID, stimulusMeme, agentSet, resolvedDescriptor, isDeferred = False, anchors = [], dependentConditions = None):
        self.stimulusID = stimulusID #The uuid of the stimulus
        self.stimulusMeme = stimulusMeme #Let's keep the cleartext ID of the meme
        self.agentSet = agentSet #The agents that are supposed to get this stimulus
        self.isDeferred = isDeferred #if filtering of the stimulus is deferred until rendering, this will be true 
        self.anchors = anchors #a list of anchor stimuli UUIDs that this stimulus is dependent on.  A free stimulus will have an empty list
        self.resolvedDescriptor = resolvedDescriptor  #This will be in the format created by the resolver  


    
    
def usage():
    print(__doc__)

    
def main():
    pass
    
