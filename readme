pigeon readme
=============
Pigeon is UAARG's ground station imaging software.
Currently, it is only intended to display images, read their metadata, allow a user to place markers on images, and save the marker locations.
For the onboard imaging software, see Waldo.

Configuration
-------------
Pigeon is designed to work with the following setup:

Onboard
	* Paparazzi UAV
	
Ground station computer
	* Set up as FTP server
	* Images and data stored by Waldo in a single directory. 

Installation
------------
Pigeon is written in PyQt.
For a list of dependencies required by pigeon, see docs/dependencies.

Features
--------
Not all of these features have been implemented yet.

Critical
* Load image metadata.
* Display image and allow user to place markers of targets on image.
* Load and save persistent target markers.
* Read and load configuration data - camera lens properties, default directories, etc...

Planned
* Present a list of images and allow user to choose between images.
* Present images sequentially in different ways - by time, proximity to ground station, etc...


Important variables
-------------------
phi
Roll. +phi = roll right.

psi
Yaw. +psi = yaw right.

theta
Pitch. +theta = pitch up.

altitude
For imaging purposes, we care about the absolute altitude above the ground terrain.
This is absolute altitude above ground level (AGL). This can also be referred to as "height."
[Paparazzi Wiki article on altitude definitions](http://wiki.paparazziuav.org/wiki/Demystified/Altitude_and_Height)

GPS:altitude
ESTIMATOR:z-estimator

ground altitude: set in flightplan?

