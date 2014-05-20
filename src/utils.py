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

_404_IMAGE_PATH = 'icons/wile-e-coyote-card.jpg'
_PLACE_HOLDER_PATH = os.sep.join(('.', _404_IMAGE_PATH,))

getDefaultUserName = lambda : os.environ.get('USER', 'Anonymous')
pathExists = lambda p : p and os.path.exists(p)
isDir = lambda p : pathExists(p) and stat.S_ISDIR(getStatDict(p).st_mode)
isReg = lambda p : pathExists(p) and stat.S_ISREG(getStatDict(p).st_mode)

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

def produceAndParse(func, dataIn):
  dbCheck = func(dataIn)
  if hasattr(dbCheck, 'reason'):
    print(dbCheck['reason'])
    return dbCheck
  else:
    response = dbCheck.get('value', None)
    if response:
      try:
        outValue = json.loads(response.decode())
        outValue['status_code'] = dbCheck.get('status_code', 200)
        return outValue
      except Exception as e:
        return dict(reason=str(e))
    else:
        return dbCheck

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')
    parser.add_option('-e', '--eavsdropping', default=False, help='Turn on eavsdropping', dest='eavsDroppingMode', action='store_true')

    return parser.parse_args()

class DynaItem:
  def __init__(self, initArgs):
    __slots__ = (arg for arg in initArgs)
    for arg in initArgs:
      setattr(self, arg, initArgs[arg])
    
  def __str__(self): 
    return self.__dict__.__str__()

  def __repr__(self):
    return self.__str__()
