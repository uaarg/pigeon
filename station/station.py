#!/usr/bin/env python3

from ui import UI
import image
import settings

class GroundStation:
    def __init__(self):
        super().__init__()
        self.image_watcher = image.Watcher()

        self.ui = UI(save_settings=self.saveSettings,
                     load_settings=self.loadSettings,
                     image_queue=self.image_watcher.queue)

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
        self.image_watcher.setDirectory(self.settings_data["Monitor Folder"])

    def run(self):
        self.loadSettings()
        self.checkMandatorySettings()

        self.image_watcher.setDirectory(self.settings_data["Monitor Folder"])
        self.image_watcher.start()

        self.ui.run() # This runs until the user exits the GUI
        self.image_watcher.stop()


def main():
    ground_station = GroundStation()
    ground_station.run()

if __name__ == '__main__':
    main()
