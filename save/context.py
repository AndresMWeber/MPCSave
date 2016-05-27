#!/usr/bin/env python
"""
    :module: contextManager
    :platform: None
    :synopsis: This module contains classes related to module attributes
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0

#py import
import collections as _collections
import os

#mpc import
import mpc.logging as _logging
#import ftrack

_log = _logging.getLogger()


class Services(object):
    def findJobs(cls):
        pass


class _AbstractContext(object):
    """ Base context object.

        The base context presents a service provider throughout the project
    """

    # The type of child nodes from this object
    __childType__ = None

    # The levels of the context's hierarchy
    # This provides the possible levels to the hierarchy
    __levelHierarchy__ = ()

    # Sets the level that this particular object represents within the hierarchy
    # If set to None this object is not tied to a particular level
    __levelIndex__ = None

    ########################################
    # Implement class behaviour
    #
    def __init__(self, services=Services(), **contextDictIn):
        self.__services = services
        self.services = services
        super(_AbstractContext, self).__init__()

    @classmethod
    def fromDict(cls, contextDict):
        """ Alternative constructor, creating a new context object from a dict
            containing the keys of the context levels.

            For the facility (optional), job, scene and shot.
        """
        # Copy contextDict and build the keyword args
        kwargs = dict((key.encode('ascii'), val) for key, val in contextDict.items() if val is not None)
        return (cls)(**kwargs)

    def __iter__(self):
        """ Return an iterable set of tuples, suitable for use with dict.

            The is order is important and reflects the hierarchy of the context
        """
        levels = [ (level, getattr(self, '_' + level, None)) for level in self.__levelHierarchy__ ]

        return iter(levels)

    def __eq__(self, obj):
        """ Provides equality tests between facility objects
        """
        return isinstance(obj, type(self)) and tuple(self) == tuple(obj)

    def __ne__(self, obj):
        """ Provides inequality tests between facility objects
        """
        return not (self == obj)

    def __cmp__(self, other):
        """ Provides comparison between context objects
        """
        return cmp(tuple(self), tuple(other))

    def __repr__(self):
        """ Returns a string representation of the context object
        """
        keywords = []

        # Get an iterator to walk over our state backwards
        stateIter = reversed(list(self))

        # Wind over the initial 'None' values
        for level, value in stateIter:
            if value is not None:
                keywords = [ '%s=%r' % (level, str(value)) ]
                break

        # Continue by putting the results in the dict
        # Note, any 'None' values mixed up in the hierarchy get included
        keywords += ['%s=%r' % (level, str(value)) for level, value in stateIter]

        # Undo the reverse we did to begin with
        keywords.reverse()

        # Build the repr string
        return "%s(%s, services=%r)" % ( self.__class__.__name__, ", ".join(keywords), self.services )

    def __str__(self):
        """ The context's name
        """
        return self.name or ''

    def __hash__(self):
        return hash(tuple(self))

    # Properties
    #
    @property
    def services(self):
        """ Provides the services that are to be used in this context
        """
        return self.__services

    ########################################
    # Public interface
    #
    @property
    def name(self):
        """ The context's name
        """
        return getattr(self, '_' + self.__levelHierarchy__[self.__levelIndex__], None)

    def fullName(self):
        """ A fullname for ths object, to be presented in application interfaces.
        """
        # Override this if the desired fullName is different from the context class name
        labels = []
        for item in self:
            labels.append("%s: %s" % (item[0], item[1]))
        return ', '.join(labels)

    @classmethod
    def label(cls):
        """ Label for this context
        """
        return cls.__name__

    def findChildren(self,
                     withReleases=True,
                     assetTypeFilter=None,
                     assetGroupFilter=None,
                     jobTypeFilter=None,
                     jobFilter=None):
        """ Provides a list of the child contexts
        """
        raise NotImplementedError # pragma: no cover

    def hasChildren(self):
        """ Provide a cheap way to determine whether this node has children
        """
        return (self.__levelHierarchy__ is None
                or self.__levelIndex__ < len(self.__levelHierarchy__) - 1)


class _AbstractJobContext(_AbstractContext): # pylint: disable=C0103
    """ Base context object for job contexts
    """
    # comment please
    __levelHierarchy__ = ('facility', 'job', 'scene', 'shot')

    # Cache the facility short names
    _facilityShortNames = _collections.defaultdict(lambda: None)

    def __init__(self,
                 job=None,
                 scene=None,
                 shot=None,
                 services=None,
                 facility=None):
        super(_AbstractJobContext, self).__init__(services,
                                                  facility=facility,
                                                  job=job,
                                                  scene=scene,
                                                  shot=shot)

        # Store context on the instance
        self._job = job.name if type(job) == Job else job
        self._scene = scene.name if type(scene) == Scene else scene
        self._shot = shot.name if type(shot) == Shot else shot

        # A default facility is used from config if none is given
        if facility is None:
            facilityShortName = self.__class__._facilityShortNames[self.services]

            if facilityShortName is None:
                facilityShortName = self.services.context.getConfig("facility")['shortName']
                self.__class__._facilityShortNames[self.services] = facilityShortName

            self._facility = facilityShortName
        else:
            self._facility = facility.name if type(facility) == Facility else facility

        self._validateContextLevels()

    def _validateContextLevels(self):
        """ Validate all context levels, ensuring that appropriate ones are
            valid strings or None.
        """
        currentLevelIndex = self.__class__.__levelIndex__

        # We check each level in the level hierarchy. For levels up to and including the
        # current level, the name must not be None and must match the appropriate
        # regular expression from the regexConstants module. E.g. for a Scene context,
        # all of facility, job and scene must not be None and must be valid strings;
        # moreover shot *has* to be None.
        for levelIndex, levelName in enumerate(self.__class__.__levelHierarchy__):

            levelValue = getattr(self, "_%s" % levelName)

            if levelIndex <= currentLevelIndex:
                # This is the case of levels before and including self's level
                # All values should not be None and valid strings.
                if levelValue is None:
                    raise _exceptions.ContextException(
                        "In %r, value for %r should not be None for %r contexts" % (
                            tuple(self), levelName, self.__class__.__name__,
                        )
                    )
                self._validateContextLevel(levelName, levelValue)
            else:
                # This is the case of levels after self's level. All values
                # must be None
                if levelValue is not None:
                    raise _exceptions.ContextException(
                        "In %r, value %r must be None for %r contexts." % (
                            tuple(self), levelValue, self.__class__.__name__,
                        )
                    )

    def _validateContextLevel(self, levelName, levelValue):
        """ Validate the level string against the given level regex
        """
        assert levelName in self.__class__.__levelHierarchy__, "Unknown level name %r given" % (levelName,)

        levelRegexStr = _regexConstants.PATTERN_DICT["%s" % (levelName,)]

        levelRegex = _re.compile("^%s$" % (levelRegexStr,))
        if not levelRegex.match(levelValue):
            raise _exceptions.ContextException(
                "Context level %r with value %r does not match expected regex pattern %r for context %r." % (
                    levelName, levelValue, levelRegexStr, tuple(self)
                ),
            )

    def findChildren(self,
                     withReleases=True,
                     assetTypeFilter=None,
                     assetGroupFilter=None,
                     jobTypeFilter=None,
                     jobFilter=None):
        """ Provides a list of the child contexts
        """
        raise NotImplementedError # pragma: no cover

    def _findChildContextNames(self, assetTypeFilter=None, assetGroupFilter=None):
        """ Returns a set containing all of the child Contexts
        """
        childRecords = self.services.asset.findChildContexts(
                            _uri.fromContext(self),
                            assetGroupFilter,
                            assetTypeFilter,
                            True)

        contexts = (_uri.toContext(context, services=self.services) for context, _ in childRecords)
        return set(contexts)

    # Redefine the fromDict to give a more complete public docstring
    @classmethod
    def fromDict(cls, contextDict, services=None):
        """ Alternative constructor, creating a new context object from a dict
            containing the keys of the context levels.

            Possible context levels include:
                facility (optional), job, scene and shot.
        """
        return super(_AbstractJobContext, cls).fromDict(contextDict, services)

    @property
    def __defaultLevel(self): #pylint: disable=R0201
        """ The default value for an unused part of the JobContext hierarchy
        """
        return None

    facility = job = scene = shot = __defaultLevel


    
    
class Shot(_AbstractJobContext):
    __childType__ = Asset
    
    def __init__(self):
        self.facility = None
        self.job = None
        self.scene = None
        self.shot = None
    
    @property
    def facility(self):
        """ The facility associated with this context
        """
        return Facility(services=self.services, facility=self._facility)

    @property
    def job(self):
        """ The job associated with this context
        """
        return Job(job=self._job, facility=self._facility, services=self.services)

    @property
    def scene(self):
        """ The scene associated with this context
        """
        return Scene(job=self._job, scene=self._scene, facility=self._facility, services=self.services)

    @property
    def shot(self):
        """ The shot associated with this context
        """
        return self
    
    @classmethod
    def validate(cls):
        pass
        
    def findChildren(self, withReleases=False, assetTypeFilter=None, assetGroupFilter=None, jobTypeFilter=None,
                    jobFilter=None):
        """ Returns an empty list, as the are no children to a shot
        """
        return list()
        
    
        
        
class Scene(_AbstractJobContext):
    __childType__ = Shot
    __levelIndex__ = 2
    _nonSceneDirectories = _collections.defaultdict(lambda: None)
    
    @property
    def facility(self):
        """ The facility associated with this context
        """
        return Facility(services=self.services, facility=self._facility)

    @property
    def job(self):
        """ The job associated with this context
        """
        return Job(job=self._job, facility=self._facility, services=self.services)

    @property
    def scene(self):
        """ The scene associated with this context
        """
        return self
        
    @classmethod
    def validate(cls):
        pass
    
    def findChildren(self, withReleases=False, assetTypeFilter=None, assetGroupFilter=None, jobTypeFilter=None,
                    jobFilter=None):
        """ Returns a list of the shots for a scene

            Generally:

            *   withReleases=True will be used when performing 'gather' operations
            *   withReleases=False will be used when performing 'release' operations
        """
        ctxUri = _uri.fromContext(self)

        # The backend that needs to be queried to find the scenes is different depending on how
        # what's being requested.  We provide an interface to both through this mechanism since it
        # is very common within asset-based applications.
        if withReleases is True:
            names = self._findChildContextNames(
                assetTypeFilter=assetTypeFilter,
                assetGroupFilter=assetGroupFilter)

        else:
            namesOnDisc = self._findChildContextNames()
            names = set(namesOnDisc).union(
                _uri.toContext(ctx, services=self.services) for ctx in
                    set(self.services.context.findShots(ctxUri))
            )

        return sorted(set(name.shot for name in names if name.shot is not None), key=lambda x: x.name)

    findShots = findChildren


class Job(_AbstractJobContext):
    __childType__ = Scene
    __levelIndex__ = 1

    def __init__(self):
        self.facility = None
        self.job = None
        self.scene = None
        self.shot = None
    
    @property
    def facility(self):
        """ The facility associated with this context
        """
        return Facility(services=self.services, facility=self._facility)

    @property
    def job(self):
        """ The job associated with this context
        """
        return self
        
    @classmethod
    def validate(cls):
        pass
    
    def findChildren(self, withReleases=False, assetTypeFilter=None, assetGroupFilter=None, jobTypeFilter=None,
                    jobFilter=None):
        """ Returns a list of the scenes under a job.

            Generally:

            *   withReleases=True  will be used when performing 'gather'  operations
            *   withReleases=False will be used when performing 'release' operations
        """
        ctxUri = _uri.fromContext(self)

        # The backend that needs to be queried to find the scenes is different depending on how
        # what's being requested.  We provide an interface to both through this mechanism since it
        # is very common within asset-based applications.

        if withReleases is True:
            names = self._findChildContextNames(
                assetTypeFilter=assetTypeFilter,
                assetGroupFilter=assetGroupFilter)
        else:
            names = self._findChildContextNames()
            names = set(names).union(
                _uri.toContext(ctxUri, services=self.services)
                    for ctxUri in set(self.services.context.findScenes(ctxUri))
            )

        return sorted(set(name.scene for name in names if name.scene is not None), key=lambda x: x.name)

    findScenes = findChildren


class Facility(_AbstractJobContext):
    """ A Facility context object representing, for example, MPC.

        Note: The facility should not be confused with the geographical sites in which a
        facility might operate.
    """
    __childType__ = Job
    __levelIndex__ = 0

    def __init__(self, services=None, facility=None):
        super(Facility, self).__init__(services=services, facility=facility)

    @property
    def facility(self):
        """ The facility associated with this context
        """
        return self

    def findChildren(self, withReleases=False, assetTypeFilter=None,
                    assetGroupFilter=None, jobTypeFilter=None, jobFilter=None):
        """ Returns a list of the child contexts

            Generally:

            *   withReleases=True will be used when performing 'gather' operations
            *   withReleases=False will be used when performing 'release' operations
        """
        # The backend that needs to be queried to find the scenes is different depending on how
        # what's being requested.  We provide an interface to both through this mechanism since it
        # is very common within asset-based applications.
        ctxUri = _uri.fromContext(self)

        if withReleases is True:
            names = self.services.asset.findJobsWithReleases(jobTypeFilter, jobFilter)
        else:
            names = self.services.asset.findJobsWithReleases(jobTypeFilter, jobFilter)
            names = set(names).union(set(self.services.context.findJobs(ctxUri, True, jobTypeFilter, jobFilter)))


        res = set()
        for name in names:
            conUri = _uri.toContext(name, services=self.services)
            if conUri.job is not None:
                res.add(conUri.job)
        return sorted(res, key=lambda x: x.name)


    findJobs = findChildren


def contextFactory(contextIn, services=None):
    """ Returns a context object from the given input.

        Args:
            contextIn (dict|context object): If using a dict, it must be a 'context' dict

        Returns:
            context object
    """
    # We have been supplied a context, we can use this as it is
    if isinstance(contextIn, _AbstractJobContext):
        return contextIn

    # Easier to work with the context as a dict
    contextIn = dict(contextIn)

    if contextIn.get('shot') is not None:
        return Shot.fromDict(contextIn, services=services)
    elif contextIn.get('scene') is not None:
        return Scene.fromDict(contextIn, services=services)
    elif contextIn.get('job') is not None and contextIn.get('job') != ".mpc":
        return Job.fromDict(contextIn, services=services)

    if contextIn.has_key("job"):
        contextIn.pop("job", None)

    return Facility.fromDict(contextIn, services=services)


def fromEnvironment(services=None):
    """ Provide a context object from the environment.

        Uses the environment variables: JOB, SCENE and SHOTNAME to create a new context
        object.

        Kwargs:
            services (mpc.pyCore.services.ServiceProvider): The services to use

        Returns:
            context object
    """

    jobEnv = _os.getenv('JOB') or None
    sceneEnv = _os.getenv('SCENE') or None if jobEnv is not None else None
    shotEnv = _os.getenv('SHOTNAME') or None if sceneEnv is not None else None

    # Need to ensure that all context levels are valid. If shot context, then we have
    # to have job and scene defined and valid.
    return contextFactory({'job':   jobEnv,
                           'scene': sceneEnv,
                           'shot':  shotEnv}, 
                           services=services)


def validateContext(context):
    """ Validates that a context object is valid

        Arguments:
            context: and instance of Facility, Job, Scene or Shot to be
                validated

        Returns:
            True if the context exists, False otherwise
    """
    if not isinstance(context, (Facility, Job, Scene, Shot)):
        raise ValueError('Invalid argument type: %r, context object expected' % (type(context),))

    contextUri = URIFactory.fromContext(context)


    services = context.service
    valid = Services.validateContext(contextUri)

    # Only cache valid contexts, since invalid ones can become valid at any time
    if valid:
        return _validContextsCache.setdefault(contextUri, valid)

    return valid


def URIFactory(object):
    self.order = {'contextTypes': ['job', 'scene', 'shot', 'asset']}
    
    @classmethod
    def parse_uri(cls, uri):
        pass
    
    @classmethod
    def build_uri(cls, context):
        pass
        
    @classmethod
    def fromContext(cls, context):
        pass
        
    @classmethod
    def toContext(cls, dict):
        pass
    
    @classmethod
    def fromDict(cls, dict):
        pass
    
    @classmethod
    def toDict(cls, context):
        pass
    
    @classmethod
    def fromAsset(cls, context):
        pass
    
    @classmethod
    def toAsset(cls, dict):
        pass