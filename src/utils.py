#!/usr/bin/env python
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Utilities to do some dirty work like file globing, 
# pyVersion handling etc

import os
import sys
import stat
import glob
import json

_404_IMAGE_PATH = 'icons/wile-e-coyote-card.jpg'
_PLACE_HOLDER_PATH = os.path.abspath('.') + os.sep + _404_IMAGE_PATH
pyVersion = sys.hexversion/(1<<24)

if pyVersion < 3:
  import Tkinter as tkModule
else:
  import tkinter as tkModule

def getStatDict(path):
  if pathExists(path):
    return os.stat(path)

getDefaultUserName = lambda : os.environ.get('USER', 'Anonymous')
pathExists = lambda p : p and os.path.exists(p)
isDir = lambda p : pathExists(p) and stat.S_ISDIR(getStatDict(p).st_mode)
isReg = lambda p : pathExists(p) and stat.S_ISREG(getStatDict(p).st_mode)

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
  else:
    response = dbCheck.get('value', None)
    if response:
      try:
        return json.loads(response.decode())
      except Exception as e:
        return dict(reason = e)
    else:
        return dict()

class DynaItem:
  def __init__(self, initArgs):
    __slots__ = (arg for arg in initArgs)
    for arg in initArgs:
      setattr(self, arg, initArgs[arg])
    
  def __str__(self): 
    return self.__dict__.__str__()

  def __repr__(self):
    return self.__str__()
