#!/usr/bin/env python2
"""Angela RML Interpreter - Core Logging Module
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
# This module is part of the Angela RML engine.

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
import queue

import Graphyne.Graph as Graph
from ... import Engine
from ... import Angela
from ... import Exceptions


class NoProcConfigError(ValueError):
    pass


class TestCaseResponseQueue(object):
    
    def __init__(self, responseQueue):
        self.responseQueue = responseQueue
        


class Plugin(Angela.Plugin):
    ''' A test broadcaster  '''
    className = 'Plugin'
    responseQueue = None
    myQueue = None
    broadcasterID = None
        
    def initialize(self, script, dtParams = None, rtParams = None):
        method = moduleName + '.' +  self.className + '.initialize'
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "entering"])
        
        try:
            self.broadcasterID = dtParams["broadcasterID"]
        
            try:
                self.myQueue = Engine.broadcasterRegistrar.registerBroadcaster(self.broadcasterID)
                
                #Store some type references for runtime checking of message types
                try:
                    #use a queue supplied tothe engine on startup
                    responseQ = rtParams["responseQueue"]
                    self.responseQueue = TestCaseResponseQueue(responseQ)
                except Exception as e:
                    errorMsg = "Unable to start broadcaster %s. No responseQueue runtime parameter supplied %s.  Traceback = %s" %(self.broadcasterID, e)
                    Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
                
                self._stopevent = threading.Event()
                self._sleepperiod = 0.03
                threading.Thread.__init__(self)
            except Exceptions.QueueError as qe:
                errorMsg = "Unable to acquire queue for broadcaster %s.  Traceback = %s" %(self.broadcasterID, qe)
                Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
            except Exceptions.NoSuchBroadcasterError as nsbe:
                errorMsg = "Unable to register broadcaster %s.  Traceback = %s" %(self.broadcasterID, nsbe)
                Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
            except Exception as e:
                errorMsg = "Unable to start broadcaster %s.  Traceback = %s" %(self.broadcasterID, e)
                Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
        
        except Exception as e:
            errorMsg = "RegressionTestBroadcaster is a broadcaster and requires a broadcasterID to me maintained.  Please edit that parameter in the plugin declaration.  Traceback = %s" %e
            Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])
         
        
        
    def run(self):
        """
            myQueue is a broadcast queue registered with the Engine's broadcast registrar.  Since we don't want
            the regression module (or any interactive dev/test harness) poking around in the broadcast queue,
            we'll forward the report to the externally available  
        """
        method = moduleName + '.' +  self.className + '.run'
        while not self._stopevent.isSet():
            try:
                if self.myQueue is None:
                    errorMsg = "%s has no queue to manage.  Shutting plugin down." %self.broadcasterID
                    Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
                    self.join()
                else:
                    #simply move the report from myQueue to the response queue
                    #note that responseQueue is a TescaseResponseQueue object, which in turn has a responseQueue attribute
                    toBeBroadcast = self.myQueue.get_nowait()
                    self.responseQueue.responseQueue.put(toBeBroadcast) 
            except queue.Empty:
                self._stopevent.wait(self._sleepperiod)
            except Exception as e:
                errorMsg = "Error encountered while trying to transfer stimulus report to response queue. Traceback = %e" %e
                Graph.logQ.put( [logType , logLevel.ERROR , method , errorMsg])
        dummyCatch = "this thread is being shut down"
        

    def join(self, timeout = 1.0):
        """
        Stop the thread
        """
        method = moduleName + '.' + self.className + '.' + 'join'
        #del self.myQueue
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "......Regression Test broadcaster shut down"])
        self._stopevent.set()
        threading.Thread.join(self, timeout)



#Globals
moduleName = 'RegressionTestBroadcaster' 
logType = Graph.logTypes.CONTENT
logLevel = Graph.LogLevel()  
            

def restrictLogLevel(level):
    llevel = level
    if level!=0 and level!=1 and level!=2 and level!=3 and level!=4:
        llevel = logLevel.ERROR
    return llevel



def usage():
    print(__doc__)

    
def main(argv):
    pass
    
    
if __name__ == "__main__":
    pass