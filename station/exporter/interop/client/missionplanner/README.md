# SUAS Mission Planner Integration

The `auvsi_suas.py` script provides Mission Planner integration to upload
telemetry to the interoperability server. Follow the
[Mission Planner Guides](http://ardupilot.org/planner/docs/using-python-scripts-in-mission-planner.html)
to launch the script.

The script uses the interoperability client library provided in this repo. The
script must be modified to add the library to the Python path. That is, add a
line like:

```
sys.path.append('c:\path\to\lib')
```

You will also need to modify the values for interoperabilitiy server URL, login
username, and login password.
