import unittest
import os
import shutil
import json

import settings

def delete_file(location):
    try:
        os.remove(location)
    except FileNotFoundError as e:
        pass

class SettingsTestCase(unittest.TestCase):
    settings_backup_path = os.path.join(*["data", "settings_backup_for_unittests.json"])

    def setUp(self):
        # Make sure that file exists first
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
        }
        with open(settings.location, 'w+') as settings_file:
            settings_file.write(json.dumps(default_settings_data))

        # Backup
        shutil.copy(settings.location, self.settings_backup_path)

    def tearDown(self):
        shutil.copy(self.settings_backup_path, settings.location)
        delete_file(self.settings_backup_path)

    def testLoadSave(self):
        """
        Tests both load and save by saving something and then
        loading it back.
        """
        for value in [True, False]:
            correct_data = {"Plane Plumbline": value}
            settings.save(correct_data.copy())
            actual_data = settings.load()
            self.assertEqual(value, actual_data.get("Plane Plumbline"))

    def testLoadNoFile(self):
        """
        If the settings file doesn't exist, loading data should return the defaults and create a new settings file.
        """
        delete_file(settings.location)

        data = settings.load()

        # Assert default data and settings file exists
        self.assertNotEqual(data.get("Plane Plumbline"), None)
        self.assertTrue(os.path.isfile(settings.location))

    def testSaveNoFile(self):
        """
        Saving should work even if the file doesn't exit.
        """
        delete_file(settings.location)

        data = settings.save({"testing": True})
