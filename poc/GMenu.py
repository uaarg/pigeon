#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import copy # Module containing helpers to copy items

import GFrame
import resources as rscs

isIterable = lambda elem : elem and hasattr(elem, '__iter__')

class CustomMenu(rscs.tkModule.Menu):
  def __init__(self, root, itemFuncMap = {}):

    if not (root and isinstance(root, rscs.tkModule.Frame)):
      raise Exception (
        "Expecting that root must be an instance of a tkinter Frame"
      )

    # Make sure that options is an object subclassed from a dictionary
    # since we'll be mapping entries to call back functions
    # if not isIterable(itemFuncMap):
    #   raise Exception ("Options for a menu must be iterable")

    rscs.tkModule.Menu.__init__(self, root, tearoff=0)
    self.__options = copy.deepcopy(itemFuncMap)

  def addOption(self, option, callback):
    self.__options[option] = callback

  def popOption(self, optionKey):
    if optionKey in self.__options:
      self.__options.remove(optionKey)

  def flushSettings(self):
    for commandKey in self.__options:
      callBack = self.__options[commandKey]
      self.add_command(
        label=commandKey, command=callBack
      )

def createGSC(respectiveFrames):
  root = rscs.tkModule.Tk()
  frameMaps = dict()
  for frameName in respectiveFrames:
    body = respectiveFrames[frameName]
    sbMap = body.get('submitButtonMap', {})
    labelToEntryMap = body.get('labelToEntryMap', {})
    theFrame = GFrame.GFrame (
      root, submitButtonMap=sbMap, labelToEntryMap=labelToEntryMap
    )

    theFrame.create()
    print(theFrame)
    frameMaps[frameName] = theFrame
    theFrame.pack(side=rscs.tkModule.LEFT)

  menuBarOptions = [
    ("Quit", root.destroy), ("Save", lambda : 10)
  ]

  mainMenu = rscs.tkModule.Menu(root)

  for labelText, cmd in menuBarOptions:
    mainMenu.add_command(label=labelText, command=cmd)
  root.config(menu=mainMenu)

  return dict(root = root, frameMap = frameMaps)
  
def main():
  print("Custom menu here!")
  frameInitBody = dict(
    stringVar=None, entryFmtArgs=dict(),
    initArgs=None
  )

  respectiveFrames = dict (
    ImageMap = dict (
     labelMap = dict (Images= copy.copy(frameInitBody))
    ),
    Markers = dict (
     labelMap = dict (Markers= copy.copy(frameInitBody))
    ),
    Information = dict (
     labelMap = dict (Information= copy.copy(frameInitBody))
    ),
    Saving = dict (
     labelMap = dict (Saving = copy.copy(frameInitBody)),
     buttonMap = dict ()
    )
  )

  mapDict = createGSC(respectiveFrames)
  welcomeRoot = mapDict['root']
  welcomeRoot.mainloop()

if __name__ == "__main__":
  main()
