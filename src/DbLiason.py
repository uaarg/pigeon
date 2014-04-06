#!/usr/bin/python3

import os
import json
import collections
import urllib.request, urllib

class DbConn:
  def __init__(self, baseUrl):
    self.baseUrl = baseUrl

  def __urlRequest(self, method, isGet=False, **getData):
    fmtdData = json.dumps(getData)
    reqUrl = self.baseUrl if not isGet else self.baseUrl + '/?' + '&'.join(['{k}={v}'.format(k=k, v=v) for k,v in getData.items()])
    req = urllib.request.Request(reqUrl)
    req.add_header('Content-Type', 'application/json')
    req.get_method = lambda : method.upper()
    dataOut = dict()
    try:
      uR = urllib.request.urlopen(req, bytes(fmtdData, encoding='utf-8'))
    except Exception as e:
      print(e)
      dataOut['reason'] = e
    else:
      dataOut['value'] = uR.read()
    return dataOut

  def get(self, data):
    return self.__urlRequest('get', isGet=True, **data)

  def put(self, data):
    return self.__urlRequest('put', **data)

  def post(self, data):
    return self.__urlRequest('post', **data)

  def delete(self, data):
    return self.__urlRequest('delete', **data)

class HandlerLiason(object):
  def __init__(self, baseUrl, *args, **kwargs):
    self.baseUrl = baseUrl
    self.__callableCache = collections.defaultdict(
      lambda *arg, **kwargs : 'Not yet defined: {a}, {k}'.format(a=args, k=kwargs)
    )
    self.handler = DbConn(baseUrl)

  def postConn(self, data):
    return self.handler.post(data)

  def deleteConn(self, data):
    return self.handler.delete(data)

  def putConn(self, data):
    return self.handler.put(data)

  def getConn(self, data):
    return self.handler.get(data)

class GCSHandler(object):
  def __init__(self, baseUrl, *args, **kwargs):
    self.baseUrl = baseUrl
    self.__imageHandler = HandlerLiason(baseUrl + '/imageHandler')
    self.__markerHandler = HandlerLiason(baseUrl + '/markerHandler')

  @property
  def imageHandler(self): return self.__imageHandler

  @property
  def markerHandler(self): return self.__markerHandler

def main():
  gcsH = GCSHandler('http://192.168.1.102:8000/gcs') 
  imageHandler  = gcsH.imageHandler
  markerHandler = gcsH.markerHandler
  print(imageHandler.getConn(dict(title=1)))
  with open(__file__, 'r') as f:
    blob = f.read()
    markerData = dict(
      author=os.environ['USER'], title='Red SUV',
      x=100.1, y=24.1, associatedImage_id=1
    )
    print(markerHandler.postConn(markerData))

    print(
      imageHandler.postConn(
        dict(uri=__file__,author="Emmanuel Odeke", title='AirField', blob=blob)
      )
    )
if __name__ == '__main__':
  main()
