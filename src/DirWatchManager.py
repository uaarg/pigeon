#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import time

import dirCheck # Local module

class DirWatchManager:
    def __init__(self, onFreshPaths, onStalePaths):
        self.__onFreshPaths = onFreshPaths
        self.__onStalePaths = onStalePaths
        self.__pathToChecker = dict()

    def watchDir(self, path, sleepTimeout=10):
        if dirCheck.pathExists(path):
            memWatcher = self.__pathToChecker.get(path, None)
            if memWatcher is None:
                memWatcher = dirCheck.DirWatch(path, sleepTimeout)
                self.__pathToChecker[path] = memWatcher
                runner = memWatcher.bootStrap(time.time())
            else:
                print('\033[47mAlready watching', path, '\033[00mwill just set latest eventHandlers')
               
            memWatcher.setOnRetainableDetected(self.__onFreshPaths)
            memWatcher.setOnPurgeableDetected(self.__onStalePaths)

            return memWatcher

    def close(self):
        for memWatcher in self.__pathToChecker.values():
            memWatcher.killAll()
