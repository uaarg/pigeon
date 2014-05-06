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

    def __init__(self, parent=None, onDeleteMarkerFromDB):
        super(ImageDisplayer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.deleteMarkerFromDB = onDeleteMarkerFromDB
        self.initResources()

    def initResources(self):
        self.__fileOnDisplay = None

        # Set up camera
        self.image_width = 1294
        self.image_height = 964
        self.viewangle_horiz = 21.733333
        self.viewangle_vert = 16.833333
        self.camera = GPSCoord.CameraSpecs(self.image_width, self.image_height, self.viewangle_horiz, self.viewangle_vert) # Need to implement read from configuration file
        self.image_center_x = self.image_width/2
        self.image_center_y = self.image_height/2

        self.imgPixMap = None
        self._childMap = None
        self.__resourcePool = dict()

    def close(self, **kwargs):
        self.__jobRunner.close()

        for markerMap in self._childMap.values():
            for marker in markerMap.values():
                if marker and hasattr(marker, 'close'):
                    marker.close()

        super().close()

    def popAllMarkers(self, path):
        return self.__jobRunner.run(self.__popAllMarkers, None, None, path)

    def __popAllMarkers(self, path, **kwargs):
        markers = self._childMap.pop(path, [])
        for marker in markers.values():
            marker.close()

    def extractSetGeoData(self, infoDict):
        # Get position 
        northing = float(infoDict["utm_north"])
        easting = float(infoDict["utm_east"])
        zone = float(infoDict["utm_zone"])
        altitude = float(infoDict["z"])
        dd_coord = GPSCoord.utm_to_DD(easting, northing, zone) # lat, lon
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

    def renderImage(self, path, markerSet, currentMap, pixMap=None):
        if self._childMap is not None:
            for v in self._childMap.values():
                v.hide()

        filename = path if path else utils._PLACE_HOLDER_PATH

        image = None
        if pixMap is None:
            image =  QImage(filename)
            if image.isNull():
                QtWidgets.QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
                return
            else:
                self.imgPixMap = QPixmap.fromImage(image)
        
        else:
            self.imgPixMap = pixMap
        
        self._childMap = currentMap    
        self.setPixmap(self.imgPixMap)

        for mData in markerSet:
            x, y = int(mData.get('x', 0)), int(mData.get('y', 0))
            retrKey = (x, y,)
            memMarker = self._childMap.get(retrKey, None)
            print('memMarker', memMarker)
            if memMarker is None:
                memMarker = self.createMarker(
                    utils.DynaItem(dict(
                        x=lambda: x, y=lambda: y, lat=mData.get('lat', 0), lon=mData.get('lon', 0),
                        author=mData.get('author', 'Anonymous'), mComments=mData.get('comments','')
                    ))
                )
                memMarker.toggleSaved()
                memMarker.hide()

        for m in self._childMap.values():
            m.show()
        
    def mousePressEvent(self, e):
        # Event handler for mouse clicks on image area.

        # Left click - target location marking (temporary)
        if e.button() == 1:
            curPos = self.mapFromGlobal(self.cursor.pos())
            pointGPSPos = self.pointGeoReference(self.georeference, self.plane_position, self.plane_orientation, curPos.x(), curPos.y())
            (lat, lon) = pointGPSPos.latLon()
            # centerGPSPos = self.centerGeoReference(self.georeference, self.plane_position, self.plane_orientation)
            # (lat, lon) = centerGPSPos.latLon()
            print(curPos.x(), curPos.y())
            print([lat, lon])


        # Right click - target marker creation
        if e.button() == 2:
            curPos = self.mapFromGlobal(self.cursor.pos())
            # Georeference the marker location
            # pointGPSPos = self.pointGeoReference(self.georeference, self.plane_position, self.plane_orientation, curPos.x(), curPos.y())
            # (lat, lon) = pointGPSPos.latLon()
            centerGPSPos = self.centerGeoReference(self.georeference, self.plane_position, self.plane_orientation)
            (lat, lon) = centerGPSPos.latLon()
            print(lat, lon)

            m = self.__createMarker(utils.DynaItem(
                dict(x=curPos.x, y=curPos.y, lat=lat, lon=lon, mComments='', author=utils.getDefaultUserName())
            ))
            m.show()
            m.toggleUnsaved()

    def createMarker(self, curPos, **kwargs): 
        return self.__createMarker(curPos, **kwargs)

    def __createMarker(self, curPos, **kwargs):
        marker = Marker.Marker(
            parent=self, x=curPos.x(), y=curPos.y(), tree=self._childMap, author=curPos.author, lat=curPos.lat, lon=curPos.lon,
            mComments=curPos.mComments, onDeleteCallback=self.deleteMarkerFromDb, **kwargs
        )

        return marker

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    imViewer = ImageDisplayer()
    imViewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
  main()
