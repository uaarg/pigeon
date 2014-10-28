#! /usr/bin/env python3

from CorrelationEngine import *
import os
import sys
import getopt
import itertools



class Runner:
    def __init__(self, debug = False):
        self.debug = debug

    def runCorrelation(self, refpath = "reference", colpath = "collected", outpath = "out.csv"):
        """
        Does the thing ;)
        """
        refFiles = self.grabKmlFiles(refpath)
        colFiles = self.grabKmlFiles(colpath)

        c = CorrelationEngine()

        for f in refFiles:
            c.addReference(f)
        for g in colFiles:
            c.addCollected(g)

        c.exportResults(outpath)


    def debugPrint(self, msg):
        if self.debug:
            print(msg)


    def grabKmlFiles(self, path):
        """
        Recursively traverses the directory structure down from "path", 
        returning the relative path to any kml file found.
        """
        f = [[os.path.join(root,f) for f in files if f.endswith('.kml')] for root, dirs, files in os.walk(path)]
        self.debugPrint("Found the following {} files: {}".format(path, f))
        return list(itertools.chain.from_iterable(f))

if __name__ == "__main__":
    r = Runner()
    r.runCorrelation(*sys.argv[1:])
