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
import mpc.tessa
from mpc.tessa import store, contexts
#import ftrack

_log = _logging.getLogger()
from save.context import _AbstractJobContext



class Asset(context._AbstractJobContext):
    """ An Asset

    A named entity whose versions are managed by Tessa. Methods are supplied for searching
    the versions on an asset.
    """
    def __init__(self, context, assetType, name, stream=None, delayLoad=False):
        super(Asset, self).__init__()
        # Properties of an asset
        self.__name = name
        self.__context = context

        self.__stream = streams.Stream(stream)

        self.__assetType = assetType # class name as string
        self.__assetTypeGroup = None

        if not delayLoad:
            self.__loadAssetGroup()

    def __repr__(self):
        """ Representation of the object
        """
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.context, self.assetType, self.name, self.stream)

    @property
    def context(self):
        """ The context of the asset
        """
        return self.__context

    @property
    def assetType(self):
        """ The type of the asset (str)
        """
        return self.__assetType

    @property
    def assetTypeGroup(self):
        """ The group type of the asset (str)
        """
        # Ensure the asset type object is loaded
        self.__loadAssetGroup()
        return self.__assetTypeGroup

    @property
    def name(self):
        """ The name of the asset
        """
        return self.__name

    @property
    def stream(self):
        """ The stream of the asset
        """
        return self.__stream

    def __eq__(self, obj):
        """ Test equality of Asset objects
        """
        return isinstance(obj, Asset) \
        and self.context == obj.context \
        and self.assetType == obj.assetType \
        and self.name == obj.name \
        and self.stream == obj.stream

    def __ne__(self, rhs):
        """ Test inequality of Asset object
        """
        return not self == rhs

    def __cmp__(self, other):
        """ Compare two asset objects

            Args:
                other (store.Asset): The asset object to compare this asset object with

            Returns:
                int.  -1 if this object is earlier than the other
                        0 if they are the same
                        1 if this object is later than the other
        """
        return cmp(_makeComparisonTuple(self), _makeComparisonTuple(other))

    def findVersions(self, allowMissing=False, _filterMissingTypeGroups=None):
        """ Find the versions available for a particular asset

            Args:
                allowMissing (bool): allow retrieval of asset versions with unknown asset definitions

                _filterMissingTypeGroups (str, list): limit the search for missing asset
                type groups, eg 'releases'.
                    * This will be deprecated when all asset definitions are in Tessa*

            Yields:
                Matching :class:`Version<mpc.tessa.store.Version>` objects
        """
        return _findVersions(self, allowMissing=allowMissing,
                    useConsistentData=False,
                    _filterMissingTypeGroups=_filterMissingTypeGroups)

    def gather(self, version, destination=None, delayLoad=False):
        """ Return a gathered asset version; do not use consistent data here.
        """
        return _gather(self, version, destination, delayLoad, useConsistentData=False)

    def __loadAssetGroup(self):
        """ Load the assetTypeGroup (str) from the assetType (resolved by the definition manager)
        """
        if self.__assetTypeGroup is None:
            try:
                # Coerce the assetType into an object
                assetTypeObj = definitions.getDefinitionObject(self.__context, self.__assetType)

                # Check asset type is compatible with our context
                definitions.checkAssetTypeForContext(assetTypeObj, self.__context)

            except exceptions.AssetTypeNotFound:
                # Instantiate the missing asset types with the minimal definition 'MissingAssetType'
                assetTypeObj = _MissingAssetType
                _log.warn("Could not find asset definition for child of asset type %r.", self.__assetType)

            self.__assetTypeGroup = assetTypeObj.assetTypeGroup

    

class SaveContext(context._AbstractJobContext):
    
    data = {'disciplines': ['anim',
                            'fx',
                            'groom',
                            'layout',
                            'lighting',
                            'matchmove',
                            'model',
                            'rig',
                            'shading',
                            'techAnim',
                            'texture']}

    def __init__(self):
        self.shot = Shot()
        
    def fromEnvironment(self):
        pass

