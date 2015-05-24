station readme
=================

Usage Notes
===========
Screen layout
-------------
* The window is split into four main area:
    * All images are shown on the bottom as thumbnails in a scroll list.
    * Info and settings are shown on the left.
    * The image currently being viewed is shown in the middle.
    * Markers are listed on the right (not implemented yet)
* You can resize all of these panes by dragging the handles that exist in between them. If made too small, the pane will disappear: that's OK and potentially desired. Just drag the pane back out again to restore it.

Settings
--------
* Settings are loaded on startup.
* After making changes, clicking "Save" both applies the settings immediately and persists them (aka saves to disk).
* Current settings:
    * Monitor Folder: Specifies the directory to be watched for new images. Can be an absolute or relative path. No error checking is done on the path yet.
    * Follow Images: Specifies whether new images should be automatically shown in the main display area upon addition.
    * Plane Plumbline: Specifies whether a plane icon should be drawn on the image at the location directly below the plane.

Thumbnail Area
--------------
* Click on an image to select.
* Use the left and right arrow keys to select the previous or next image.
* Selecting an image causes it to be displayed in the main image viewer.

Info Area
---------
* Info is shown for both the overall system under the "State" section and the image currently being displayed, under the "Image" section.

Main Image Area
---------------
* Click on the image to geo-reference that particular point. The results are printed in the terminal for now.

Development Notes
=================

Conventions
-----------
* A method called run implies it doesn't return, but rather loops
  forever. A method called start will return immediately, putting
  it's looping logic into a separate thread as necessary to do so.
