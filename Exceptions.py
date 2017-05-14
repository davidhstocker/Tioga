#!/usr/bin/env python2
"""Angela RML Interpreter - Exception Definitions
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




#classes

class ActionKeyframeExecutionError(ValueError):
    ''' A general error for failed action keyframes'''
    pass

class WorkerThreadIndexError(ValueError):
    ''' A worker thread for processing an action or stimulus is not indexed properly'''
    pass

class WorkerThreadTerminationRollback(ValueError):
    ''' A worker thread's termination is being rolled back'''
    pass

class EmptyFileError(ValueError):
    '''File contains no data  '''
    pass

class UndefinedValueListError(ValueError):
    pass

class DuplicateValueListError(ValueError):
    pass

class UndefinedOperatorError(ValueError):
    pass

class DuplicateConditionalError(ValueError):
    pass

class UndefinedUUIDError(ValueError):
    pass

class TemplatePathError(ValueError):
    pass

class MalformedArgumentPathError(ValueError):
    '''Parsing a conditional argument path via regular expressions yields a zero length array.  
        This means that the argument path does not follow the xPath style  '''
    pass

class MismatchedArgumentPathError(ValueError):
    '''Walking down an agent's attributes using th3e argumen path yields an error.
        This indicated that the agent does not have the desired arguent path available '''
    pass

class MissingArgumentError(ValueError):
    '''A conditional that requires argument X has been called without that argument  '''
    pass

class MissingAgentPathError(ValueError):
    '''A conditional that requires an agent with an attribute at path X has been called without that agent/attribute  combo'''
    pass

class MissingAgentError(ValueError):
    '''A conditional that requires a reference agent has been called without one'''
    pass

class MalformedConditionalError(ValueError):
    ''' A conditional is somehow malformed and can not be processed'''
    pass

class MissingTokenError(ValueError):
    ''' A conditional is somehow malformed and can not be processed'''
    pass

class UnknownConditionalError(ValueError):
    ''' Unknown conditional %s requested from catalog '''
    pass

class ChannelError(ValueError):
    ''' A stimulus is uses an undefined channeland can not be processed - or the channel is malformed'''
    pass

class DuplicateChannelError(ValueError):
    ''' The channel already exists'''
    pass

class DuplicateSubscription(ValueError):
    ''' already subscribed to the object '''
    pass

class DisallowedDescriptorType(ValueError):
    ''' Used for controllers that try  to subscribe to a descriptor that they can't handle, or are not allowed to have '''
    pass

class DisallowedChannelChange(ValueError):
    ''' The method is not allowed on this particuler channel type '''
    pass

class ControllerUpdateError(ValueError):
    ''' The controller is invalid'''
    pass

class InvalidControllerError(ValueError):
    ''' The controller is invalid'''
    pass

class DuplicateControllerError(ValueError):
    ''' The controller is invalid'''
    pass

class PassiveControllerActivationError(ValueError):
    ''' Strictly passive (mayBeActive == False) controllers may not be activated'''
    pass

class MismatchedStimulusDestination(ValueError):
    """A stimulus is given a set of controllers as the destination, but the stimulus has an agent oriented distribution model"""
    pass

class NullDisplacement(ValueError):
    """A displacement can't be determined; usually because the two locations are not in the same zone"""
    pass

class DurationModelError(ValueError):
    """A generic problem with a duration model"""
    pass

class ScriptError(ValueError):
    """A script error"""
    pass

class NoSuchZoneError(ValueError):
    """The entity repository is called using an invalid zone filter parameter"""
    pass

class NoSuchEntityError(ValueError):
    """The entity repository is called using an invalid entity uuid"""
    pass

class RegistrarModeError(ValueError):
    """
        Registrars (action and stimulus) need to be either in production mode, in where they use the default queues
        provided by the engine, or they need to have the inbound and outbound queues explicitly declared
    """
    pass

class RegistrarResponseError(ValueError):
    """
        The action engine is not getting the expected response from its registrar
    """
    pass

class RegistrarSyncError(ValueError):
    """
        The action engine and its registrar no longer agree on the current action being serviced
    """
    pass

class ActionIndexerInvalidTargetError(ValueError):
    """
        The action Indexer object needs a target to index over, looking for action singletons to index.  It can be a 
        Queue.Queue object, the Engines entity repository, or the action index of an already running registrar.
    """
    pass


class ActionIndexerError(ValueError):
    """ An undefined error indexing an action"""
    pass

class UnknownAction(ValueError):
    """ An unknown action was referenced"""
    pass


class EntityNotInLinkError(ValueError):
    """The link does not have the prescribed entity"""
    pass

class EntityLinkFailureError(ValueError):
    """The link could not be created"""
    pass

class EntityDuplicateLinkError(ValueError):
    """The link already exists"""
    pass


class SingletonEntityDuplicationError(ValueError):
    """ We expected to have a singleton and instead had a normal entity """
    pass

class NullBroadcasterIDError(ValueError):
    """ When we register a broadcaster, we expect it to have a non null ID """
    pass

class NoSuchBroadcasterError(ValueError):
    """ An engine service plugin is claiming a broadcaster ID that is not registered"""
    pass

class QueueError(ValueError):
    """ We have a problem with an engine comm queue"""
    pass

class InvalidStimulusProcessingType(ValueError):
    ''' The Stimulus Engine may only take the types TiogaSchema.ConditionalStimulus and 
        Stimulus.StimulusChoice.  Everything else throws an exception'''
    pass

class MemeMembershipValidationError(ValueError):
    """A meme has an invalid member"""
    pass

class EntityMaxXOffsetExceeded(ValueError):
    """ An offset element's 'x' is greater than the 'x' value of the agent's OffsetMax"""
    pass

class EntityMaxYOffsetExceeded(ValueError):
    """ An offset element's 'y' is greater than the 'y' value of the agent's OffsetMax"""
    pass

class EntityMaxZOffsetExceeded(ValueError):
    """ An offset element's 'z' is greater than the 'z' value of the agent's OffsetMax"""
    pass

class EntityMinXOffsetExceeded(ValueError):
    """ An offset element's 'x' is greater than the 'x' value of the agent's OffsetMin"""
    pass

class EntityMinYOffsetExceeded(ValueError):
    """ An offset element's 'y' is greater than the 'y' value of the agent's OffsetMin"""
    pass

class EntityMinZOffsetExceeded(ValueError):
    """ An offset element's 'z' is greater than the 'z' value of the agent's OffsetMin"""
    pass

class EntityMaxXAngleExceeded(ValueError):
    """ An offset element's 'x' is greater than the 'x' value of the agent's OffsetMax"""
    pass

class EntityMaxYAngleExceeded(ValueError):
    """ An offset element's 'y' is greater than the 'y' value of the agent's OffsetMax"""
    pass

class EntityMaxZAngleExceeded(ValueError):
    """ An offset element's 'z' is greater than the 'z' value of the agent's OffsetMax"""
    pass

class EntityMinXAngleExceeded(ValueError):
    """ An offset element's 'x' is greater than the 'x' value of the agent's OffsetMin"""
    pass

class EntityMinYAngleExceeded(ValueError):
    """ An offset element's 'y' is greater than the 'y' value of the agent's OffsetMin"""
    pass

class EntityMinZAngleExceeded(ValueError):
    """ An offset element's 'z' is greater than the 'z' value of the agent's OffsetMin"""
    pass
    
