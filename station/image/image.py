"""
Provides tools for importing images.
"""

import pyinotify
import queue
import os

import geo

supported_image_formats = ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm"]
supported_info_formats = ["txt"]

class Image:
    def __init__(self, name, image_path, info_path):
        self.name = name
        self.path = image_path
        self.info_path = info_path

        self._readInfo()
        self._prepareProperties()

        self.width = None # Will be set later
        self.height = None # Will be set later
        self.field_of_view_horiz = 30
        self.field_of_view_vert = 20


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
                     "pitch": "phi",
                     "roll": "psi",
                     "yaw": "theta"}

        missing_fields = [field for field in field_map.values() if field not in self.info_data.keys()]

        if len(missing_fields) != 0:
            raise(Exception("Missing %s field(s) from info file while importing image %s." % (", ".join(missing_fields), self.name)))

        easting = float(self.info_data[field_map["easting"]])
        northing = float(self.info_data[field_map["northing"]])
        zone = int(self.info_data[field_map["zone"]])
        height = float(self.info_data[field_map["height"]])
        alt = float(self.info_data[field_map["alt"]])
        pitch = float(self.info_data[field_map["pitch"]])
        roll = float(self.info_data[field_map["roll"]])
        yaw = float(self.info_data[field_map["yaw"]])

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


    def geoReferencePoint(self, pixel_x, pixel_y):
        """
        Determines the position of the location on the ground visible
        at pixel
        """
        if not self.georeference:
            self._prepareGeo()

        return self.georeference.pointInImage(self.plane_position, self.plane_orientation, pixel_x, pixel_y)


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
                new_image = Image(filename, image_pathname, info_pathname)
                self.queue.put(new_image)

            def process_IN_CLOSE_WRITE(self, event):
                filename, extension = os.path.splitext(event.name)
                extension = extension[1:]

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

