"""
Provides a way to save and restore user configuration/preferences.
"""

import os
import json

location = os.path.join(*["data", "settings.json"])
settings_data = {} # Global settings data.

def _update_global_dict(new_data):
    settings_data.clear()
    settings_data.update(new_data)
    return settings_data

def load():
    """
    Returns a dictionary of the saved settings. This mutable object
    will be updated if the settings are changed. Keep a reference to
    this dict to get updates if desired.
    """
    try:
        with open(location) as settings_file:
            return _update_global_dict(json.load(settings_file))
    except FileNotFoundError:
        return None

def save(settings):
    """
    Saves provided dictionary of settings. Updates the dictionary
    returned by load() with these settings: everything that uses those
    settings will be updated with these new ones.
    """
    with open(location, "w") as settings_file:
        json.dump(settings, settings_file, indent=4)
    _update_global_dict(settings)
