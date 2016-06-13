#!/usr/bin/env python
"""
    :module: cmd
    :platform: None
    :synopsis: This module will be used for a command line interface for MPCSave
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0

import sys
import argparse

def main():
    parser = argparse.ArgumentParser('ftrack_copyAsset', description="Tool to copy ftrack srcAsset builds between jobs")
    parser.add_argument('-s', '--sourceJob', dest="srcJobName", action="store", required=True, help="Name of source job")
    parser.add_argument('-b', '--buildName', dest="buildName", action="store", required=True, help="Name of asset build to copy")
    parser.add_argument('-o', '--override', dest='override', action='store_true', help="Override if destination asset build already exists", default=False)
    # These are not hooked up!
    parser.add_argument('-t', '--testmode', dest='testmode', action='store_true', help="Test mode - print without populating ftrack", default=False)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help="Verbose mode", default=False)

    if '' in sys.argv:
        sys.argv.remove('')
    args = parser.parse_args()

    if args.testmode:
        args.verbose = True

    try:
        args.dstJobName = os.environ["JOB"]
    except KeyError:
        print "Set job to destination job first!"
        return
    #copyAsset(args)

if __name__ == "__main__":
    main()