import pyudev
import threading
import logging

class USBDetector():
    def __init__(self):
        thread = threading.Thread(target=self._work)
        thread.daemon = False
        thread.start()
 
    def _work(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')
        print("READY")
        self.monitor.start()
        for device in iter(self.monitor.poll, None):
            if device.sys_path[-3:].isalpha():
                if device.action == 'add':
                    print(device.sys_path[-3:] + " plugged")
                if device.action == 'remove':
                    print(device.sys_path[-3:] + " removed")

a = USBDetector() 
