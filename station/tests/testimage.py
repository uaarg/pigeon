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

class BaseTestCase(unittest.TestCase):
    source_path = os.path.join(*["tests", "data", "images"])
    source_name = "1"
    image_extension = "jpg"
    info_extension = "txt"
    source_image = os.path.join(*[source_path, source_name + os.extsep + image_extension])
    source_info = os.path.join(*[source_path, source_name + os.extsep + info_extension])

class BaseWatcherTestCase(BaseTestCase):
    grace_period = 0.01 # Time in seconds before the image watcher should have detected a new image

    def createFile(self, path, binary=True):
        """
        Creates a file at the specified path. Can be a large, binary file
        (default) or a small text file by specifying binary=False.
        """
        if binary:
            shutil.copy(self.source_image, path)
        else:
            with open(path, "a") as f:
                f.write("File created during unittest.")

    def createImageInfoPair(self, path, name):
        """
        Creates an image and associated text file at the specified path 
        with the specified name (name excludes exension).
        """
        image_path = os.path.join(*[path, name + os.extsep + self.image_extension])
        info_path = os.path.join(*[path, name + os.extsep + self.info_extension])
        shutil.copy(self.source_image, image_path)
        shutil.copy(self.source_info, info_path)
        return image_path, info_path


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
        image_path, info_path = self.createImageInfoPair(self.watched_directories[0], "1")

        found_image = self.getImageAndAssert()

        self.image_watcher.setDirectory(self.watched_directories[0])
        self.assertTrue(self.image_watcher.queue.empty(), msg="Only one image should have been added to the queue.")

        self.assertTrue(os.path.samefile(image_path, found_image.path))
        self.assertTrue(os.path.samefile(info_path, found_image.info_path))

    def testRandomFileAdded(self):
        """
        Test that only supported image files are added to the queue.
        """

        file_path = self.makeFilePath("debug.log")
        self.createFile(file_path, binary=False)

        file_path = self.makeFilePath("binary_dump.bin")
        self.createFile(file_path, binary=True)

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
        image1_path, info1_path = self.createImageInfoPair(self.watched_directories[0], "image1")

        time.sleep(self.grace_period) # Giving the watcher time to find image1 before the watched directory is changed

        self.image_watcher.setDirectory(self.watched_directories[1])

        image2_path, info2_path = self.createImageInfoPair(self.watched_directories[1], "image2")

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

        image_paths = []

        # Creating the image files
        for i in range(number_of_images):
            image_path, info_path = self.createImageInfoPair(self.watched_directories[0], str(i))
            image_paths.append(image_path)

        # Checking that the images added to the queue match what was created
        for i in range(number_of_images):
            self.assertTrue(os.path.samefile(image_paths[i], self.getImageAndAssert().path))

    def testMissingInfo(self):
        """
        Tests that an image isn't added to the queue until it's corresponding
        info file can be included with it.
        """
        file_path = self.makeFilePath("1.jpg")
        self.createFile(file_path, binary=True)

        try:
            found_image = self.image_watcher.queue.get(True, self.grace_period)
        except queue_module.Empty:
            pass
        else:
            self.fail("Found %s after creating %s. Shouldn't have found anything since this an image file was created without the corresponding info file." % (found_image.path, file_path))

class ImageTestCase(BaseTestCase):
    def setUp(self):
        class MockImage(image.Image):
            def __init__(self):
                pass

        self.image = MockImage()
        self.image.info_path = self.source_info


    def testReadImage(self):
        """
        Tests that the data in an info file can be read properly.
        """
        try:
            self.image._readInfo()
        except Exception as e:
            self.fail(msg="Exception raised while reading info image: %s" % e)

        self.assertEqual(self.image.info_data["phi"], "4.56")
        self.assertEqual(self.image.info_data["alt"], "610.75")
        self.assertEqual(self.image.info_data["utm_east"],  "345120")

    def testImageProperties(self):
        """
        Tests that the properties of an image can be prepared properly.
        """
        self.image._readInfo()
        try:
            self.image._prepareProperties()
        except Exception as e:
            self.fail(msg="Exception raised while preparing properties: %s" % e)

        self.assertAlmostEqual(self.image.plane_position.alt, 610.75)
        self.assertAlmostEqual(self.image.plane_orientation.pitch, 4.56)