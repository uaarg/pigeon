#!/usr/bin/env python
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Generic Frame that you pass into a layout of
# the  desired look in the form of nested dicts

import resources as rscs

class GFrame(rscs.tkModule.Frame):
  def __init__(
      self, root, width=200, height=200, labelToEntryMap=dict(), 
      submitButtonMap=dict(), validatorFuncs=dict(), fields=list(),
      *args, **kwargs
  ):
    self.__root = root
    self.__fields = fields
    self.__children = list()
    self.__validatorFuncs = validatorFuncs
    self.__labelToEntryMap = labelToEntryMap
    self.__submitButtonMap = submitButtonMap
    self.__args = args
    self.__kwargs = kwargs

  def __setStringVars(self):
    entriesMap = self.__labelToEntryMap.get('entryMap', {})
    for attrDict in entriesMap.values():
      attrDict['stringVar'] = rscs.tkModule.StringVar(self)

      # Retrieve the entry's initializing arguments and set them
      initArgs = attrDict.get('initArgs', 'PlaceHolder :)')
      attrDict['stringVar'].set(initArgs)

  def __createChildren(self):
      self.__labelMap = dict()
      rowIndex = 0
      labels = self.__labelToEntryMap.get('labelMap', {})
      entries = self.__labelToEntryMap.get('entryMap', {})
      buttons = self.__labelToEntryMap.get('buttonMap', {})

      for labelKey, attrLabelMap in  labels.items():
        print(labelKey, attrLabelMap)
        textVar = attrLabelMap.get('stringVar', None) 
        entryFmtArgs = attrLabelMap.get('entryFmtArgs', None)

        freshLabel = rscs.tkModule.Label(
          self, entryFmtArgs, text=labelKey, relief=rscs.tkModule.RAISED, width=25
        )
        freshLabel.pack()

      for entryKey, attrEntryMap in entries.items():
        textVar = attrEntryMap.get('stringVar', None)
        entryFmtArgs = attrEntryMap.get('entryFmtArgs', None)

        freshEntry = rscs.tkModule.Entry(self, entryFmtArgs, textvariable=textVar)
        freshLabel = rscs.tkModule.Label(self, text=entryKey)
        freshLabel.grid(row=rowIndex, column=1)
        freshEntry.grid(row=rowIndex, column=1)
        rowIndex += 1

        freshLabel.pack()
        freshEntry.pack()

        self.__labelMap[entryKey] = freshLabel

      for buttonKey, attrButtonMap in buttons.items():
        textVar = attrButtonMap.get('stringVar', None)
        initArgs = attrButtonMap.get('initArgs', 'UnMapped Button')
        buttonAttrs = attrButtonMap.get('buttonAttrs', {})
        if textVar:
          textVar.set(initArgs);

        entryFmtArgs = attrButtonMap.get('entryFmtArgs', None)
        freshButton = rscs.tkModule.Button(self, entryFmtArgs, **buttonAttrs)
        freshButton.pack() # side=rscs.tkModule.LEFT)
      
      if self.__submitButtonMap:
        __initArgs = self.__submitButtonMap.get('initArgs', {})
        self.__submitButton = rscs.tkModule.Button(self, **__initArgs)
        self.__submitButton.pack()

  def create(self):
    if not self.__root:
      self.__root = rscs.tkModule.Tk()
      self.__root.title(self.__title)

    rscs.tkModule.Frame.__init__(self, self.__root, *self.__args, **self.__kwargs)

    self.__setStringVars()
    self.__createChildren()

def main():
  root = rscs.tkModule.Tk()
  root.title('GFrame test')

  gF = GFrame(root,
    labelToEntryMap=dict(
      entryMap = dict(
        Username = dict(
          stringVar=None, initArgs='Odeke', entryFmtArgs=dict()
        ),
        Host = dict(
          stringVar=None, initArgs='uaarg@uaargHQ', entryFmtArgs=dict()
        )
      ),
      labelMap = dict(
        TestLabel = dict(
          stringVar=None, entryFmtArgs=dict()
        )
      ),
    ),
    submitButtonMap = dict(
      initArgs = dict(
        text='Connect', command=lambda : root.quit(),
        relief=rscs.tkModule.GROOVE, cursor='arrow'
      )
    )
  )

  gF.create()
  gF.pack()
  root.mainloop()

if __name__ == '__main__':
  main()
