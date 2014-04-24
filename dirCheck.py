#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import time
from threading import Thread

accessTimeChecker = lambda path: os.path.getatime(path)
creationTimeChecker = lambda path: os.path.getctime(path)
pathExists = lambda qPath: qPath and os.path.exists(qPath)

class DirWatch:
    def __init__(self, dirPath=None, sleepTimeout=10):
        if not pathExists(dirPath):
            raise Exception("Unknown directory")

        self.__pathToWatch = dirPath
        self.__sleepTimeout = sleepTimeout or 10
        self.__isRunning = False

    def getPaths(self, lastSaveTime=0, statTimeAccessor=accessTimeChecker):
        freshPaths = []
        purgeable = []
        for root, dirs, paths in os.walk(self.__pathToWatch):
            for path in paths:
                joinedPath = os.path.join(root, path)
                if statTimeAccessor(joinedPath) >= lastSaveTime:
                    freshPaths.append(joinedPath)
                else:
                    purgeable.append(joinedPath)

        freshTh = purgeTh = None
        
        if purgeable:
            purgeTh = Thread(
                # target=self.__handleByBucket, args=(purgeable, os.unlink)
                target=self.__handleByBucket, args=(purgeable, lambda p: 'Purgeable: %s'%(p),)
            )
            purgeTh.start()

        if freshPaths:
            freshTh = Thread(
                # target=self.__handleByBucket, args=(
                #       freshPaths, lambda p: shutil.move(p, destDir)
                # )
                target=self.__handleByBucket, args=(freshPaths, lambda p: 'Fresh: %s'%(p),)
            )
            freshTh.start()

        return freshTh, purgeTh

    def __handleByBucket(self, elemBucket, generalAction):
        for elem in elemBucket:
            try:
                print(generalAction(elem))
            except Exception as e:
                print(e)

    def handleRun(self, startTime=0, action=None):
        threshTime = startTime
        self.__isRunning = True
        while self.__isRunning:
            freshTh, purgeTh = self.getPaths(threshTime) 
            print('\033[92mSleeping for ', self.__sleepTimeout, '\033[00m')
            threshTime = time.time()
            time.sleep(self.__sleepTimeout)

        print('\033[92mExiting now\033[00m')

    def kill(self):
        print('\033[91mKilling now\033[00m')
        self.__isRunning = False

    def bootStrap(self, startTime):
        runner = Thread(target=self.handleRun, args=(startTime,))
        runner.start()
        return runner

def main():
    dW = DirWatch('.')
    runner = dW.bootStrap(10)

    try:
        while 1:
            time.sleep(2)
    except KeyboardInterrupt:
        dW.kill()
    finally:
        runner.join()
        print('Bye now..')

if __name__ == '__main__':
    main()
