pigeon readme
=============
Pigeon is UAARG's ground station imaging software. It is used to analyze
images received from the aircraft through a combination of manual and
automatic processes. The ultimate goal is to quickly provide accurate 
information about points of interest found on the ground. 

Implemented Features:
---------------------
* Monitors a folder for images added to it
* Displays a scrollable list of images
* Displays a main image as selected from the scrollable list
* Settings area for specifying and saving settings

Future Features:
----------------
* See the bitbucket issue tracker for desired features.


Input
-----
* Some configuration (ex. Camera specs, folder to watch)
* Image files in a single folder as specified in the configuration
  (usually, expect these to be added a few at a time during the flight)
* Image info files. Also in a folder as specified in the configuration
  There should be an info file for each image: the two will be imported 
  together. 
  Info file fields:
  * (to be added later)
* Data entered into UI by human operator (ex. Marker locations)

Output
------
* UI for manually viewing images
* Marker list as a csv file


Installation
------------
Pigeon is written in PyQt. It also has a few python module dependencies.
To install on Ubuntu (tested on 14.04), do:

sudo apt-get install python3 python3-dev qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5 python3-shapely python3-pyproj python3-pip && sudo pip3 install pyinotify


Running the ground station
--------------------------
From the station directory, do:
python3 station.py

See the README in the station directory for usage notes.

uavsimulator.py in the utils directory is useful for creating images periodically
instead of running the onboard software. 


Run the tests
-------------
From the station directory, do:
python3 test.py


Contributing
------------
A few notes about contributing:

* Please feel free to ask any question at any time.
* Please feel free to ask for help.
* Please follow pep8 for style: https://www.python.org/dev/peps/pep-0008/
* Please run the tests and make sure they pass before commiting anything:
  if the tests don't pass, it means you broke something somehow (or, someone 
  else commited a break, in which case find who and get them to fix it).
