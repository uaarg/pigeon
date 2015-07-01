"""
Provides tools for importing images.
"""

import pyinotify
import queue
import os
import logging

import geo

logger = logging.getLogger(__name__)

supported_image_formats = ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm"]
supported_info_formats = ["txt"]


class Image:
    def __init__(self, name, image_path, info_path):
        self.name = name
        self.path = image_path
        self.info_path = info_path

        self._readInfo()
        self._prepareProperties()

        self.width = None # Automatically set later when image read
        self.height = None # Automatically set later when  image read
        self.field_of_view_horiz = 58.2
        self.field_of_view_vert = 44.5


        self.georeference = None

    def _readInfo(self):
        """
        Populates info_data with the data from the info file.
        """
        self.info_data = {}
        with open(self.info_path) as f:
            for line in f:
                key, sep, value = line.partition("=")
                self.info_data[key.strip()] = value.strip()

    def _prepareProperties(self):
        """
        Groups the raw data into Position and Orientation objects.
        """

        # Going through some extra effort to be able to surface a 
        # list of missing fields, not just the first missing one 
        # for a more user-friendly error message.
        field_map = {"easting": "utm_east",
                     "northing": "utm_north",
                     "zone": "utm_zone",
                     "height": "height",
                     "alt": "alt",
                     "pitch": "theta",
                     "roll": "phi",
                     "yaw": "psi"}

        missing_fields = [field for field in field_map.values() if field not in self.info_data.keys()]

        if len(missing_fields) != 0:
            raise(KeyError("Missing %s field(s) from info file." % ", ".join(missing_fields)))

        easting = float(self.info_data[field_map["easting"]])
        northing = float(self.info_data[field_map["northing"]])
        zone = int(self.info_data[field_map["zone"]])
        height = float(self.info_data[field_map["height"]])
        alt = float(self.info_data[field_map["alt"]])
        pitch = float(self.info_data[field_map["pitch"]])
        roll = float(self.info_data[field_map["roll"]])
        yaw = float(self.info_data[field_map["yaw"]])

        YAW_CORRECTION = 90 # Accounting for magnetometer offset from paparazzi
        yaw += YAW_CORRECTION

        lat, lon = geo.utm_to_DD(easting, northing, zone)
        self.plane_position = geo.Position(lat, lon, height, alt)
        self.plane_orientation = geo.Orientation(pitch, roll, yaw)

    def _prepareGeo(self):
        """
        Prepares all the data needed to perform geo-referencing on 
        this image into a georeference object. Will raise an Exception
        if anything important is missing (ex. image width or height).
        """
        if not self.width:
            raise(Exception("Can't geo-reference image. Missing image width."))
        if not self.height:
            raise(Exception("Can't geo-reference image. Missing image height."))

        self.camera_specs = geo.CameraSpecs(self.width, self.height, self.field_of_view_horiz, self.field_of_view_vert)
        self.georeference = geo.GeoReference(self.camera_specs)

    def _requireGeo(self):
        if not self.georeference:
            self._prepareGeo()

    def geoReferencePoint(self, pixel_x, pixel_y):
        """
        Determines the position of the location on the ground visible
        at pixel.
        """
        self._requireGeo()
        return self.georeference.pointInImage(self.plane_position, self.plane_orientation, pixel_x, pixel_y)

    def invGeoReferencePoint(self, position):
        """
        Determines the pixel that depicts the location at the provided
        position.
        """
        self._requireGeo()
        return self.georeference.pointOnImage(self.plane_position, self.plane_orientation, position)

    def getPlanePlumbPixel(self):
        """
        Returns a tuple of the x and y values of the pixel corresponding
        to the point in the image that's located directly below the plane.

        Returns None, None if the point isn't in the image.
        """
        self._requireGeo()
        return self.georeference.pointBelowPlane(self.plane_position, self.plane_orientation)


class Watcher:
    """
    Watches a directory for new images (and associated info files). 
    Adds them to it's queue.
    """
    def __init__(self):
        self.queue = queue.Queue()

        self.watch_manager = pyinotify.WatchManager()

        self.mask = pyinotify.IN_CLOSE_WRITE # Picking which types of events are watched.
                                             # Here we want to know AFTER a file has been written (new or existing)

        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, queue):
                self.queue = queue
                self.pending_images = {} # For saving which image files don't have a corresponding info file yet
                self.pending_infos = {} # For saving which info files don't have a corresponding image file yet

            def _createImage(self, filename, image_pathname, info_pathname):
                try:
                    new_image = Image(filename, image_pathname, info_pathname)
                except Exception as e:
                    logger.error("Unable to import image %s: %s" % (filename, e))
                else:
                    logger.info("Imported image %s" % filename)
                    self.queue.put(new_image)

            def process_IN_CLOSE_WRITE(self, event):
                filename, extension = os.path.splitext(event.name)
                extension = extension[1:]

                logger.debug("New file: %s" % event.name)

                # Matching image files with info files. Adding to the queue 
                # when a match is made.
                if extension.lower() in supported_image_formats:
                    info_pathname = self.pending_infos.pop(filename, False)
                    if info_pathname:
                        self._createImage(filename, event.pathname, info_pathname)
                    else:
                        self.pending_images[filename] = event.pathname
                elif extension.lower() in supported_info_formats:
                    image_pathname = self.pending_images.pop(filename, False)
                    if image_pathname:
                        self._createImage(filename, image_pathname, event.pathname)
                    else:
                        self.pending_infos[filename] = event.pathname

                if len(self.pending_images) > 1 or len(self.pending_infos) > 1:
                    logger.debug("Pending info files: %s" % ", ".join(self.pending_infos))
                    logger.debug("Pending image files: %s" % ", ".join(self.pending_images))

        handler = EventHandler(self.queue)
        self.notifier = pyinotify.ThreadedNotifier(self.watch_manager, handler)

        self.watches = None

    def setDirectory(self, path):
        """
        Sets the directory to be watched. Can be called even after the
        watcher has been started to change the directory being watched.
        """
        if self.watches is not None:
            for wd in self.watches.values():
                self.watches = self.watch_manager.rm_watch(wd)

        self.watches = self.watch_manager.add_watch(path, self.mask, rec=False)

    def start(self):
        """
        Starts watching the directory. Creates a second thread to 
        start the loop in.
        """
        self.notifier.start()

    def stop(self):
        """
        Stops watching the directory. Joins with the created thread and
        destroys it.
        """
        self.notifier.stop()

