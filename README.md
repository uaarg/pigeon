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
* Start of multi-operator functionality: features and images can be synced with
  other pigeon instances over an ivybus
* Scans QR codes from selected image (under process menu), reading up to 60 cm
  away at up to 45 degrees using a 7x7cm QR code

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

To install quickly, simply run `sudo ./install_dependencies.sh`

Manual Installation
-------------------

Pigeon is written in PyQt. It also has a few python module dependencies.
To install on Ubuntu (tested on 14.04), do:

```
sudo apt-get install python3 python3-dev
sudo apt-get install qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5
sudo apt-get install python3-shapely python3-pip
sudo apt-get install libxml2-dev libxslt1-dev
sudo apt-get install libzbar0
sudo pip3 install pyinotify pyproj pykml==0.1.0
sudo pip3 install git+https://github.com/camlee/ivy-python
sudo pip3 install requests 
sudo pip3 install Pillow pyzbar
```

See below for installing interop export functionality

SubModules
----------

## Interop 
Pigeon requires a submodule in order to communicate with the interop server at 
AUSVI SUAS Competitions. This submodule is developed by the AUVSI competition 
comitee and contains the modules we use to export data to the interop server

To install the submodule, run

```
git submodule init
git submodule update
```

Run `install_interop_export.sh` in the modules folder to install the client library.
Or see the getting started page [here](https://github.com/auvsi-suas/interop#getting-started) 
for installation instructions.

Below lists the pip3 modules needed by the interop client library:
```
libxml2-dev 
libxslt-dev 
protobuf-compiler 
python 
python-dev 
python-lxml 
python-nose 
python-pip 
python-pyproj 
python-virtualenv 
python3 
python3-dev 
python3-nose 
python3-pip 
python3-pyproj 
python3-lxml 
sudo 
```

Running the Ground Station
--------------------------
Simply run `./run.sh`

See the README in the station directory for usage notes.


Running the Tests
-------------
Run `run_tests.sh` in the root of the project

To run a particular test, test case, or module, add it as an argument. Ex:
`run_tests.sh testimage.WatcherTestCase.testImageAdded`


Installation 
------------

If you'd like to create a launcher for Pigeon that you can ex. put
on the desktop or access through your application launcher, from
the station directory, do:

`scons install`

You can then launch the program through the GUI. Note that this
creates a launcher pointing to that station folder: it doesn't
install binaries to a central location. So any code changes or
git pulling you do will be reflected instantly, and moving your
git repository will break things.

To uninstall, do:

`scons install -c`


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


Security
--------
A brief overview of some security considerations of Pigeon, and in particular
station.py are listed here:
* First, the obvious: station.py launches an HTTP server which serves up the
  image and info files imported into Pigeon. This data should not be considered
  private. Also, features and associated meta-data are made available on the
  network so this data is effectively public too.
* Given the significant amount of network communication needed for some
  of the features (in particular, multi-operator), there is a significant
  attack area.
* Any vulnerabilities in the ivybus library or Python's built-in http server
  (http.server.HTTPServer) would be exposed. Remotely received data is
  also unpickled, albeit with a whitelist of allowed classes. There's two
  potential failure points here:
  1. The pickling protocal has a way to avoid this whitelist.
  2. A whitelisted class exposes more than it should (ex. keeping a reference
     to the os module).
* Potential exploits include:
  * Remote code execution
  * Exposing private information such as local files
  * Privilege escalation.
* Anybody on the specified network can attempt exploits. By default, this
  is just localhost, so other programs running on this maching could attempt
  privilege escalation. When this network setting is changed, other machines
  can attempt exploits.
* The locally saved settings.json file provides a significant amount of control
  over how station.py behaves. Anyone with permission to edit this (ex. another
  use in the group depending on file permissions) could change the monitored
  folder to somewhere that they don't already have access to, etc...
* Denial of service: there's no rate limiting, so this kind of attack should
  be very easy to perform.
* Although the developers have thought about security and attempted to avoid
  any vulnerabilities, there has been no security audit or other testing so
  the answer to "is pigeon safe" is: ¯\_(ツ)_/¯
* Obscurity: this is huge source of protection. At the time of writting this,
  Pigeon is closed source and not widely used.
* Mitigation:
  * Don't run as root.
  * Ideally, only open up to trusted networks (ex. behind a firewall, etc...).
  * All network communication should be logged so investigate any suspicious
    behaviour.
  * Ensure the file permissions of settings.json are appropriate for your
    environment.


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
* Documentation is in the doc folder. .odg files can be opened in
  LibreOffice Draw.
* Add to the wiki in the repository. We need more documentation!


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
