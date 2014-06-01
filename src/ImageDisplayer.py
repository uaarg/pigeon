#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>

import os
import time
import collections
from threading import Thread

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QCursor, QPixmap

import utils # Local module
import Marker # Local module
import GPSCoord # Local module for GPS coordinate calculations
import mpUtils.JobRunner

class ImageDisplayer(QtWidgets.QLabel):
    __jobRunner = mpUtils.JobRunner.JobRunner()

    def __init__(self, parent=None, onDeleteMarkerFromDB=None, onMarkerMove=None):
        super(ImageDisplayer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.__allowClicks = False

        self.onMarkerMove = onMarkerMove
        print('onMarkerMove', onMarkerMove)
        self.deleteMarkerFromDB = onDeleteMarkerFromDB

        self.initResources()

    def allowClicks(self):
        self.__allowClicks = True

    def disableClicks(self):
        self.__allowClicks = False

    def initResources(self):
        self.__fileOnDisplay = None

        # Set up camera
        self.image_width = 1294
        self.image_height = 964
        self.viewangle_horiz = 21.733333
        self.viewangle_vert = 16.833333
        self.camera = GPSCoord.CameraSpecs(
            self.image_width, self.image_height, self.viewangle_horiz, self.viewangle_vert
        ) # Need to implement read from configuration file
        self.image_center_x = self.image_width/2
        self.image_center_y = self.image_height/2

        self.imgPixMap = None
        self._childMap = None
        self.__resourcePool = dict()

    def close(self, **kwargs):
        self.__jobRunner.close()

        if self._childMap:
            for marker in self._childMap.values():
                if marker and hasattr(marker, 'close'):
                    marker.close()

        super().close()

    def extractSetGeoData(self, infoDict):
        # Get position 
        northing = float(infoDict["utm_north"])
        easting = float(infoDict["utm_east"])
        zone = float(infoDict["utm_zone"])
        altitude = float(infoDict["alt"])
        # print('infoDict', infoDict)
        dd_coord = GPSCoord.utm_to_DD(easting, northing, zone) # lat, lon
        print('\033[94mdd_coord', dd_coord, altitude, '\033[00m')
        self.plane_position = GPSCoord.Position(dd_coord[0], dd_coord[1], altitude)

        # Get orientation
        pitch = float(infoDict["theta"])
        roll = float(infoDict["phi"])
        yaw = float(infoDict["psi"])

        self.plane_orientation = GPSCoord.Orientation(pitch, roll, yaw)
        # print("orientation object set up")

        # Set up georeference object
        self.georeference = GPSCoord.GeoReference(self.camera)
        # print("georef object set up")

    def pointGeoReference(self, georeference_obj, position, orientation, point_x, point_y):
        """
        Returns the georeferenced point in the image as a new Position object with DD lat, long.
        georeference_obj = 
        position =  Position object containing lat, long, and altitude of the plane frm GPSCoord
        orientation = Orientation object containing pitch, roll, yaw of the plane from GPSCoord
        point_x = pixels from left edge of image.
        point_y = pixels from right edge of image.
        """
        point_gpsPosition = georeference_obj.pointInImage(position, orientation, point_x, point_y)
        return point_gpsPosition

    def centerGeoReference(self, georeference_obj, position, orientation):
        center_gpsPosition = georeference_obj.centerOfImage(position, orientation)
        return center_gpsPosition

    def renderImage(self, path, markerSet, currentMap, pixMap=None, altPixMap=None):
        if hasattr(self._childMap, 'values'):
            for v in self._childMap.values():
                v.hide()

        self.__allowClicks = False

        if not hasattr(pixMap, 'isNull'):
            self.imgPixMap = QPixmap(path)
        else:
            self.imgPixMap = pixMap
       
        if self.imgPixMap.isNull(): 
            self.imgPixMap = altPixMap

        if (not hasattr(self.imgPixMap, 'isNull')) or self.imgPixMap.isNull():
            QtWidgets.QMessageBox.information(self, "Error", "Can't load image %s." %(path))
            return False

        else:
            self.__allowClicks = True

        print('cMap is currentMap', self._childMap is currentMap)
        self._childMap = currentMap    
        self.setPixmap(self.imgPixMap)

        for mData in markerSet:
            mData['x'] = int(mData.get('x', 0))
            mData['y'] = int(mData.get('y', 0))
            mData.setdefault('iconPath', 'icons/mapMarkerOut.png')

            memMarker = self._childMap.get(mData.get('longHashNumber', None), None)

            if memMarker is None:
                memMarker = self.createMarker(**mData)
                memMarker.toggleSaved()
            else:
                memMarker.updateContent(**mData)

        for m in self._childMap.values():
            m.show()

        return True
        
    def mousePressEvent(self, e):
        if not self.__allowClicks:
            e.ignore()

        # Event handler for mouse clicks on image area.

        # Left click - target location marking (temporary)
        elif e.button() == 1:
            curPos = self.mapFromGlobal(self.cursor.pos())
            pointGPSPos = self.pointGeoReference(self.georeference, self.plane_position, self.plane_orientation, curPos.x(), curPos.y())
            (lat, lon) = pointGPSPos.latLon()
            # centerGPSPos = self.centerGeoReference(self.georeference, self.plane_position, self.plane_orientation)
            # (lat, lon) = centerGPSPos.latLon()
            print(curPos.x(), curPos.y())
            print([lat, lon])


        # Right click - target marker creation
        elif e.button() == 2:
            curPos = self.mapFromGlobal(self.cursor.pos())
            pointGPSPos = self.pointGeoReference(
                self.georeference, self.plane_position, self.plane_orientation, curPos.x(), curPos.y()
            )
            (lat, lon) = pointGPSPos.latLon()
            print(lat, lon)

            m = self.createMarker(
                x=curPos.x(), y=curPos.y(), lat=lat,comments='',
                author=utils.getDefaultUserName(), lon=lon
            )
            m.show()
            m.toggleUnsaved()

    def createMarker(self, **data):
        m = Marker.Marker(
            onMoveEvent=self.onMarkerMove, parent=self, onDeleteCallback=self.deleteMarkerFromDB,
            tree=self._childMap, **data
        )
        return m

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    imViewer = ImageDisplayer()
    imViewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
  main()
