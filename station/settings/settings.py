"""
Provides a way to save and restore user configuration/preferences.
"""

import os
import json
import logging

location = os.path.join(*["data", "settings.json"])
default_settings_data = {
    "Plane Plumbline": True,
    "Load Existing Images": True,
    "Monitor Folder": "data/images",
    "UAV Network": "127:2011",
    "Pigeon Network": "127:2010",
    "Follow Images": True,
    "Feature Export Path": "data/exports",
    "Nominal Target Size": "2.5",
    "Instance Name": "",
    "MavLink Device": "/dev/cu.usbserial-DN007320",
}

settings_data = default_settings_data.copy() # Global settings data.


logger = logging.getLogger(__name__)

def _update_global_dict(new_data):
    settings_data.update(new_data)

def _handleMigrations():
    """
    Handling data structure changes here. That is, taking old style settings,
    and turning them into new-style. This is often required to avoid
    requiring users to manually change or clear their settings. In
    order for this to work, a few rules need to be followed:

    1. Add an appropriate migration here anytime you change the
       default_settings_data in an incompatible fashion (ex. renaming
       a field).
    2. Don't remove any existing migrations.
    3. Add your migration to the end.
    4. Your migration shouldn't do anything if called a second time.

    Note that this doesn't handle users going backwards: using a newer
    settings file with an older version of Pigeon. They are on their
    own in this case (so should clear their settings if they run into
    any issues).
    """

    # 1 - Moving UAV Network to different port
    custom_uav_network = settings_data.get("UAV Network")
    if custom_uav_network == "127:2010":
        settings_data["UAV Network"] = "127:2011"

def load():
    """
    Returns a dictionary of the saved settings. This mutable object
    will be updated if the settings are changed. Keep a reference to
    this dict to get updates if desired.

    Settings are loaded from a file located at the location variable.
    In the event that the file DNE, then it is created with the 
    default settings.
    """
    try:
        with open(location) as settings_file:
            _update_global_dict(json.load(settings_file))
    except FileNotFoundError:
        logger.debug("Settings currently do not exist. Creating it..")
        with open(location, 'w+') as settings_file:
            settings_file.write(json.dumps(default_settings_data))

    except ValueError as e:
        logger.debug("Custom settings file corrupt: %s" % e)
    else:
        logger.debug("Loaded settings.")

    _handleMigrations()
    return settings_data

def save(settings):
    """
    Saves provided dictionary of settings. Updates the dictionary
    returned by load() with these settings: everything that uses those
    settings will be updated with these new ones.
    """
    _update_global_dict(settings)

    different_data = {key: value for key, value in settings_data.items() if value != default_settings_data.get(key)}
    with open(location, "w") as settings_file:
        json.dump(different_data, settings_file, indent=4)

    logger.debug("Saved settings.")
    return settings_data
