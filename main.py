# TO-DO - DISPLAY NOT COMMING BACK TO MAIN THREAD AFTER DONE
#       - ADD AUTO FORMATTING OPTION AFTER DD IS DONE
import pyudev
import threading
import logging
import os
import subprocess
from subprocess import Popen, PIPE
from os import system, name
import smbus
import time
import RPi.GPIO as GPIO
from datetime import datetime
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

class Lcd_class():
  lcd_columns = 16
  lcd_rows = 2

  lcd_rs = digitalio.DigitalInOut(board.D22)
  lcd_en = digitalio.DigitalInOut(board.D17)
  lcd_d4 = digitalio.DigitalInOut(board.D25)
  lcd_d5 = digitalio.DigitalInOut(board.D24)
  lcd_d6 = digitalio.DigitalInOut(board.D23)
  lcd_d7 = digitalio.DigitalInOut(board.D18)
  
  
  # Initialise the lcd class
  global lcd
  lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
  def lcd_clear(self):
    lcd.clear()
  
  def lcd_string(self, message):
    # Send string to display
    lcd.clear()
    message = message.ljust(16," ")
    lcd.message = message

class Usbshredder():
    def __init__(self):
        self.show_lcd('USB DESTROYER\nv0.0.0.0.1 ALPHA')
        time.sleep(3)
        self.show_lcd('clear')
        thread = threading.Thread(target=self._work)
        thread.daemon = False
        thread.start()

    def button(self, block):
        global pressed
        pressed = False
        time.sleep(2)
        GPIO.setwarnings(False) # Ignore warning for now
        #GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        while True: # Run forever
          time.sleep(0.2)
          if GPIO.input(21) == GPIO.HIGH:
            try:
              if p.poll() is None: # Check if the p subprocess is running.
                pressed = True     # Button watchdog
                p.terminate()      # Terminate p subprocess
                self.show_lcd("Creating\nGPT Table")
                os.system('parted /dev/'+ block +' mklabel gpt')
                time.sleep(1)
                self.show_lcd("Creating\nPartition")
                os.system('parted /dev/' + block + ' mkpart primary 2048s 100%')
                time.sleep(1)
                self.show_lcd("Formating\nvfat partition")
                os.system('mkfs.vfat /dev/' + block + '1')
                time.sleep(1)
                self.show_lcd("DONE!\nRemove USB")
                self._running = False
            except:
              print("")

    def shred(self, block):
        self.show_lcd('clear')
        global p
        p = subprocess.Popen(["dd", "if=/dev/urandom", "of=/dev/" + block, "bs=4M", "status=progress"], stderr=subprocess.PIPE)
        #self.show_lcd(p[0])
        line = ''
        while True: # This is horrible, but it deals with the sting of the subprocess
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
                  self.show_lcd("Shredding USB\n" + ls[:-1] + "@" + sl[9] + sl[10])
                
                line = ''
                time.sleep(1)
            else:
              line = line + s
      
    def show_lcd(self, lcdstr, status = " "):
      asdf = Lcd_class()  ## DESCOMENTAR PARA USAR CON LCD

      if lcdstr == "clear":
          system('clear')
          asdf.lcd_clear()  ## DESCOMENTAR PARA USAR CON LCD
      else: 
          #print(lcdstr)
          #print(status)
          asdf.lcd_string(lcdstr)  ## DESCOMENTAR PARA USAR CON LCD

    def _work(self):
        global t0
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')
        self.show_lcd("Ready for duty\nInsert USB")
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
                    self.show_lcd("Ready for duty\n" + "Insert USB")
a = Usbshredder()
