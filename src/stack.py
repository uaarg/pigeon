#!/usr/bin/env python
# Author: Emmanuel Odeke <odeke@ualberta.ca>

class Stack:
  def __init__(self, content=list()):
    self.__ptr = 0
    self.__content = []
    self.__contentMap = dict() 
    self.__invertedIndexMap = dict()

  @property
  def size(self):
    return len(self.__contentMap)

  def push(self, key, value=None):
    keyIndex = self.size
    self.__invertedIndexMap[keyIndex] = key
    self.__contentMap[key] = (keyIndex, value,) # Save the latest value

  def popByKey(self, key, altValue=None):
    popd = self.__contentMap.pop(key, (-1, altValue,))
    return popd[1]

  def popByIndex(self, index, altValue=None):
    return self.__invertedIndexMap.pop(index, altValue)

  def pop(self):
    key = self.popByIndex(self.__ptr, None)
    # print('ptrIndex', self.__ptr)
    if key is not None:
      return self.popByKey(key, None)

  def reverseMapKey(self, index, altValue=None):
    return self.__invertedIndexMap.get(index, altValue) 

  @property
  def contentLength(self): return len(self.__contentMap)

  def canGetPrev(self): return self.__ptr > 0 and self.contentLength
  def canGetNext(self): return self.__ptr < (self.contentLength - 1)

  def next(self):
    self.__ptr += 1
    return self.__accessByIndexPtr()

  def accessByKey(self, keyName, altValue=None):
    return self.__contentMap.get(keyName, (-1, altValue,))[1]

  def __accessByIndexPtr(self):
    modBase = self.size
    if not modBase: modBase = 1
    keyName = self.__invertedIndexMap.get(self.__ptr % modBase, None)
    # print('keyName', keyName)
    if keyName is not None:
        return keyName, self.__contentMap.get(keyName, (-1, None,))[1]

  def setPtrToKeyIndex(self, key):
    indexOfKey = self.__contentMap.get(key, (0, None))[0]
    print('setting ptr to', indexOfKey)
    self.__ptr = indexOfKey 
    
  def prev(self):
    if self.__ptr > 0:
       self.__ptr -= 1
       return self.__accessByIndexPtr()

  def __str__(self):
    return self.__ptr.__str__()

def main():
    pass

if __name__ == '__main__':
    main()
