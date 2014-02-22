"""
Watches the given directory for image/text data.
Depends on the pyinotify library, linux-only.
"""

def directory_scanner(DIR_PATH):
    import pyinotify
    
    wm = pyinotify.WatchManager() # new WatchManager
    notifier = pyinotify.Notifier(wm) # make a notifier associated with the WatchManager
    event_mask = pyinotify.IN_CREATE # Choose which events to watch for
    
    # Define the event handler class
    class EventHandler(pyinotify.ProcessEvent):
        # Note that for handling EVENT_TYPE, process_EVENT_TYPE must be called
        def process_IN_CREATE(self, event):
            print ("Creating:", event.pathname)

    # Create main event handler
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(DIR_PATH, event_mask, rec=True) # Add a new watch for events in mask
    notifier.loop() # loop and handle events

if __name__ == "__main__":
    DIR_PATH = "./data/"
    print("Scanning directory %s" %(DIR_PATH))
    directory_scanner(DIR_PATH)
