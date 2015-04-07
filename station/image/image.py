"""
Provides tools for importing images.
"""

import pyinotify
import queue
import os

supported_image_formats = ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm"]
supported_text_formats = ["txt"]

class Image:
    def __init__(self, name, path):
        self.name = name
        self.path = path

class Watcher:
    """
    Watches a directory for new images. Adds them to it's queue.
    """
    def __init__(self):
        self.queue = queue.Queue()

        self.watch_manager = pyinotify.WatchManager()

        self.mask = pyinotify.IN_CREATE  # Picking which types of events are watched

        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, queue):
                self.queue = queue
            def process_IN_CREATE(self, event):
                filename, extension = os.path.splitext(event.name)
                extension = extension[1:]
                if extension.lower() in supported_image_formats:
                    self.queue.put(Image(filename, event.pathname))

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

