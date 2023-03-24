#!/usr/bin/env python3

import os
import logging
import argparse

import log
from ui import UI
from image import Watcher
import settings
import features
from comms.uav import UAV
from comms.uav_socket import UAVSocket
from comms.uav_mavlink import UAVMavLink
from exporter import ExportManager
import queue

__version__ = "0.5.1"


class IOQueue():
    def __init__(self):
        self.in_queue = queue.Queue()
        self.out_queue = queue.Queue()

class GroundStation:
    def __init__(self):
        super().__init__()
        self.loadSettings()
        self.image_watcher = Watcher()
        device = self.settings_data.get("MavLink Device")
        self.uav = UAVMavLink(device)

        ground_control_points = features.load_ground_control_points()
        export_manager = ExportManager(self.settings_data.get("Feature Export Path", "./"))

        about_text = """Pigeon

Pigeon is UAARG's ground imaging software. It can be used to control
the onboard imaging computer, view downloaded images, and make features
within those images. Marked features can be analyzed and exported.

Running in "%(run_directory)s"

Version: %(version)s

Copyright (c) 2016 UAARG
""" % {"version": __version__, "run_directory": os.getcwd()}

        # Temporary queues that will connect to UAV connections
        # TODO: Implement Mavlink communication for these queues
        self.im_queue = queue.Queue()
        self.feature_queue = IOQueue()

        self.ui = UI(save_settings=self.saveSettings,
                     load_settings=self.loadSettings,
                     export_manager=export_manager,
                     image_in_queue=self.im_queue,
                     feature_io_queue=self.feature_queue,
                     uav=self.uav,
                     ground_control_points=ground_control_points,
                     about_text=about_text)

    def loadSettings(self):
        self.settings_data = settings.load()
        return self.settings_data

    def saveSettings(self, settings_data):
        settings.save(settings_data)
        self._propagateSettings()

    def _propagateSettings(self):
        """
        Applies settings to things that need them. This should be called
        anytime the settings have been changed.
        """
        self.image_watcher.setDirectory(self.settings_data["Monitor Folder"])

        if self.settings_data.get("UAV Network"):
            self.uav.setBus(self.settings_data["UAV Network"])         

    def run(self):
        self._propagateSettings()

        if self.settings_data["Load Existing Images"] == True:
            self.image_watcher.loadExistingImages(self.settings_data["Monitor Folder"])
        self.uav.connect()
        self.image_watcher.start()

        self.ui.run() # This runs until the user exits the GUI

        self.image_watcher.stop()
        self.uav.disconnect()

def get_args():
    parser = argparse.ArgumentParser(description="pigeon ground imaging software. For analyzing and geo-referencing aerial imagery")
    parser.add_argument("-b", "--ivy-bus", type=str, default=None,
                              help="The subnet and port number to use when connecting to other pigeon instances through ivybus (default: '127:2010')")
    parser.add_argument("-ub", "--uav-ivy-bus", type=str, default="127:2011",
                              help="The subnet and port number to use when connecting to the uav through ivybus (default: '127:2011')")

    args = parser.parse_args()
    args.ivy_bus = args.ivy_bus or os.environ.get("IVYBUS")
    return args

def main():
    log.initialize()
    logger = logging.getLogger("station")
    logger.info('\n')
    logger.info("Started")
    logger.info("Version: %s" % __version__)

    args = get_args()
    logger.info("Arguments: %s" % args)
    ground_station = GroundStation()
    ground_station.run()

    logger.info("Finished")

if __name__ == "__main__":
    main()
