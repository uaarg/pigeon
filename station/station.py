#!/usr/bin/env python3

import os
import logging
import argparse

import log
from ui import UI
import image
import settings
import features
from comms.uav import UAV
from exporter import ExportManager

__version__ = "0.3"

class GroundStation:
    def __init__(self, uav_ivybus=None):
        super().__init__()
        self.loadSettings()
        self.image_watcher = image.Watcher()
        self.uav = UAV(uav_ivybus)

        ground_control_points = features.load_ground_control_points()
        export_manager = ExportManager(self.settings_data.get("Feature Export Path", "./"))

        self.ui = UI(save_settings=self.saveSettings,
                     load_settings=self.loadSettings,
                     export_manager=export_manager,
                     image_queue=self.image_watcher.queue,
                     uav=self.uav,
                     ground_control_points=ground_control_points)

    def checkMandatorySettings(self):
        for mandatory_field in ["Monitor Folder"]:
            try:
                self.settings_data[mandatory_field]
            except KeyError:
                raise(RuntimeError('Mandatory setting field "%s" not found. Please add it to the persisted data.' % mandatory_field))

    def loadSettings(self):
        self.settings_data = settings.load()
        return self.settings_data

    def saveSettings(self, settings_data):
        self.settings_data = settings_data
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
        self.checkMandatorySettings()
        self._propagateSettings()

        if self.settings_data["Load Existing Images"] == True:
            self.image_watcher.loadExistingImages(self.settings_data["Monitor Folder"])
        self.image_watcher.start()
        self.uav.start()

        self.ui.run() # This runs until the user exits the GUI
        self.image_watcher.stop()
        self.uav.stop()

def get_args():
    parser = argparse.ArgumentParser(description="pigeon ground imaging software. For analyzing and geo-referencing aerial imagery")
    parser.add_argument("-b", dest="ivy_bus", type=str, default=None, help="The subnet and port number to use when connecting to the UAV through ivybus (default: '127:2010')")

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

    ground_station = GroundStation(uav_ivybus=args.ivy_bus)
    ground_station.run()

    logger.info("Finished")

if __name__ == "__main__":
    main()
