#!/usr/bin/env python
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Utilities to do some dirty work like file globing, 
# pyVersion handling etc

import os
import sys
import stat
import glob
import json
from optparse import OptionParser

getDefaultUserName = lambda : os.environ.get('USER', 'Anonymous')
pathExists = lambda p : p and os.path.exists(p)
isDir = lambda p : p and os.path.isdir(p)
isReg = lambda p : p and os.path.isfile(p)

baseDir = os.path.dirname(os.path.abspath(__file__))

pathLocalization = lambda *args: os.sep.join((baseDir,) + args)
isCallable = lambda a: hasattr(a, '__call__')
isCallableAttr = lambda obj, attr: isCallable(getattr(obj, attr, None))

_404_IMAGE_PATH = 'icons/wile-e-coyote-card.jpg'
_PLACE_HOLDER_PATH = pathLocalization( _404_IMAGE_PATH)

def itemComparisonInWords(countA, countB):
    diff = countA - countB
    if diff != 0:
        absDiff = abs(diff)
        return '%d %s'%(absDiff, 'less' if diff < 0 else 'more')

def getStatDict(path):
  if pathExists(path):
    return os.stat(path)

def massagePath(path):
    if path:
        extractedPath = os.path.split(path)
        nameExtSplit = (extractedPath[-1]).split('.')
        return [extractedPath[0]] + nameExtSplit

def getLocalName(path):
    splitPath = massagePath(path)
    if isinstance(splitPath, list) and len(splitPath) == 3:
        dirLocation, localName, extension = splitPath
        return localName
    

def getPathsLike(regexList, srcDir=None):
  originalPath = None
  if isDir(srcDir): # Must change current path to the target source and revert after the desired matching
    originalPath = os.path.abspath('.')
    os.chdir(srcDir)

  # Don't want to recomputation in matching paths of duplicate regexs
  _regexsAsSet = set(regexList)
  matches = dict()

  curFullPath = os.path.abspath('.')
  for regex in _regexsAsSet:
    pathMatches = glob.glob(regex) 
    # perform an abspath preprocessing
    fullPaths = map(lambda p : os.path.join(curFullPath, p), pathMatches)
    matches[regex] = list(fullPaths)
    
  if originalPath: # Revert back to original path
    os.chdir(originalPath)

  return matches

def getInfoFileNameFromImagePath(fPath):
        if not fPath:
            return -1

        splitPath = os.path.split(fPath)
        parentDir, axiom = os.path.split(fPath)
        seqIDExtSplit = axiom.split('.')

        if not (seqIDExtSplit and len(seqIDExtSplit) == 2):
            print('Erraneous format, expecting pathId and extension eg from 12.jpg')
            return -1

        seqID, ext = seqIDExtSplit
        if ext != 'jpg':
            print('Could not find an info file associated with the image', fPath)
            return -1

        # Scheme assumed is that directories [info, data] have the same parent
        grandParentDir, endAxiom = os.path.split(parentDir)

        infoFilename = os.sep.join([grandParentDir, 'info', seqID + '.txt'])
        return infoFilename

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')
    parser.add_option('-e', '--eavsdropping', default=False, help='Turn on eavsdropping', dest='eavsDroppingMode', action='store_true')

    return parser.parse_args()

class DynaItem:
  def __init__(self, **initArgs):
    __slots__ = (arg for arg in initArgs)
    for arg in initArgs:
      setattr(self, arg, initArgs[arg])
    
  def __str__(self): 
    return self.__dict__.__str__()

  def __repr__(self):
    return self.__str__()
