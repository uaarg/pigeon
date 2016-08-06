import unittest
import os
import shutil

import settings

def delete_file(location):
    try:
        os.remove(location)
    except FileNotFoundError as e:
        pass

class SettingsTestCase(unittest.TestCase):
    settings_backup_path = os.path.join(*["data", "settings_backup_for_unittests.json"])

    def setUp(self):
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
        If the settings file doesn't exist, loading data should return the defaults.
        """
        delete_file(settings.location)

        data = settings.load()
        self.assertNotEqual(data.get("Plane Plumbline"), None)

    def testSaveNoFile(self):
        """
        Saving should work even if the file doesn't exit.
        """
        delete_file(settings.location)

        data = settings.save({"testing": True})
