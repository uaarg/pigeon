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
    self.__invertedIndexMap[self.size] = key
    self.__contentMap[key] = value # Save the latest value

  def popByKey(self, key, altValue=None):
    return self.__contentMap.pop(key, altValue)

  def popByIndex(self, index, altValue=None):
    return self.__invertedIndexMap.pop(index, altValue)

  def pop(self):
    key = self.popByIndex(self.__ptr, None)
    print('ptrIndex', self.__ptr)
    if key is not None:
      contentPop = self.__contentMap.pop(key, None)
      return contentPop

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
    return self.__contentMap.get(keyName, altValue)

  def __accessByIndexPtr(self):
    modBase = self.size
    if not modBase: modBase = 1
    keyName = self.__invertedIndexMap.get(self.__ptr % modBase, None)
    print('keyName', keyName)
    if keyName is not None:
        return keyName, self.__contentMap.get(keyName, None)

    
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
