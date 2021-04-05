# TO-DO - DISPLAY NOT COMMING BACK TO MAIN THREAD AFTER DONE
#       - ADD AUTO FORMATTING OPTION AFTER DD IS DONE
import pyudev
import threading
import logging
import os
import subprocess
import time
from subprocess import Popen, PIPE
from os import system, name
import smbus
import time
import RPi.GPIO as GPIO
import I2C_LCD_driver

class Usbshredder():
    def __init__(self):
        self.show_lcd('USB DESTROYER', 'v0.0.0.0.1 ALPHA')
        time.sleep(3)
        self.show_lcd('clear')
        thread = threading.Thread(target=self._work)
        thread.daemon = False
        thread.start()
        

    def button(self, block):
        global pressed
        pressed = False
        GPIO.setwarnings(False) # Ignore warning for now
        GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        while True: # Run forever
          time.sleep(0.2)
          if GPIO.input(40) == GPIO.HIGH:
            self.show_lcd("clear")
            try:
              if p.poll() is None: # Check if the p subprocess is running.
                pressed = True     # Button watchdog
                p.terminate()      # Terminate p subprocess
                self.show_lcd("Creating", "MSDOS Label")
                os.system('parted /dev/'+ block +' mklabel msdos')
                time.sleep(1)
                self.show_lcd("Creating", "Partition")
                os.system('parted /dev/' + block + ' mkpart primary 2048s 100%')
                time.sleep(1)
                self.show_lcd("Formatting", "as VFAT (FAT32)")
                os.system('mkfs.vfat /dev/' + block + '1')
                time.sleep(1)
                self.show_lcd("DONE!", "Remove USB")
                self._running = False
                  
            except:
              print("")

    def shred(self, block):
        self.show_lcd('clear')
        global p
        p = subprocess.Popen(["dd", "if=/dev/urandom", "of=/dev/" + block, "bs=4M", "status=progress"], stderr=subprocess.PIPE)
        #self.show_lcd(p[0])
        line = ''
        while True: # This is horrible, but it deals with the strsudo reing of the subprocess
          out = p.stderr.read(1)
          if out == '' and p.poll() != None:
            break
          if out != '':
            s = out.decode("utf-8")
            if s == '\r':
              if len(line) > 0:
                sl = line.split(" ")
                ls = sl[4] + sl[5]
                
                if p.poll() is None and not pressed: # Check if the p subprocess is running and the button haven't being pressed
                  self.show_lcd("Shredding USB", ls[:-1] + "@" + sl[9] + sl[10])
                
                line = ''
                time.sleep(1)
            else:
              line = line + s
      
    def show_lcd(self, lcdstr, status = " "):
      mylcd = I2C_LCD_driver.lcd()
      if lcdstr == "clear":
          system('clear')
          mylcd.lcd_clear() ## DESCOMENTAR PARA USAR CON LCD
      else: 
          print(lcdstr)
          print(status)
          mylcd.lcd_display_string(lcdstr, 1)  ## DESCOMENTAR PARA USAR CON LCD
          mylcd.lcd_display_string(status, 2)  ## DESCOMENTAR PARA USAR CON LCD

    def _work(self):
        global t0
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')
        self.show_lcd("Ready for duty", "Insert USB")
        self.monitor.start()
        for device in iter(self.monitor.poll, None):
            
            if device.sys_path[-3:].isalpha():
              
                if device.action == 'add':
                    self.show_lcd('clear')
                    self.show_lcd("USB Inserted")
                    time.sleep(1)
                    t0 = threading.Thread(name='t0', target=self.button, args=(device.sys_path[-3:],))
                    t0.start()
                    self.shred(device.sys_path[-3:])          

                if device.action == 'remove':
                    self.show_lcd('clear')
                    self.show_lcd("USB Removed")
                    
                    time.sleep(1)
                    self.show_lcd('clear')
                    self.show_lcd("Ready for duty", "Insert USB")
a = Usbshredder()
