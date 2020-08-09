import pyudev
import threading
import logging
import os
import subprocess
import time
from os import system, name 
class usbshredder():
    def __init__(self):
        self.show_lcd('clear')
        thread = threading.Thread(target=self._work)
        thread.daemon = False
        thread.start()
    def shred(self, block):
        self.show_lcd('clear')
        self.show_lcd("Shredding /dev/" + block)
        p = subprocess.Popen(["dd", "if=/dev/urandom", "of=/dev/" + block, "bs=4M", "status=progress"])
    def show_lcd(self, lcdstr):
        if lcdstr == "clear":
            system('clear')
        else: 
            print(lcdstr)
    def _work(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')
        self.show_lcd("READY")
        self.monitor.start()
        for device in iter(self.monitor.poll, None):
            if device.sys_path[-3:].isalpha():
                if device.action == 'add':
                    self.show_lcd('clear')
                    self.show_lcd("USB block " + device.sys_path[-3:] + " plugged in")
                    time.sleep(2)
                    self.shred(device.sys_path[-3:])          

                if device.action == 'remove':
                    self.show_lcd("\nUSB block " + device.sys_path[-3:] + " removed")
                    p2 = subprocess.Popen(["killall", "dd"])
                    time.sleep(2)
                    self.show_lcd('clear')
                    self.show_lcd("READY")
a = usbshredder()
