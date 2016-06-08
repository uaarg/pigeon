import requests
import ast
from time import time
import threading

from geo import Position

baseurl = "http://localhost:8000"
username = "testuser"
password = "testpass"


class InteropClient:

    def sendData(self, rawdata):
        self.rawdata = rawdata
        self.interopTH = threading.Thread(target = self.runner)
        self.interopTH.start()

    def runner(self):
        self.interoplink = Connection()
        for eachtarget in self.rawdata:
            if eachtarget.feature.data["Export"] == True: # To be sure we only export things we want to
                targ = {'type':str(eachtarget.feature.data["Name"]),'Latitude':float(eachtarget.feature.position.lat), 'Longitude':float(eachtarget.feature.position.lon),
                        'Orientation':str(eachtarget.feature.data["Orientation"]),'Shape':str(eachtarget.feature.data["Shape"]), 'Background_Color':str(eachtarget.feature.data["Background_Color"]), 
                        'Alphanumeric':str(eachtarget.feature.data["Alphanumeric"]),'Alphanumeric_Color':str(eachtarget.feature.data["Alphanumeric_Color"])}
        #     self.interoplink.updatetelemetry(targ, img) # Commented for testing
                print(targ)

            print("completed: exiting server")






class Connection:
    def __init__(self):
        self.loginsucess = False
        self.s = requests.Session()
        self.lasttele = 0
        data = {"username": username, "password": password}
        loginurl = "/api/login"
        try:
            self.login = self.s.post(baseurl + loginurl, data=data)
            self.loginsucess = True
            pass
        except Exception as e:
            print("Failed to login to interop server")
            pass

    def getobstacleinfo(self):
        ob = self.s.get(baseurl + "/api/obstacles")
        objects = ast.literal_eval(ob.text)
        return objects

    def updatetelemetry(self, tele):
        tl = self.s.post(baseurl + "/api/telemetry", tele)
        print(tl.status_code)

    def updatetargets(self, targ, img):
        tl = self.s.post(baseurl + "/api/targets", targ)
        print(tl.status_code)
        files = {'media': open('test.jpg', 'rb')}
        res = self.s.post(baseurl + "/api/targets/" + str(tl.id) + "/image", img)
        return tl.id #need to edit this for what it actually is
