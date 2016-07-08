"""
Provides a way to save and restore user configuration/preferences.
"""

import os
import json
import logging

location = os.path.join(*["data", "settings.json"])
settings_data = {
    "Plane Plumbline": True,
    "Load Existing Images": True,
    "Monitor Folder": "data/images",
    "UAV Network": "127:2010",
    "Follow Images": True,
    "Feature Export Path": "data/exports/",
    "Nominal Target Size": "2.5"
} # Global settings data. These are the defaults.


logger = logging.getLogger(__name__)

def _update_global_dict(new_data):
    settings_data.update(new_data)

def load():
    """
    Returns a dictionary of the saved settings. This mutable object
    will be updated if the settings are changed. Keep a reference to
    this dict to get updates if desired.
    """
    try:
        with open(location) as settings_file:
            _update_global_dict(json.load(settings_file))
    except FileNotFoundError:
        logger.debug("No custom settings to load.")
    else:
        logger.debug("Loaded settings.")
    return settings_data

def save(settings):
    """
    Saves provided dictionary of settings. Updates the dictionary
    returned by load() with these settings: everything that uses those
    settings will be updated with these new ones.
    """
    _update_global_dict(settings)
    with open(location, "w") as settings_file:
        json.dump(settings_data, settings_file, indent=4)

    logger.debug("Saved settings.")
    return settings_data
