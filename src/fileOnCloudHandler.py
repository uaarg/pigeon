#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Utility to enable file management on the cloud using restAssured

import os
import sys
import json
import hashlib

try:
    import requests
except ImportError:
    sys.stderr.write("\033[91mFirst install 'requests'\033[00m")
    sys.exit(-1)

getDefaultUserName = lambda: os.environ.get('USER', 'Anonymous')
isRegPath = lambda p: not os.path.isdir(p)

class FileOnCloudHandler:
    def __init__(self, url, checkSumAlgoName='md5'):
        self.__baseUrl = url.strip('/')
        self.__upUrl = self.__baseUrl + '/uploader'
        self.__mediaUrl = self.__baseUrl + '/media/'

        self.__checkSumAlgoName = checkSumAlgoName

    def initCheckSumAlgoName(self, algoName):
        self.__checkSumAlgoName = algoName

    def getCheckSumAlgoName(self):
        return self.__checkSumAlgoName

    def __pushUpFileByStream(self, isPut, stream, **attrs):
        if self.__checkSumAlgoName and hasattr(hashlib, self.__checkSumAlgoName):
            try:
                origPos = stream.tell()
                checkSum = getattr(hashlib, self.__checkSumAlgoName)(stream.read()).hexdigest()
                stream.seek(origPos) # Get back to originalPosition
            except Exception as e:
                print(e)
            else:
                attrs['checkSum'] = checkSum
                attrs['checkSumAlgoName'] = self.__checkSumAlgoName
 
        method = requests.put if  isPut else requests.post
        return method(self.__upUrl, data=attrs, files={'blob': stream})

    def __pushUpFileByPath(self, methodToggle, fPath, **attrs):
        response = None
        if fPath and os.path.exists(fPath):
            checkSumInfo = None
            with open(fPath, 'rb') as f:
                response = self.__pushUpFileByStream(methodToggle, f, **attrs)
       
            return response

    def uploadFileByStream(self, stream, **attrs):
        return self.__pushUpFileByStream(isPut=False, stream=f, **attrs)

    def uploadFileByPath(self, fPath, **attrs):
        return self.__pushUpFileByPath(False, fPath, **attrs)

    def updateFileByStream(self, f, **attrs):
        return self.uploadFileByStream(isPut=True, stream=f, **attrs)

    def updateFileByPath(self, fPath, **attrs):
        return self.__pushUpFileByPath(True, fPath, **attrs)


    def __pathForMediaDownload(self, fPath):
        return self.__mediaUrl + fPath

    def downloadFileToStream(self, fPath, readChunkSize=512):
        formedUrl = self.__pathForMediaDownload(fPath)
        dataIn = requests.get(formedUrl, stream=True)
        if dataIn.status_code == 200:
            return dataIn.iter_content(chunk_size=readChunkSize)

    def downloadFileToDisk(self, pathOnCloudName, altName=None, chunkSize=1024):
        chunkIterator = self.downloadFileToStream(pathOnCloudName, chunkSize)
        writtenBytes = 0
        if hasattr(chunkIterator, '__next__'):
            localName = altName or os.path.basename(pathOnCloudName)
            with open(localName, 'wb') as f:
                for chunk in chunkIterator:
                    if chunk:
                        writtenBytes += f.write(chunk)
                        f.flush()

        return writtenBytes

    def deleteFileOnCloud(self, **attrsDict):
        return requests.delete(self.__upUrl, **attrsDict)

    def getManifest(self, queryDict={}):
        return requests.get(self.__upUrl, params=queryDict)

    def jsonParseResponse(self, reqResponse):
        jsonParsed = dict()
        try:
            jsonParsed['data'] = json.loads(reqResponse.text).get('data', [])
        except Exception as e:
            print('Exception', e)
            jsonParsed['reason'] = str(e)
        finally:
            jsonParsed['status_code'] = reqResponse.status_code
            return jsonParsed

def main():
    argc = len(sys.argv)
    if argc < 2:
        sys.stderr.write('%s \033[42m<paths>\n\033[00m'%(__file__))
    else:
        fH = FileOnCloudHandler('http://127.0.0.1:8000', 'sha1')
        uploadFunc = lambda p: fH.uploadFileByPath(p, author=getDefaultUserName(), title=p)
        for p in sys.argv[1:]:
            if not os.path.exists(p):
                print('Non existant path', p)
                continue
            elif os.path.isdir(p):
                for root, dirs, paths in os.walk(p):
                    joinedPaths = map(lambda p: os.path.join(root, p), paths)
                    dlResponse = map(uploadFunc, joinedPaths)
                    print(list(dlResponse))
            else:
                print(uploadFunc(p))
        '''
        srcPath = '/Users/emmanuelodeke/Desktop/bbndk.png'
        uResponse =fH.uploadFileByPath(srcPath, author=getDefaultUserName(), title=srcPath)
        # print(uResponse)
        print(uResponse.text)
  
        shortPath = os.path.basename(srcPath) 
        print(fH.downloadFileToDisk('documents/' + shortPath))
        '''

        print(fH.getManifest(dict(select='id')).text)
        # print(fH.deleteFileOnCloud().text)

if __name__ == '__main__':
    main()
