station readme
=================

Usage Notes
===========
Screen layout
-------------
* The window is split into four main area:
    * All images are shown on the bottom as thumbnails in a scroll list.
    * Info and settings are shown on the left. (info not implemented yet)
    * The image currently being viewed is shown in the middle.
    * Markers are listed on the right (not implemented yet)
* You can resize all of these panes by dragging the handles that exist in between them. If made too small, the pane will dissapear: that's OK and potentially desired. Just drag the pane back out again to restore it.

Settings
--------
* Settings are loaded on startup.
* After making changes, clicking "Save" both applies the settings immediately and persists them (aka saves to disk).
* Current settings:
    * Monitor Folder: This specified the directory to be watched for new images. Can be an absolute or relative path. No error checking is done on the path yet.
    * Follow Images: Specified whether new images should be automatically shown in the main display area upon addition.

Thumbnail Area
-------------
* Click on an image to select.
* Use the left and right arrow keys to select the previous or next image.
* Selecting an image causes it to be displayed in the main image viewer.

Development Notes
=================

Conventions
-----------
* A method called run implies it doesn't return, but rather loops
  forever. A method called start will return immediately, putting
  it's looping logic into a separate thread as necessary to do so.
