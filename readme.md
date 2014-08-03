pigeon readme [ ![Codeship Status for odeke-em/pigeon](https://www.codeship.io/projects/2168d5b0-fd85-0131-3861-7ac8d6a30f22/status?branch=master)](https://www.codeship.io/projects/29444)
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

Running the ground station
--------------------------
For commandline arguments:
        Provide the address on which to connect to the DB provided by restAssured[See docs/dependencies]
        
          + python station.py -p 8000 -i http://127.0.0.1
            which is equivalent to 
          + python station.py --port 8000 --ip http://127.0.0.1

        For help with the arguments:
            python station.py --help
                Usage: station.py [options]

                Options:
                    -h, --help            show this help message and exit
                    -i IP, --ip=IP        Port server is on
                    -p PORT, --port=PORT  IP address db connects to
                    -e, --eavsdropping    Turn on eavsdropping 

                * eavsdropping enables the ground station to become a mirror
                  of snapshots of the database ie only synced data will be persistent
