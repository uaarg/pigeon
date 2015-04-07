import unittest
import os
import shutil
import time

import image

import queue as queue_module

def delete_file(location):
    try:
        os.remove(location)
    except FileNotFoundError as e:
        pass

class BaseWatcherTestCase(unittest.TestCase):
    grace_period = 0.01 # Time in seconds before the image watcher should have detected a new image

    def createFile(self, image_path):
        open(image_path, "a").close()


class WatcherTestCase(BaseWatcherTestCase):

    def setUp(self):
        self.base_directory = os.path.join(*["data", "test"])
        self.watched_directories = [os.path.join(*[self.base_directory, "watched_dir_1"]), 
                                    os.path.join(*[self.base_directory, "watched_dir_2"])]

        for watched_directory in self.watched_directories:
            os.makedirs(watched_directory, exist_ok=True)

        self.image_watcher = image.Watcher()
        self.image_watcher.setDirectory(self.watched_directories[0])
        self.image_watcher.start()


    def tearDown(self):
        self.image_watcher.stop()
        shutil.rmtree(self.base_directory)

    def getImageAndAssert(self):
        try:
            found_image = self.image_watcher.queue.get(True, self.grace_period)
        except queue_module.Empty:
            self.fail("No image was found within the allowed grace period of %s seconds." % self.grace_period)
        else:
            return found_image

    def makeFilePath(self, filename, watched_directory_index=0):
        return os.path.join(*[self.watched_directories[watched_directory_index], filename])

    def testImageAdded(self):
        """
        Tests that an image added to the watched_directory is put in 
        the queue.
        """
        self.assertTrue(self.image_watcher.queue.empty(), msg="Queue should be empty before any images are added.")
        image_path = self.makeFilePath("image1.jpg")
        self.createFile(image_path)

        found_image = self.getImageAndAssert()

        self.image_watcher.setDirectory(self.watched_directories[0])
        self.assertTrue(self.image_watcher.queue.empty(), msg="Only one image should have been added to the queue.")

        self.assertTrue(os.path.samefile(image_path, found_image.path))

    def testRandomFileAdded(self):
        """
        Test that only supported image files are added to the queue.
        """

        file_path = self.makeFilePath("debug.log")
        self.createFile(file_path)

        try:
            found_image = self.image_watcher.queue.get(True, self.grace_period)
        except queue_module.Empty:
            pass
        else:
            self.fail("Found %s after creating %s. Shouldn't have found anything since this created file isn't an image." % (found_image.path, file_path))

    def testMonitoredFolderChange(self):
        """
        Tests that the folder being monitored can be changed after
        initialization.
        """

        image1_path = self.makeFilePath("image1.jpg")
        self.createFile(image1_path)

        time.sleep(self.grace_period) # Giving the watcher time to find image1 before the watched directory is changed

        self.image_watcher.setDirectory(self.watched_directories[1])

        image2_path = self.makeFilePath("image2.jpg", watched_directory_index=1)
        self.createFile(image2_path)

        found_image_1 = self.getImageAndAssert()
        found_image_2 = self.getImageAndAssert()

        self.assertTrue(os.path.samefile(image1_path, found_image_1.path))
        self.assertTrue(os.path.samefile(image2_path, found_image_2.path))

    def testMultipleImagesAdded(self):
        """
        Tests that things still work even if lots of images are 
        added in a short amount of time.
        """
        number_of_images = 500
        image_name = "image%s.jpg"

        # Creating the image files
        for i in range(number_of_images):
            self.createFile(self.makeFilePath(image_name % i))

        # Checking that the images added to the queue match what was created
        for i in range(number_of_images):
            self.assertTrue(os.path.samefile(self.makeFilePath(image_name % i), self.getImageAndAssert().path))