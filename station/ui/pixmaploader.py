import logging
from PyQt5 import QtCore, QtGui

logger = logging.getLogger(__name__)

class PixmapLoader:
    """
    Class for efficiently loading and displaying images.
    Handles loading this mage file and providing a pixmap at the
    requested size. Tries to optimize performance by balancing
    memory usage and disk access.
    """
    def __init__(self, image_path):
        self.image_path = image_path
        self.pixmap = None # This is where the pixmap is cached in memory
        self.image_width = None
        self.image_height = None
        self.image_size = None

        self.hold_original = False # A hint indicating the the original image should be held.
        self.used_sizes = []
            # A history of sizes of the pixamp used; a hint for what sizes to potentially keep when freeing memory.
            # Each entry is a tuple, with the second element being the requested size and the first the used size.
            # (they are likley different because getPixmapForSize will keep the original pixmap's aspect ratio)

        self.maximum_megabytes_to_safely_keep = 1
            # Pixmaps under this size (in MB) will be kept in memory to avoid raving to re-load from disk.
            # Although you probably don't need to change it, if you want to tune things:
            #   For a given number of images:
            #     * If your computer is running out of memory, decrease this.
            #     * If you experience lag while performing operations that result in a new image being displayed somewhere,
            #       and your computer has enough memroy, increase this.
            #
            #   Typical numbers are likely: 1000 images * 1 MB/image (this number above) = 1 GB

        self.slightly_large_size_factor = 2

    def getPixmapForSize(self, size):
        """
        Returns a pixmap for the requested size. This is the most
        important method of this class.
        May or may not have to load or re-load the image file
        depending on whether optimizeMemory() has been called
        and it's behaviour.
        If the provided size is None, returns the original pixmap.
        """
        if not size:
            size = QtCore.QSize(self.image_width, self.image_height)
        self._requireLoad()
        if not self.pixmap or ((size.width() > self.pixmap.width() and size.height() > self.pixmap.height()) and (self.pixmap.width() < self.image_width or self.pixmap.height() < self.image_height)):
            logger.debug("Performing load to get bigger pixmap (have: %s need: %s, %s)" % ("%s, %s" % (self.pixmap.width(), self.pixmap.height()) if self.pixmap else None, size.width(), size.height()))
            self._loadOriginalPixmap()
        pixmap = self.pixmap.scaled(size, QtCore.Qt.KeepAspectRatio)
        self.used_sizes.append((pixmap.size(), size))
        return pixmap # Note that this returned pixmap is now owned by the caller: PixmapLoader isn't responsible for freeing that memory (and in fact can't)

    def width(self):
        """
        Returns the width of the image.
        """
        self._requireLoad()
        return self.image_width

    def height(self):
        """
        Returns the height of the image.
        """
        self._requireLoad()
        return self.image_height

    def size(self):
        """
        Returns the size of the image.
        """
        self._requireLoad()
        return self.image_size

    def holdOriginal(self):
        """
        Marks that the largest sized pixmap should be kept in memory.
        """
        self.hold_original = True

    def freeOriginal(self):
        """
        Marks that the pixmap can be shrunk to save memory
        (this is the default until holdOriginal() is called).
        """
        self.hold_original = False

    def optimizeMemory(self, might_need_a_bit_bigger=True):
        """
        Tries to free memory used by the pixmap. Doesn't necessarily
        go all out though: might keep the pixmap or a scaled down
        version in memory. Call this after getPixmapForSize() to
        save as much memory as possible.
        """
        # Actual memory freeing occurs whenever self.pixmap is set to a new value
        # in the code below: once this is done, the old object is not referenced
        # by anything and so gets cleaned up by Python's garbage collector (in
        # CPython, this happens immediately)

        if self.pixmap and not self.hold_original:
            for size, requested_size in self._used_sizes_largest_to_smallest():

                # Keeping a small version of the pixmap if something used it (because it might use it again).
                if might_need_a_bit_bigger:
                    slightly_large_size = size * self.slightly_large_size_factor
                    if slightly_large_size.width() <= self.pixmap.width() and slightly_large_size.height() <= self.pixmap.height() and self._estimatePixmapMemory(slightly_large_size, self.pixmap.depth()) < self.maximum_megabytes_to_safely_keep:
                        self.pixmap = self.pixmap.scaled(slightly_large_size, QtCore.Qt.KeepAspectRatio)
                        break

                if size.width() <= self.pixmap.width() and size.height() <= self.pixmap.height() and self._estimatePixmapMemory(size, self.pixmap.depth()) < self.maximum_megabytes_to_safely_keep:
                    self.pixmap = self.pixmap.scaled(requested_size, QtCore.Qt.KeepAspectRatio) # Using the actual, requested size to ensure the exact same scaling is performed as before: don't want to be off by even 1 pixel
                    break
            else:
                if self.pixmap.width() == self.image_width and self.pixmap.height() == self.image_height:
                    logger.debug("In PixmapLoader.optimizeMemory(), completely clearing out pixmap to reduce memory usage.")
                    self.pixmap = None
                else:
                    pass
        # if self.pixmap:
        #     logger.debug("In PixmapLoader.optimizeMemory(), keeping size %s, %s at %.2f MB" % (self.pixmap.width(), self.pixmap.height(), self._estimatePixmapMemory(self.pixmap.size(), self.pixmap.depth())))

    def _requireLoad(self):
        """
        Performs the initial read of the image, if necessary.
        """
        if not self.image_width or not self.image_height:
            self._loadOriginalPixmap()

    def _loadOriginalPixmap(self):
        self.pixmap = QtGui.QPixmap(self.image_path)
        if self.pixmap.isNull():
            self.pixmap = None
            raise(ValueError("Failed to load image at %s" % self.image_path))
        self.image_width = self.pixmap.width()
        self.image_height = self.pixmap.height()

    def _estimatePixmapMemory(self, size, depth):
        """
        Returns an estimate of the memory used by a pixmap of the
        provided size and depth in MegaBytes (MB).
        """
        # Calculation from https://forum.qt.io/topic/4876/how-much-memory/5
        # Measured too and seems accurate enough.
        return size.width() * size.height() * depth / 1024 / 1024 / 8

    def _used_sizes_largest_to_smallest(self):
        # Assuming sizes all have the same aspect ratio, so it doesn't matter if we sort using width or height: so picking one:
        self.used_sizes.sort(key=lambda item: item[0].width(), reverse=True)
        return self.used_sizes