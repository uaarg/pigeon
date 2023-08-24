pigeon readme
=============
Pigeon is UAARG's ground station imaging software. It is used to analyze
images received from the aircraft through a combination of manual and
automatic processes. The ultimate goal is to quickly provide accurate
information about points of interest found on the ground.


Installation & Setup
--------------------

Make sure you have python >=3.10 installed on your machine and that it is in
your `PATH`.

Pigeon is written in PyQt. Which means that on a non-Windows system you may
have to ensure some pyqt5 packages are installed. For an Ubuntu/Debian system,
these are:

```sh
sudo apt-get install qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5
```

3. Then install python dependencies located in `requirements.txt`:

```sh
# Setup the python virtual environment (do this once)
python3 -m venv venv

# Activate the virtual environment (different for each OS)
source ./venv/bin/activate  # (MacOS/Linux/...) unix shell
venv\Scripts\activate.bat   # (Windows) cmd.exe
venv\Scripts\Activate.ps1   # (Windoes) PowerShell

# Install dependencies (do this at setup and/or when requirements.txt changes)
pip install -r requirements.txt.
```


Running Pidgeon
---------------

Before running the GUI, start a shell session in the repo root. Activate the
virtual environment. Then run the following in the station folder:

```sh
python3 station.py
```


Running the Tests
-------------

TODO: we no longer have tests. I, Aidan, am working on adding these.


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


Code Conventions
----------------
* A method called run implies it doesn't return, but rather loops
  forever. A method called start will return immediately, putting
  it's looping logic into a separate thread as necessary to do so.
* When dealing with filepaths, make sure to not to hardcode the
  directory separators character (/) because it's platform specific.
  Instead, use the cross-platform tools in os.path module such as
  os.path.join().  (TODO: we should start using pathlib)
