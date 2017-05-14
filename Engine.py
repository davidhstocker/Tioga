#!/usr/bin/env python2
"""Angela RML Interpreter - Core Server Module (abstract)
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
import time
import copy
import os
from os.path import expanduser
import sys

import Graphyne.Graph as Graph
from Tioga import Exceptions
from Graphyne import Fileutils
from Tioga import PluginFacade
from Tioga import API



class StartupState(object):
    def __init__(self):
        self.TEMPLATES_FINISHED_LOADING = 0
        self.ACTIONS_INDEXED = 1
        self.REGISTRAR_READY = 2
        self.AE_READY_TO_SERVE = 3
        
        

class LogLevel(object):
    ''' Java style class to designate constants. ERROR = 0, WARNING = 1, INFO = 2 and ALL = -1.  '''
    def __init__(self):
        self.ERROR = 0
        self.WARNING = 1
        self.ADMIN = 2
        self.INFO = 3
        self.DEBUG = 4 
        
        
class LogType(object):
    ''' Java style class to designate constants. ERROR = 0, WARNING = 1, INFO = 2 and ALL = -1.  '''
    def __init__(self):
        self.ENGINE = 0
        self.CONTENT = 1
        
        
class Queues(object):
        
    def syndicate(self, streamData):
        #syndicate all data to the load queues
        for loadQKey in self.__dict__.keys(): 
            try:
                loadQ = self.__getattribute__(loadQKey)
                loadQ.put(streamData)
            except:
                pass       
            
             

api = None
moduleName = 'Engine'
serverLanguage = 'en' 
rmlEngine = None  
logTypes =  LogType() 
logType = logTypes.ENGINE
logLevel = LogLevel()
validateOnLoad = True
startupState = StartupState()
renderStageStimuli = []

import queue

queues = Queues()
templateQueues = []
#LogQ is always there and a module attribute
securityLogQ = queue.Queue()
lagLogQ = queue.Queue()

#Startup State Queues
startupStateActionEngineFinished = False



class LinkType(object):
    ATOMIC = 0
    SUBATOMIC = 1
    ALIAS = 2    



class ControllerCatalog(object):
    className = "ControllerCatalog"
    
    def __init__(self):
        self.indexByType = {}
        self.indexByID = {}
        
    def addController(self, controller):
        #method = moduleName + '.' +  self.className + '.addController'
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "entering"])
        #try:
        if controller.uuid not in self.indexByID:
            # We'll need to update both the typelist and the indexByID list
            typeList = []
            try:
                typeList = self.indexByType[controller.path.fullTemplatePath]
            except:
                #This will always happen the first time we instantiate a controller of a given type
                pass
            if controller.uuid not in typeList:
                typeList.append(controller.uuid)
                self.indexByType[controller.path.fullTemplatePath] = typeList
            else:
                raise Exceptions.DuplicateControllerError ("Controller %s already in the controller catalog under the indexByType list" % controller.id)
            
            self.indexByID[controller.uuid] = controller
        else:
            #The controller already has an entry
            raise Exceptions.DuplicateControllerError ("Controller %s already in the controller catalog" % controller.id)
        #except Exception as e:
            #raise Exceptions.ControllerUpdateError(e)
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])
    
    
    def removeController(self, controllerID):
        #method = moduleName + '.' +  self.className + '.removeController'
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "entering"])
        try:
            if controllerID in self.indexByID:
                pass
                '''# We'll need to update both the typelist and the indexByID list
                typeList = self.indexByType[controller.templateName] 
                if controller.id in typeList:
                    del typeList[controller.id]
                    typeList.remove(controller.id)
                    self.indexByType[controller.templateName] = typeList
                else:
                    raise Exceptions.InvalidControllerError ("Controller %s in the controller catalog under the indexByID list, but not the indexByType list" % controller.id)
                del self.indexByID[controller.id]'''
            else:
                #The controller already has an entry
                raise Exceptions.InvalidControllerError ("Controller %s is not in the controller catalog" % controllerID)
        except Exception as e:
            raise Exceptions.ControllerUpdateError(e)
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])
    
    
    def getControllersByType(self, controllerType):
        method = moduleName + '.' +  self.className + '.getControllersByType'
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "entering"])
        returnList = []
        try:
            returnList = self.indexByType[controllerType]
        except Exception as e:
            errorMsg = "Failed to find any controllers of type %s.  Traceback = %s" % (controllerType, e)
            Graph.logQ.put( [logType , logLevel.WARNING , method , errorMsg])
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])
        return returnList   





class BroadcasterRegistrar(object):
    className = "BroadcasterRegistrar"
    
    broadcasterIndex = {}   
    metamemeIndex = {}
    memeIndex = {}
    stimulusIndex = {}
    registeredBroadcasters = [] 
    defaultBroadcasters = []     
    
    def indexDescriptorMetamemes(self, broadcasterID, metamemeIDs):
        for metamemeID in metamemeIDs:
            try:
                existingBroadcasterSet = self.metamemeIndex[metamemeID]
                existingBroadcasterSet.add(metamemeID)
                self.metamemeIndex[metamemeID] = existingBroadcasterSet
                
                #Make a recursive call to cover all extending metamemes as well
                metamemeChildren = api.getExtendingMetamemes(metamemeID)
                self.indexDescriptorMetamemes(broadcasterID, metamemeChildren)
            except KeyError:
                newBroadcasterSet = set([metamemeID])
                self.metamemeIndex[metamemeID] = newBroadcasterSet
            except Exception as e:
                raise e
                
    
    def indexDescriptorMemes(self, broadcasterID, memeIDs):
        for memeID in memeIDs:
            try:
                if memeID == "*":
                    self.stimulusIndex["*"] = broadcasterID
                else:
                    existingBroadcasterSet = self.memeIndex[memeID]
                    existingBroadcasterSet.add(broadcasterID)
                    self.memeIndex[memeID] = existingBroadcasterSet
            except KeyError:
                newBroadcasterSet = set([broadcasterID])
                self.memeIndex[memeID] = newBroadcasterSet
            except Exception as e:
                raise e
            

    def indexBroadcaster(self, broadcasterID):
        if broadcasterID is not None:
            try:
                broadcasterQueue = queue.Queue()
                self.broadcasterIndex[broadcasterID] = broadcasterQueue
            except Exception as e:
                raise e
        else:
            errorMsg = "Can't register broadcaster with value None"
            raise Exceptions.NullBroadcasterIDError(errorMsg)
        
    def registerBroadcaster(self, broadcasterID):
        try:
            queuePointer = self.broadcasterIndex[broadcasterID]  
            testQueue = queue.Queue()
            if type(queuePointer) != type(testQueue):
                errorMsg = "No queue defined for broadcaster %s" %broadcasterID
                raise Exceptions.QueueError(errorMsg)
            else:
                self.registeredBroadcasters.append(broadcasterID)
                return queuePointer
        except Exceptions.QueueError as qe:
            raise qe
        except KeyError:
            errorMsg = "No such broadcaster (%s) registered" %broadcasterID
            raise Exceptions.NoSuchBroadcasterError(errorMsg)
        except Exception as e:
            raise e
        
        
    def indexDescriptor(self, descriptorID):
        method = moduleName + '.' +  self.className + '.indexDescriptor'
        
        #There is only one descriptor and the list length is 1,so use descriptors[0] for the descriptor uuid
        try:
            descriptorMeme = api.getEntityMemeType(descriptorID)
            descriptorMetaMeme = api.getEntityMetaMemeType(descriptorID)
        except Exception as e:
            raise e           
        
        broadcasterList = set([])
        for memeKey in self.memeIndex:
            if memeKey == descriptorMeme:
                broadcasterListByMeme = self.memeIndex[memeKey]
                broadcasterList.update(broadcasterListByMeme)
        for metaMemeKey in self.metamemeIndex:
            if metaMemeKey == descriptorMetaMeme:
                broadcasterListByMetaMeme = self.metamemeIndex[metaMemeKey]
                broadcasterList.update(broadcasterListByMetaMeme)
        self.stimulusIndex[descriptorID] = broadcasterList
        Graph.logQ.put( [logType , logLevel.INFO , method , "Descriptor %s registered with broadcasters %s" %(descriptorMeme, broadcasterList)])
        
        
        
    def getBroadcastQueue(self, stimulusUUID):
        try:
            broadcasterIDList = self.stimulusIndex[stimulusUUID] 
            try:
                defaultBroadcasterID = self.stimulusIndex["*"] 
                defaultBroadcaster = self.broadcasterIndex[defaultBroadcasterID]
                queueList = [defaultBroadcaster]
            except:
                queueList = []
            try:
                for broadcasterID in broadcasterIDList:
                    if broadcasterID in self.registeredBroadcasters:
                        queue = self.broadcasterIndex[broadcasterID]
                        queueList.append(queue)
                    else:
                        errorMsg = "Broadcaster %s not registered.  Please check configuration XML" %broadcasterID
                        raise Exceptions.NoSuchBroadcasterError(broadcasterID)
            except KeyError:
                errorMsg = "No queue defined for broadcaster %s" %broadcasterID
                raise Exceptions.QueueError(errorMsg)
            except Exceptions.NoSuchBroadcasterError as e:
                raise Exceptions.NoSuchBroadcasterError(e)
            return queueList
        except KeyError:
            keyList = list(self.stimulusIndex.keys())
            memeIDList = []
            badMemeID = None
            try:
                badMemeID = api.getEntityMemeType(stimulusUUID)
                for keyID in keyList:
                    memeID = api.getEntityMemeType(keyID)
                    memeIDList.append(memeID)
            except: pass
            errorMsg = "Descriptor %s No among registered descriptors in broadcast registrar.   Registered Descriptors = %s" %(badMemeID, memeIDList)
            raise Exceptions.NullBroadcasterIDError(errorMsg)
        except Exceptions.NoSuchBroadcasterError as e:
            raise Exceptions.NoSuchBroadcasterError(e)
        except Exceptions.QueueError as e:
            raise Exceptions.QueueError(e)    
    


#Globals



class Engine(object):
    className = "Engine"
    ''' The generic Engine core class. '''
    
    def __init__(self, processName = 'tioga'):
        global logLevel   
        self.rtParams = {}     
        self.engineQueues = {'pyLoader' : False, 'mmLoadQ' : True, 'mLoadQ' : True, 'restLoadQ' : True}
        self.scriptLanguages = {"Python" : ['PythonScriptHandler', 'PythonScriptValidator']}
        self.consoleLogLevel = logLevel.WARNING
        self.persistenceArg = None
        self.persistenceType = None
        self.additionalRepos = []
        self.processName= processName
        self.noMainRepo = False
        self.broadcasters = {'default' : {'memes' : ['*'], 'metaMemes' : ['*']}}
        
        self.scriptDefinitions = {"getAllAgentsInAgentScope" : ["Agent", "getAllAgentsInAgentScope"],
                            "getAllLandmarksInAgentScope" : ["Agent", "getAllLandmarksInAgentScope"],
                            "getAllAgentsInAgentView" : ["Agent", "getAllAgentsInAgentView"],
                            "getAllLandmarksInAgentView" : ["Agent", "getAllLandmarksInAgentView"],
                            "getAllAgentsWithAgentView" : ["Agent", "getAllAgentsWithAgentView"],
                            "getAllLandmarksWithAgentView" : ["Agent", "getAllLandmarksWithAgentView"],
                            "getAllAgentsInSpecifiedPage" : ["Agent", "getAllAgentsInSpecifiedPage"],
                            "getAllAgentsWithViewOfSpecifiedPage" : ["Agent", "getAllAgentsWithViewOfSpecifiedPage"],
                            "getAgentView" : ["Agent", "getAgentView"],
                            "getAgentsWithViewOfStimulusScope" : ["Agent", "getAgentsWithViewOfStimulusScope"],
                            "getStimulusScope" : ["Agent", "getStimulusScope"],
                            "getAgentScope" : ["Agent", "getAgentScope"]}
        
        self.plugins = {
                        'ActionEngine' : {'name' : 'ActionEngine',
                            'pluginType' : 'EngineService',
                            'Module' : 'ActionEngine.ActionEngine',
                            'PluginParemeters': {'heatbeatTick' : 1}
                            },
                        'StimulusEngine' : {'name' : 'StimulusEngine',
                            'pluginType' : 'EngineService',
                            'Module' : 'StimulusEngine.StimulusEngine',
                            'PluginParemeters': {'heatbeatTick' : 1}
                            }
                        }




    def addBroadcaster(self, newDefID, newDef):
        pass
        #test that memes and metamemes are in and structured correcty
        
    def removeBroadcaster(self, defID):
        pass
    
    def setScriptDefinition(self, newDefID, newDef):
        pass
    
    def setPersistence(self, persistenceArg, persistenceType):
        self.persistenceArg = persistenceArg
        self.persistenceType = persistenceType
        
    def addRepo(self, repo):
        self.additionalRepos.append(repo)
        
    def addPlugin(self, newDefID, newDef):
        pass
    
    def removePlugin(self, defID):
        pass
    
    def setRuntimeParam(self, paramID, paramValue):
        self.rtParams[paramID] = paramValue
        
    
    def start(self, startWithTestRepo = False):
        '''
            processName = process attribute value from Logging.Logger in AngelaMasterConfiguration.xml.
                The process name must be one of the ones defined in the configuration file
            manualAutoVal = an optional boolean (True or False) overriding the validateOnLoad setting in 
                AngelaMasterConfiguration.xml.  If this is not given, or is not boolean, the engine will
                use the setting defined in the configuration file
        '''
        
        method = moduleName + '.' +  self.className + '.start'
        global queues
        global logQ
        global validateOnLoad

        #server language
        try:
            global serverLanguage
            serverLanguage = self.serverLanguage
        except: pass
        
        #validate on load
        try:        
            global validateOnLoad    
            validateOnLoad = self.validateOnLoad
        except: pass

        for queueName in self.engineQueues.keys():
            loadQueue = self.engineQueues[queueName]
            Graph.logQ.put( [logType , logLevel.ADMIN , method , "Creating queue %s, template loader = %s" %(queueName, loadQueue)])
            newQueue = queue.Queue()
            #queues[queueName] = newQueue
            queues.__setattr__(queueName, newQueue)
            if loadQueue == True:
                templateQueues.append(queueName)
        print(("queues = %s" %self.engineQueues.keys()))
        
        #Get All Repositories
        objectMap = {}
        for repoLocation in self.additionalRepos:
            sys.path.append(repoLocation)
            objectMap = Fileutils.walkRepository(repoLocation, objectMap)
        
            
        if startWithTestRepo is True:
            try:
                childDirectory = os.path.dirname(Exceptions.__file__)
                parentDirectory = os.path.split(childDirectory)
                objectMap = Fileutils.walkRepository(parentDirectory[0], objectMap)
            except Exception as e:
                errorMessage = "Error: startWithTestRepo is set to true, but default package (Memetic) can't be bootstrapped.  Please install it and ensure that it is in the PYTHONPATH.  Traceback = %s" %e
                print(errorMessage)
                raise Exceptions.TemplatePathError(errorMessage)
        
        Graph.logQ.put( [logType , logLevel.INFO , method , "Python Path %s" %(sys.path)])
        
        for repoDir in self.additionalRepos:
            Graph.logQ.put( [logType , logLevel.INFO , method , "Memetic Repository at %s" %(repoDir)])
        
        #syndicate all data to the load queues
        for packagePath in objectMap.keys():
            try:
                Graph.logQ.put( [logType , logLevel.INFO , method , "Memetic Repository Module %s" %(packagePath)])
                print(("module = %s" %(packagePath)))
                fileData = objectMap[packagePath]
                for fileStream in fileData.keys():
                    codepage = fileData[fileStream]
                    streamData = [fileStream, codepage, packagePath]
                    queues.syndicate(streamData)
            except Exception as e:
                Graph.logQ.put( [logType , logLevel.ERROR , method , "problem syndicating file in repository %s.  Traceback = %s" %(packagePath, e)])
 

            
        #Before starting any plugins, initialize the broadcaster registrar
        #queues
        for broadcasterID in self.broadcasters.keys():
            broadcasterDeclaration = self.broadcasters[broadcasterID]
            broadcasterRegistrar.indexBroadcaster(broadcasterID)
            memeIDs = []
            metamemeIDs = []           
            try:
                memeIDs = broadcasterDeclaration['memes']
            except KeyError: pass
            except Exception as e:
                raise e
            
            try:
                metamemeIDs = broadcasterDeclaration['metaMemes']
            except KeyError: pass
            except Exception as e:
                raise e
            
            try:
                broadcasterRegistrar.indexDescriptorMemes(broadcasterID, memeIDs)
                broadcasterRegistrar.indexDescriptorMetamemes(broadcasterID, metamemeIDs)
            except Exceptions.NullBroadcasterIDError as e:
                Graph.logQ.put( [logType , logLevel.ERROR , method , "Can't index broadcaster %s.  Traceback = %s" %(broadcasterID, e)])
            except Exception as e:
                Graph.logQ.put( [logType , logLevel.ERROR , method , "Problem indexing broadcaster %s and descriptor ownership %s.  Traceback = %s" %(broadcasterID, memeIDs, e)])



        # Monkey Patching Alert!  We will decorate the Graphyne.Graph.Scriptacade class with additional script commands before initializing it
        #MasterScriptFunctions
        # /Monkey Patching.  We can now start the Graph.  :)
        
        
        #By default, the engine runs at log level warning, but the wrapper that calls Engine may supply a 'consoleLogLevel' paremeter
        lLevel = logLevel.WARNING
        try:
            lLevel = self.consoleLogLevel
        except: pass

        #Memetic Repositories
        # Tioga needs its standard repo.  That's hardcoded in
        # There is a default location for repository info: /usr/Tioga/Repository
        # The user can also define other locations
        # If the user gives a repo location for the main Memetic (technical) Repository

        #Main Repo
        if self.noMainRepo is False: 
            userRoot =  expanduser("~")
            mainRepo = os.path.join(userRoot, "Tioga", "MemeticRepository")
            Fileutils.ensureDirectory(mainRepo)
            self.additionalRepos.append(mainRepo)
         
        #Depricated, as the Tioga repo has been moved out of this package   
        #Standard Tioga Schema
        #myLocation = os.path.dirname(os.path.abspath(__file__))
        #tiogaRepo = os.path.join(myLocation, "TiogaRepository")
        #self.additionalRepos.append(tiogaRepo)
                            
        Graph.startLogger(lLevel, "utf-8", True, self.persistenceType)
        Graph.startDB(self.additionalRepos, self.persistenceType, self.persistenceArg, True)
        
        global api
        api = Graph.api.getAPI()
        #/Start Graphyne
                
        #Initialize Other Plugins
        PluginFacade.initPlugins(self.plugins)
                
        #Yeah baby!  Start dem services!
        #rtParams[u"responseQueue"]
        self.rtParams['processName'] = self.processName
        self.rtParams['engineService'] = True
        self.archiveServices = []
        self.services = []
        self.threadNames = []

        while Graph.readyToServe == False:
            time.sleep(5.0)   
            Graph.logQ.put( [logType , logLevel.DEBUG , method, "...Angela Engine waiting for initial loading of templates and entities to finish"])
        Graph.logQ.put( [logType , logLevel.ADMIN , method, "Templates and Entities are ready.  Angela Engine ready to start action indexer"])
                     
        #now, we should make sure that all singleton memes are instantiated.
        Graph.logQ.put( [logType , logLevel.INFO , method ,"Loading Action and Stimulus Indexers"])

        actions = api.getEntitiesByMetaMemeType("Action.Action")
        for actionID in actions:
            actionIndexerQ.put(actionID)
            
        desriptors = api.getEntitiesByMetaMemeType("Stimulus.Descriptor")
        for desriptorID in desriptors:
            stimulusIndexerQ.put(desriptorID)
        Graph.logQ.put( [logType , logLevel.INFO , method ,"Finished initial loading of Action and Stimulus Indexers"])
        
        #Now we can start the service plugins
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "starting engine services"])
        print("starting engine services")
        for plugin in PluginFacade.engineServices:
            engineService = plugin['module']
            self.rtParams['moduleName'] = plugin['moduleName']
            dtParams = plugin['params']
            try:
                tmpClass = getattr(engineService, 'Plugin')
                service = tmpClass()
                apiCopy = copy.deepcopy(api)
                service.initialize(apiCopy, dtParams, self.rtParams)
                print(("starting = %s" %service.__class__))
                service.start()
                self.services.append(service)
                self.threadNames.append(service.getName())
                Graph.logQ.put( [logType , logLevel.ADMIN , method , "starting %s as thread ID %s" %(service.__class__, service.getName())])
            except Exception as e:
                print(("Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)))
                Graph.logQ.put( [logType , logLevel.ERROR , method , "Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)])
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "finished starting engine services"])
        print("finished starting engine services")
        
        #The modulename param, that we introduced in the loop above is obsolete, no longer relevant and we don't know what it contains
        del self.rtParams['moduleName']
        
        #init services!
        self.rtParams['engine'] = self
        self.rtParams['objectMap'] = objectMap
        self.rtParams['engineService'] = False
        self.initServices = []
        
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "starting init services"])
        print("starting init services")
        print((PluginFacade.initServices))
        for plugin in PluginFacade.initServices:
            engineService = plugin['module']
            self.rtParams['moduleName'] = plugin['moduleName']
            dtParams = plugin['params']
            #try:
            tmpClass = getattr(engineService, 'Plugin')
            service = tmpClass()
            service.initialize(dtParams, self.rtParams)
            Graph.logQ.put( [logType , logLevel.ADMIN , method , "starting %s" %service.__class__])
            print(("starting = %s" %service.__class__))
            service.start()
            self.initServices.append(service)
            #except Exception as e:
                #print("Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)
                #Graph.logQ.put( [logType , logLevel.ERROR, method , "Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)])
        Graph.logQ.put( [logType , logLevel.ADMIN, method , "finished starting init services"])
        print("finished starting init services")

        Graph.logQ.put( [logType , logLevel.ADMIN , method , "starting initialization plugins"])        
        print("starting initialization plugins")
        for plugin in PluginFacade.initUtils:
            dtParams = plugin['params']
            util = plugin['module']
            try:
                tmpClass = getattr(util, 'Plugin')
                service = tmpClass()
                service.initialize(dtParams, self.rtParams)
                Graph.logQ.put( [logType , logLevel.ADMIN , method , "executing %s" %tmpClass.__class__])
                print(("executing = %s" %service.__class__))
                service.execute()
            except Exception as e:
                print(("Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)))
                Graph.logQ.put( [logType , logLevel.ERROR , method , "Failed to start Plugin %s.  Traceback = %s" %(str(engineService), e)])
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "finished executing initialization plugins"])
        print("finished executing initialization plugins")
        
        
        #Now signal to all of the init services that they should shut down when finished with their queues
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "shutting down initialization services"])
        print("shutting down initialization services")
        for initService in self.initServices:
            print(("stopping %s" %service.__class__))
            initService.join()
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "finished shuting down initialization services"])
        print("finished shuting down initialization services")
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "exiting"])
        
        
    def shutdown(self):
        method = moduleName + '.' +  self.className + '.shutdown'
        #Graph.logQ.put( [logType , logLevel.DEBUG , method , "entering"])
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "Engine Shutdown Started."])
        print("Finished waiting.  Shutting down service plugins.")
        for service in self.services:
            #print("stopping %s" %service.__class__
            try:
                service.killServers()
                service.join()
            except Exception as e:
                print(( 'Exception while waiting for service thread to shut down. Traceback = %s' %(e)))

        print("Shutdown Started.  Waiting sixty seconds to allow log and database queues to be cleared before shutting archive services down.")
        Graph.logQ.put( [logType , logLevel.ADMIN , method , "Engine Services shut down.  Waiting twenty seconds to allow log and database queues to be cleared before shutting archive services down."])
        time.sleep(60.0)
        
        try:
            if len(threading.enumerate()) > 0:
                self.shutdownWait()
        except Exception as e:
            print(( 'Exception while waiting for child threads to shut down. Traceback = %s' %(e)))
            
        Graph.stopLogger()            
        print("Finished shutting down service and archive plugins.  Shutting Down engine")

        
        
        
    def shutdownWait(self):
        """ 
            This method is a bit wonky,as it substitutes recursive calls for a while loop. 
            It is a hackish solution to fill the need to poll the the threads that are still up
        """
        main_thread = threading.currentThread()
        canStopNow = True
        for t in threading.enumerate():
            canStopNow = True
            threadName = t.getName()
            if t is main_thread:
                continue
            elif threadName in self.threadNames:
                canStopNow = False
                print(( 'Engine waiting for thread %s to finish shutting down' %threadName))   
        if canStopNow == False:
            time.sleep(6.0)    
            self.shutdownWait()
        


#Globals
controllerCatalog = None
scriptLanguages = {}
logQ = queue.Queue()
aQ = queue.Queue() # action queue
siQ = queue.Queue()
actionIndexerQ = queue.Queue()
stimulusIndexerQ = queue.Queue()
stagingQ = queue.Queue() 
logType = LogType()
logLevel = LogLevel()     
linkTypes = LinkType()  
broadcasterRegistrar = BroadcasterRegistrar()



def getUUIDAsString(uuidToParse):
    #ensure that the uuid given as a parameter is in unicode format
    try:
        testStr = 'x'
        testUnicode = 'x'

        if type(uuidToParse) == type(testStr):
            uuidAsString = str(uuidToParse)
            return uuidAsString
        elif type(uuidToParse) == type(testUnicode):
            #nothing to do
            return uuidToParse
        else:
            stringURN = uuidToParse.get_urn()
            partStringURN = stringURN.rpartition(":")
            uuidAsString = partStringURN[2]
            return uuidAsString
    except Exception as e:
        return "Traceback = %s" %e  


def filterListDuplicates(listToFilter):
    # Not order preserving
    keys = {}
    for e in listToFilter:
        keys[e] = 1
    return list(keys.keys())


def runscript(script):
    PluginFacade.utilities
                
