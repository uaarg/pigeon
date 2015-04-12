"""
Provides tools for importing images.
"""

import pyinotify
import queue
import os

supported_image_formats = ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm"]
supported_info_formats = ["txt"]

class Image:
    def __init__(self, name, image_path, info_path):
        self.name = name
        self.path = image_path
        self.info_path = info_path

        self.readInfo()

    def readInfo(self):
        """
        Populates info_data with the data from the info file.
        """
        self.info_data = {}
        with open(self.info_path) as f:
            for line in f:
                key, sep, value = line.partition("=")
                self.info_data[key.strip()] = value.strip()

class Watcher:
    """
    Watches a directory for new images (and associated info files). 
    Adds them to it's queue.
    """
    def __init__(self):
        self.queue = queue.Queue()

        self.watch_manager = pyinotify.WatchManager()

        self.mask = pyinotify.IN_CREATE  # Picking which types of events are watched

        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, queue):
                self.queue = queue
                self.pending_images = {} # For saving which image files don't have a corresponding info file yet
                self.pending_infos = {} # For saving which info files don't have a corresponding image file yet

            def process_IN_CREATE(self, event):
                filename, extension = os.path.splitext(event.name)
                extension = extension[1:]

                # Matching image files with info files. Adding to the queue 
                # when a match is maded.
                if extension.lower() in supported_image_formats:
                    info_pathname = self.pending_infos.pop(filename, False)
                    if info_pathname:
                        self.queue.put(Image(filename, event.pathname, info_pathname))
                    else:
                        self.pending_images[filename] = event.pathname
                elif extension.lower() in supported_info_formats:
                    image_pathname = self.pending_images.pop(filename, False)
                    if image_pathname:
                        self.queue.put(Image(filename, image_pathname, event.pathname))
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

