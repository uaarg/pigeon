import unittest
import os

import settings

def delete_file(location):
    try:
        os.remove(location)
    except FileNotFoundError as e:
        pass

class SettingsTestCase(unittest.TestCase):
    def setUp(self):
        self.old_config = settings.load().copy() # Backup up any existing settings

    def tearDown(self):
        settings.save(self.old_config) # Restoring the old, backed up settings

    def testLoadSave(self):
        """
        Tests both load and save by saving something and then 
        loading it back.
        """

        correct_data = {"key1": "val1",
                        "key2": 3.14159,
                        "key3": [1,2,3,4],
                        "key4": True}

        settings.save(correct_data.copy())

        actual_data = settings.load()

        self.assertEqual(correct_data, actual_data)

    def testLoadNoFile(self):
        """
        If the settings file doesn't exist, loading data should return None.
        """
        delete_file(settings.location)

        data = settings.load()
        self.assertEqual(data, None)

    def testSaveNoFile(self):
        """
        Saving should work even if the file doesn't exit.
        """
        delete_file(settings.location)

        data = settings.save({"testing": True})
