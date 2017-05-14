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




from xml.dom import minidom
from time import ctime
import codecs
import os
import threading

import Graphyne.Graph as Graph
from ... import Fileutils
from ... import Engine
from ... import Angela


class NoProcConfigError(ValueError):
    pass


class LogLevel(Engine.LogLevel):
    pass
 
logLevel = LogLevel() 
    
    
    
class Plugin(Angela.Plugin):
    ''' The Angela logging class.  Intended to run 1x per process.  '''
    className = 'Plugin'
    
    def initialize(self, dtParams = None, rtParams = None):
        xmlData = rtParams['configXMLData']
        codepage = rtParams['configCodepage']     
        processName = rtParams['processName']
        
        try:
            self.observedLogQueue = rtParams['logQ']
        except:
            self.observedLogQueue = None
        
        fileXML = minidom.parseString(xmlData.encode( codepage ))
        
        self._stopevent = threading.Event()
        self._sleepperiod = 5.0
        threading.Thread.__init__(self, name="Logger")

        loggingElement = fileXML.getElementsByTagName("Logger")
        try:
            loggerFound = False
            for loggerElement in loggingElement:
                if loggerElement.getAttribute("process") == processName:
                    loggerFound = True
                    break
                #loggingElement = fileXML.getElementsByTagName("LogLocation")
            if loggerFound is False:
                raise NoProcConfigError
        except NoProcConfigError:
            print('Failed to find process %s in log configuration.  Can not start process without logger and can not start logger.  ')
            print('Please check the logger configuration and ensure that the logger is initialized with a process name found in the process attribute of a logger element.')
            print('terminating process')
            raise SystemExit
        except:
            pass
                
        
        logDir = os.path.join(os.environ['ANGELA_HOME'], "Logs")
        logFile = os.path.join(logDir, "%s.log" % processName)
        lLevel = 0
        header = ''
        overwrite = True
        codePage = 'ascii'
                    
        try:
            for ll in loggerElement.getElementsByTagName("LogLevel"):
                if ll.firstChild.data == 'Error': lLevel = 0
                elif ll.firstChild.data == 'Warning': lLevel = 1
                elif ll.firstChild.data == 'Admin': lLevel = 2
                elif ll.firstChild.data == 'Info': lLevel = 3
                elif ll.firstChild.data == 'Debug': lLevel = 4
                else: lLevel = 3
                
            for hd in loggerElement.getElementsByTagName("Header"):
                header = hd.firstChild.data
            for oa in loggerElement.getElementsByTagName("OverwriteOrAppend"):
                oaString = oa.firstChild.data
                if oaString == 'Append':
                    overwrite = False
            for cp in loggerElement.getElementsByTagName("CodePage"):
                codePage = cp.firstChild.data                
                    
        except:
            print('Failed to read the loggingAttributes dictionary.')             
            
        lLevel = restrictLogLevel(lLevel)
        self.standardLogLevels = LogLevel()
        self.lLevel = lLevel
        self.logFile = logFile
        self.codePage = codePage
        header = header + '\n'
        overwriteAppend = 'w'
        if overwrite == False: 
            overwriteAppend = 'a'
            header = '\n\n\n' + header

        Fileutils.ensureDirectory(logDir)
        fileName = codecs.open( self.logFile, overwriteAppend, self.codePage )
        #file = open(self.logFile, overwriteAppend)
        if header != None :
            fileName.writelines(header)
        fileName.writelines('%s Initialization \n' % ctime() )
        fileName.close

        
        
    def run(self):
        while not self._stopevent.isSet():
            try:
                if self.observedLogQueue is None:
                    toBeLogged = Engine.logQ.get_nowait()
                else:
                    toBeLogged = self.observedLogQueue.get_nowait()
                #toBeLogged = [contentType : logLevel : method : message]
                
                method = toBeLogged[2]
                statement = toBeLogged[3]
                errorLevel = toBeLogged[1]
                logLevelStr = ''
                if errorLevel == logLevel.ERROR: logLevelStr = ' ERROR: '
                elif errorLevel == logLevel.WARNING: logLevelStr = ' WARNING: '
                elif errorLevel == logLevel.ADMIN: logLevelStr = ' ADMIN: '
                elif errorLevel == logLevel.INFO: logLevelStr = ' INFO: '
                elif errorLevel == logLevel.DEBUG: logLevelStr = ' DEBUG: '
                
                if restrictLogLevel(errorLevel) <= self.lLevel:
                    fileName = codecs.open( self.logFile, "a", self.codePage )
                    #file = open(self.logFile,"a")
                    fileName.writelines('%s: %s %s - %s \n' % (ctime(), logLevelStr, method, statement) )
                    fileName.close
                    
                    # There is a risk of the loglevel affecting the content of the operations
                    # When characters with a non-latin codepage are printed non-latin codepage
                    try:
                        if (errorLevel == logLevel.ERROR) or (errorLevel == logLevel.WARNING) or (errorLevel == logLevel.ADMIN):
                            print(('%s: %s - %s' % (ctime(), method, statement)))
                    except:
                        print(('%s: %s - *** message contains character coding that can not \n               be rendered in the console. Please check your logfile***' % (ctime(), method))) 
                        print(('               Please check your logfile' % (ctime(), method)))
                
            except:
                self._stopevent.wait(self._sleepperiod)
        try:
            fileName = codecs.open( self.logFile, "a", self.codePage )
            fileName.writelines('%s:  %s' % (ctime(), "ADMIN:  Engine has ordered all archive threads to be terminated.  Logger Signing Off.") )
            fileName.close
        except: 
            pass
        print(("%s ends" % (self.getName(),)))
        
        

    def join(self, timeout = 10):
        """
        Stop the thread
        """
        self._stopevent.set()
        threading.Thread.join(self, timeout)



#Globals
moduleName = 'Logger'   
            

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