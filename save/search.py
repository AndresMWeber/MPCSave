""" Searching the store
"""
from mpc.logging import getLogger as _getLogger

from mpc.tessa import exceptions, contexts
from mpc.tessa.utils.validators import NameDoesNotContainStreamValidator
from mpc.tessa import uri as _uri
from mpc.tessa._core.asset import asset as _asset, assetVersion as _assetVersion
from mpc.tessa._core.utils import hierarchyUtils as _hierarchyUtils
from mpc.tessa._core.utils import serialisationUtils
from mpc.tessa._core.utils import streamUtils as _streamUtils

_log = _getLogger()

def _validateAndFormatNames(assetName):
	""" the find functions require that the assetName be a list and be valid
	"""
	validator = NameDoesNotContainStreamValidator()
	# our asset name can be a string or a list, so we should convert to a list if we have a string
	if isinstance(assetName, basestring):
		assetName = [assetName]

	for name in assetName:
		validator(name)

	return assetName

def findAssets(context, assetType=None, name=None, stream=None, filterTypeGroups=None, recursive=False,
			allowMissing=False):
	""" Find assets in the store.

		Args:
			context: current context object

			assetType (str, list): limit the search to an asset type or list of types

			name (str, list): specifies the asset name, or list of names

			stream (str): The stream of the asset to search for

			filterTypeGroups (str, list): limit the search to asset type groups, eg 'releases'

			recursive (bool): determines if the search should include all child contexts of `context`.
				Default: True
				(Not available for Facility level contexts)

			allowMissing (bool): determines if asset types unknown to Tessa can be returned.
				Default: False


		Returns:
			generator of store.Asset instances
	"""

	if isinstance(context, contexts.Facility) and recursive:
		raise exceptions.TessaException("Recursive search is not available for Facility level contexts")

	filterTypeGroups = filterTypeGroups or ['releases', 'elements', 'dailies',]
	if stream and name is None:
		raise exceptions.TessaValueError("Sorry, search by just stream is currently not support, please provide a name")

	# If our asset name isn't None, validate it
	if name is not None:
		name = _validateAndFormatNames(name)

	# Get the list of assets from the service
	# The results from asset.findAssets is processed by hierarchyUtils.compressAssets() in order
	# to group each component efficiently
	results = _hierarchyUtils.expandAssets(
		context.services.asset.findAssets(
			_uri.fromContext(context),
			assetType,
			name,
			serialisationUtils.serialiseStream(stream),
			filterTypeGroups,
			recursive,
			allowMissing
		)
	)

	# Return Asset objects for each asset found
	for assetContext, _, assetType, assetName in results:
		try:
			resultName, resultStream = _streamUtils.splitAssetNameForStream(assetName)
			yield _asset.Asset(
				_uri.toContext(assetContext, services=context.services),
				assetType,
				resultName,
				stream=resultStream,
				delayLoad=allowMissing,
			)
		except Exception, exc:
			print str(exc)

def findVersionsOfAssets(context, assetType=None, name=None, stream=None, filterTypeGroups=None,
							recursive=False, filterAttributes=None,
							startDateTime=None, endDateTime=None, recent=None):
	""" Find assets in the store and a list of versions of those assets which
		adhere to additional attribute filters for those versions.

		Args:
			context: current context object

			assetType (str, list): limit the search to an asset type or list of types

			name (str, list): specifies the asset name

			stream (str): The stream of the asset to search for

			filterTypeGroups (str, list): limit the search to asset type groups; choices are 'elements', 'releases', 'dailies'

			recursive (bool): determines if the search should include all child contexts of `context`.
				Default: True

			filterAttributes (dict): return only versions with matching attributes.
				Ignored if no filterTypeGroup is specified

			startDateTime (datetime): limit search to start at specified date, time

			endDateTime (datetime): limit search to end at specified date, time

			recent (int): returns `recent` most asset versions, by release date

		Returns:
			generator of (Asset, (assetVersions,)) tuples

		Note: if the context is a facility context (i.e. across all jobs) then you need to also supply
		the recent argument. This prevents the query from, potentially, returning too much data and locking
		the database during the query.
	"""

	filterTypeGroups = filterTypeGroups or ['releases', 'elements', 'dailies',]

	if isinstance(context, (contexts.Facility, contexts.Job, contexts.Scene)) and recursive and not any((recent, assetType, name)):
		raise exceptions.TessaException("Recursive Facility/Job/Scene searches must be limited by 'recent', 'assetType' or 'name'")

	if stream and name is None:
		raise exceptions.TessaValueError("Sorry, search by just stream is currently not support, please provide a name")

	# Convert to list if necessary
	if isinstance(assetType, basestring):
		assetType = [assetType]

	# Convert to list if necessary
	if isinstance(name, basestring):
		name = [name]

	# If our asset name isn't None, validate it
	if name is not None:
		name = _validateAndFormatNames(name)

	# Get the list of assets from the service (via the asset version cache)
	for assetContext, assetType_, assetName_, stream_, assetVersions in _assetVersion.Cache.findVersionsOfAssets(
			context,
			assetType,
			name,
			stream,
			filterTypeGroups,
			filterAttributes,
			recursive,
			startDateTime,
			endDateTime,
			recent):
		yield (_asset.Asset(assetContext, assetType_, assetName_, stream=stream_),
			tuple(sorted(assetVersions, reverse=True)))
