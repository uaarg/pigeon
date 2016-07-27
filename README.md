pigeon readme
=============
Pigeon is UAARG's ground station imaging software. It is used to analyze
images received from the aircraft through a combination of manual and
automatic processes. The ultimate goal is to quickly provide accurate
information about points of interest found on the ground.

Implemented Features:
---------------------
* Imports images that exist in the target folder on startup
* Monitors the folder for new images added to it
* Displays a scrollable list of images
* Displays a main image as selected from the scrollable list
* Settings area for specifying and saving common settings
* Settings Window for specifying and saving all settings (under the Edit menu)
* Displays program state and currently viewed image info in an information area
* Plots pre-set ground control points in images by doing inverse geo-referencing
* Right click on the main image to have the lat/lon printed in the terminal
* Left click on the main image to create a new marker
* Created markers are shown in a list on the right and can be edited in the
  marker detail area below this list
* Various Export options under the Export menu
* Start of multi-operator functionality: features can be synced with other
  pigeon instances over an ivybus

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
  * Take a look at Image._prepareProperties() in image/image.py for the
    list of required fields.
* Data entered into UI by human operator (ex. Marker locations)
* (optional) Ground Control Points in data/ground_control_points.json

Output
------
* UI for manually viewing images
* Marker list as a csv file (Exporting)


Installation
------------
Pigeon is written in PyQt. It also has a few python module dependencies.
To install on Ubuntu (tested on 14.04), do:

```
sudo apt-get install python3 python3-dev
sudo apt-get install qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5
sudo apt-get install python3-shapely python3-pip
sudo apt-get install libxml2-dev libxslt1-dev
sudo pip3 install pyinotify pyproj pykml
sudo pip3 install git+https://github.com/camlee/ivy-python
sudo pip3 install requests
```


Running the Ground Station
--------------------------
From the station directory, do:
python3 station.py

See the README in the station directory for usage notes.


Running the Tests
-------------
From the station directory, do:
python3 test.py


Installation
-----------
If you'd like to create a launcher for Pigeon that you can ex. put
on the desktop or access through your application launcher, from
the station directory, do:
scons install

You can then launch the program through the GUI. Note that this
creates a launcher pointing to that station folder: it doesn't
install binaries to a central location. So any code changes or
git pulling you do will be reflected instantly, and moving your
git repository will break things.

To uninstall, do:
scons install -c


Utilities
---------
Various utility programs exist in the utils directory. They are
summarized here. They each take command line arguments for specifying
options. Call each program with --help argument to get usage info
and see all the options.
* uavsimulator.py: useful for creating images periodically instead
  of running the onboard software. Note that station now requires
  images to exist during it's entire operation so use uavsimulator
  with the --wait argument or don't stop it until station is closed.
* images2kml.py: useful for visualizing images and metadata in
  Google Earth. Creates a KML file for one or more input images that
  plots the plane location, image outline, image overlay, field of
  view, etc... (use command line arguments to specify what you want).


Contributing
------------
A few notes about contributing:

* Please feel free to ask any question at any time.
* Please feel free to ask for help.
* Please follow pep8 for style: https://www.python.org/dev/peps/pep-0008/
* Please run the tests and make sure they pass before commiting
  anything: if the tests don't pass, it means you broke something
  somehow (or, someone else commited a break, in which case find who
  and get them to fix it).


Code Conventions
----------------
* A method called run implies it doesn't return, but rather loops
  forever. A method called start will return immediately, putting
  it's looping logic into a separate thread as necessary to do so.
* Utilities can import the station module to leverage existing code
  and avoid repetition. So When writting utilities, feel free to
  make enhancements to classes in station when it makes sense, even
  if they are only used by your utility for now (ex. addding a new
  method to Image to return the area of ground it can see).
* When dealing with filepaths, make sure to not to hardcode the
  directory separators character (/) because it's platform specific.
  Instead, use the cross-platform tools in os.path module such as
  os.path.join().
