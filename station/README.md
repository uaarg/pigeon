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
    * Markers are listed on the right
* You can resize all of these panes by dragging the handles that exist in between them. If made too small, the pane will disappear: that's OK and potentially desired. Just drag the pane back out again to restore it. Note that resizing the thumnail area potentially has a performance impact: when increasing it's size, a large amount of disk activity might be triggered to load large images and more memory will be used. Resizing this area before any images are loaded is best since that avoids the disk activity and potentially reduces memory usage (if the area is shrunk).

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
* The most recently received image is always shown on the very right.
* Click on an image to select.
* Use the left and right arrow keys to select the previous or next image.
* Selecting an image causes it to be displayed in the main image viewer.

Info Area
---------
* Info is shown for both the overall system under the "State" section and the image currently being displayed, under the "Image" section.

Main Image Area
---------------
* Right click on the image to geo-reference that particular point and have the results printed in the terminal.
* Left click to create a marker which will be added to the Marker List on the right.
* Markers can be dragged around to change their location.

Marker Area
----------------
* Select a marker from the list to have it's details be shown in the Marker Detail Area below the list.
* Make changes to any of the editable fields in the Marker Detail Area to store this information on the marker (no need to save)
* Markers in the list will appear as "(unnamed)" until a name is set for that marker.
* Markers in the list have a little image icon associated with them: this isn't finished yet and is just a taste of what's to come (that image crop will be editable and bigger)
* The Marker Detail Area also shows some information you can't edit, such as the image number the marker was created in and the geo-referenced position of the marker
* Just like ground control points, markers are plotted in all images using inverse geo-referencing.