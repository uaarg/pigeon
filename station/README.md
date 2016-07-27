station readme
=================

Usage Notes
===========
Screen layout
-------------
* The window is split into four main area:
    * All images are shown on the bottom as thumbnails in a scroll list.
    * UAV controls, info and some settings are shown on the left.
    * The image currently being viewed is shown in the middle.
    * Markers are listed on the right
* You can resize all of these panes by dragging the handles that exist in between them. If made too small, the pane will disappear: that's OK and potentially desired. Just drag the pane back out again to restore it. Note that resizing the thumnail area potentially has a performance impact: when increasing it's size, a large amount of disk activity might be triggered to load large images and more memory will be used. Resizing this area before any images are loaded is best since that avoids the disk activity and potentially reduces memory usage (if the area is shrunk).

Settings
--------
* Settings are loaded on startup.
* Some common settings are available in the setting area in the bottom right corner.
* All settings are available in the Settings Window. Got to "Edit" in the menu bar then "Settings".
* Making any changes applies the settings immediately and persists them (aka saves to disk).
* Current settings:
    * Feature Export Path: Specified the path where the exporters should save their file exports.
    * Follow Images: Specifies whether new images should be automatically shown in the main display area upon addition.
    * Instance Name: The name of this Pigeon instance for multi-operator support (in progress). Setting to your name makes sense.
    * Load Existing Images: Specified whether to load all images from the monitor folder on startup. Doesn't re-scan the folder if enabled: applies to the next launch.
    * Monitor Folder: Specifies the directory to be watched for new images. Can be an absolute or relative path. No error checking is done on the path yet.
    * Nominal Target Size: The expected size of features in meters. Used for automatic thumnail creating for new features.
    * Pigeon Network: the ivybus network to connect to other Pigeon instances for multi-operator support. Format is subnet:port. Ex: 127:2010 or 192.168.99:2010 etc...
    * Plane Plumbline: Specifies whether a plane icon should be drawn on the image at the location directly below the plane.
    * UAV Network: the ivybus network to connect to the onboard imaging software over. Format is subnet:port. Ex: 127:2010 or 192.168.99:2010 etc...

Thumbnail Area
--------------
* The most recently received image is always shown on the very right.
* Click on an image to select.
* Use the left and right arrow keys to select the previous or next image.
* Selecting an image causes it to be displayed in the main image viewer.

UAV Area
--------
* Info and controls for the onboard imaging software are in the top left. This requires the UAV Network setting to be set correctly in pigeon. The onboard imaging software must be running and configured properly too.

Info Area
---------
* Info is shown for both the overall system under the "State" section and the image currently being displayed, under the "Image" section.

Main Image Area
---------------
* Left click to create a marker which will be added to the Marker List on the right.
* Markers can be dragged around to change their location.
* Right click on the image to place a point down on the image. A second right click will place another point and calculate the distance/angle of the point relative to the first. Points can be dragged on creation, for dynamic distance/angle update.

Marker Area
-----------
* Select a marker from the list to have it's details be shown in the Marker Detail Area below the list.
* Make changes to any of the editable fields in the Marker Detail Area to store this information on the marker (no need to save)
* Markers in the list will appear as "(unnamed)" until a name is set for that marker.
* Markers in the list have a little image icon associated with them: this isn't finished yet and is just a taste of what's to come (that image crop will be editable)
* The Marker Detail Area also shows some information you can't edit, such as the image number the marker was created in, the geo-referenced position of the marker, and the approximate error between all identified instances of the marker.
* Just like ground control points, markers are plotted in all images using inverse geo-referencing.
* If a marker is moved in an image other than the one it was created in, that creates a new "subfeature", aka an instance of the marker.
* To add a new instance of a marker in an image where inverse geo-referencing wasn' accurate enough to already show the marker (or you just don't want to use drag and drop), simply click on "Add Subfeature" then the location in the main image where you can see that feature.

Multi-Operator
--------------
* Work has been started on multi-operator support. This means running multiple pigeon instances (usually on different computers) and having data be shared between them.
* Right now, it's basically a feature-sync mechanism. Any features created or changed by one Pigeon are sent to other instances connected to the ivybus.
* To use, configure the "Pigeon Network" setting so that the two Pigeons can talk (the default should work if they are on the same computer). Then, just start making and changing features.