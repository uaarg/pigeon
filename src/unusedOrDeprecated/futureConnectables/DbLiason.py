#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
import json
import collections

pyVersion = sys.hexversion / (1<<24)

if pyVersion >= 3:
    import urllib.request as urlReqModule
    byteFyer = dict(encoding='utf-8')
else:
    import urllib2 as urlReqModule
    byteFyer = dict()

class DbConn:
  def __init__(self, baseUrl):
    self.baseUrl = baseUrl

  def __urlRequest(self, method, isGet=False, **getData):
    fmtdData = json.dumps(getData)
    reqUrl = self.baseUrl if not isGet else self.baseUrl + '/?' + '&'.join(['{k}={v}'.format(k=k, v=v) for k,v in getData.items()])
    req = urlReqModule.Request(reqUrl)
    req.add_header('Content-Type', 'application/json')

    '''
    req.add_header('enctype', 'multipart/form-data')

    if fPathToUpload:
        # with  as f:
        dataIn = open(fPathToUpload, 'rb').read()
        req.add_header('Contentlength', len(dataIn))
        req.add_header('files', dataIn)
    '''

    req.get_method = lambda : method.upper()
    dataOut = dict()
    statusCode = 500
    try:
      uR = urlReqModule.urlopen(req, bytes(fmtdData, **byteFyer))
    except Exception as e:
      print(e)
      dataOut['reason'] = e
    else:
      dataOut['value'] = uR.read()
      statusCode = uR.getcode()
    finally:
      dataOut['status_code'] = statusCode

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
    self.__blobHandler = HandlerLiason(baseUrl + '/list')
    self.__imageHandler = HandlerLiason(baseUrl + '/imageHandler')
    self.__markerHandler = HandlerLiason(baseUrl + '/markerHandler')

  @property
  def imageHandler(self): return self.__imageHandler

  @property
  def markerHandler(self): return self.__markerHandler

  @property
  def blobHandler(self): return self.__blobHandler

class UploadHandler(object):
    def __init__(self, baseUrl, *args, **kwargs):
        self.dataHandler = HandlerLiason(baseUrl + '/')
    

def main():
    uHandler = UploadHandler('http://127.0.0.1:8000/uploader') 
    blobHandler = uHandler.dataHandler

    targetFile = __file__ # './icons/iconmonstr-checkbox.png'
    print(
        blobHandler.getConn(dict())
    )

    print(blobHandler.postConn(dict()))

    '''
    print(
        blobHandler.getConn(dict(select='data'))
    )

    print(
        blobHandler.deleteConn(dict())
    )
    '''
            
if __name__ == '__main__':
  main()
