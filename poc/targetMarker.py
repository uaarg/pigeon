#!/usr/bin/env python
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Proof of concept for adding markers to an image, porting will be done to QT
# Usage:
# ./targetMarker ~/Pictures

# Requires module cImage [written by Brad Miller] -- extends a canvas and tkinter

import sys
import time
import cImage
from math import sqrt

import resources as rscs

def pointsOnCircle(x, y, r=10.0, steps=80.0, ringTh=10):
  def getByRadius(radius):
    onCircle = list()
    i = x - radius
    rSquared = radius * radius
    diff = float.__div__(radius, steps)
    while i <= x * 2:
      xSqr = (x - i) ** 2
      if xSqr <= rSquared:
        sqR = sqrt(abs(rSquared - xSqr))
        onCircle.append(cImage.Point(i, y - sqR))
        onCircle.append(cImage.Point(i, y + sqR))
      i += diff
    onCircle.append(cImage.Point(x, y))

    return onCircle

  comboOnCircle = []
  for i in range(ringTh):
    onCircle = getByRadius(r - i)
    comboOnCircle += onCircle
      
  return set(comboOnCircle)

class CustImageWin(cImage.ImageWin):
  def __init__(self, *args, **kwargs):
    cImage.ImageWin.__init__(self, *args, **kwargs)

class CustImageViewer:
  def __init__(self, *args, **kwargs):
    self.__win = cImage.ImageWin(*args, **kwargs)
    self.__win.setMouseHandler(self.handleClicks)
    self.__tImage = None

  def hasValidImage(self):
    return isinstance(self.__tImage, cImage.AbstractImage)

  @property
  def maxX(self):
    return self.__tImage.getWidth()
 
  @property
  def maxY(self): return self.__tImage.getHeight()

  @property
  def minY(self): return 0.0

  @property
  def minX(self): return 0.0

  def isInRange(self, x, y):
    return self.hasValidImage()\
       and (x <= self.maxX and x >= self.minX)\
       and (y <= self.maxY and y >= self.minY)
 
  def handleClicks(self, point):  
    print(point.x, point.y)
    redPixel = cImage.Pixel(255, 0, 0)
    if self.__tImage:
      circleInfo = pointsOnCircle(point.x, point.y, r=42.0, ringTh=10)
      # Now actually drawing of the lines
      for pt in circleInfo:
        if self.isInRange(pt.x, pt.y):
          self.__tImage.setPixel(int(pt.x), int(pt.y), redPixel)
        # else:
        #   print('outOfRange', pt)
      self.__tImage.draw(self.__win)

  def show(self, filePath, *args, **kwargs):
    if rscs.pathExists(filePath):
      self.__tImage = cImage.FileImage(filePath, *args, **kwargs)
      self.__tImage.draw(self.__win)
      self.__currentPath = filePath

  def slideShow(self, paths, timeout=5):
    for p in paths:
      self.show(p)
      time.sleep(timeout)

def main():
  argc = len(sys.argv)
  srcDir = '.'
  if argc > 1:
    srcDir = sys.argv[1]

  imgMatches = rscs.getPathsLike(['*.jpg', '*.png'], srcDir=srcDir)
  allMatches = []
  for regex in imgMatches:
    allMatches += imgMatches.get(regex, [])

  if allMatches:
    cImgViewer = CustImageViewer(__file__, 600, 600)

    cImgViewer.slideShow(allMatches, timeout=2.2)

  rscs.tkModule.mainloop()
      
if __name__ == '__main__':
  main()
