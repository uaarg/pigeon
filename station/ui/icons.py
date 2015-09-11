"""
Centralized list of icons.
"""
import os

airplane = os.path.join(*["data", "icons", "airplane.png"])
x = os.path.join(*["data", "icons", "x.png"])
flag = os.path.join(*["data", "icons", "flag.png"])
marker = os.path.join(*["data", "icons", "marker.png"])

name_map = {"marker": marker,
            "flag": flag,
            "x": x}