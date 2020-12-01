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
import shutil

class Lcd_class():
  # Define some device parameters
  I2C_ADDR  = 0x27 # I2C device address
  LCD_WIDTH = 16   # Maximum characters per line

  # Define some device constants
  LCD_CHR = 1 # Mode - Sending data
  LCD_CMD = 0 # Mode - Sending command

  LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
  LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
  #LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
  #LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

  #LCD_BACKLIGHT  = 0x08  # On
  LCD_BACKLIGHT = 0x00  # Off

  ENABLE = 0b00000100 # Enable bit

  # Timing constants
  E_PULSE = 0.0005
  E_DELAY = 0.0005
  bus = smbus.SMBus(1) ## DESCOMENTAR PARA USAR CON LCD

  def __init__(self):
    self.lcd_byte(0x33,Lcd_class.LCD_CMD) # 110011 Initialise
    self.lcd_byte(0x32,Lcd_class.LCD_CMD) # 110010 Initialise
    self.lcd_byte(0x06,Lcd_class.LCD_CMD) # 000110 Cursor move direction
    self.lcd_byte(0x0C,Lcd_class.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
    self.lcd_byte(0x28,Lcd_class.LCD_CMD) # 101000 Data length, number of lines, font size
    self.lcd_byte(0x01,Lcd_class.LCD_CMD) # 000001 Clear display
    time.sleep(Lcd_class.E_DELAY) 

  def lcd_clear(self):
    self.lcd_byte(0x01,Lcd_class.LCD_CMD)
  
  def lcd_byte(self, bits, mode):
    bits_high = mode | (bits & 0xF0) | Lcd_class.LCD_BACKLIGHT
    bits_low = mode | ((bits<<4) & 0xF0) | Lcd_class.LCD_BACKLIGHT

    # High bits
    Lcd_class.bus.write_byte(Lcd_class.I2C_ADDR, bits_high)
    self.lcd_toggle_enable(bits_high)

    # Low bits
    Lcd_class.bus.write_byte(Lcd_class.I2C_ADDR, bits_low)
    self.lcd_toggle_enable(bits_low)

  def lcd_toggle_enable(self, bits):
    # Toggle enable
    time.sleep(Lcd_class.E_DELAY)
    self.bus.write_byte(Lcd_class.I2C_ADDR, (bits | Lcd_class.ENABLE))
    time.sleep(Lcd_class.E_PULSE)
    self.bus.write_byte(Lcd_class.I2C_ADDR,(bits & Lcd_class.ENABLE))
    time.sleep(Lcd_class.E_DELAY)

  def lcd_string(self, message,line):
    # Send string to display
    message = message.ljust(Lcd_class.LCD_WIDTH," ")
    self.lcd_byte(line, Lcd_class.LCD_CMD)
    for i in range(Lcd_class.LCD_WIDTH):
      self.lcd_byte(ord(message[i]),Lcd_class.LCD_CHR)

class Usbshredder():
    def __init__(self):
        self.show_lcd('clear')
        thread = threading.Thread(target=self._work)
        thread.daemon = False
        thread.start()

    def button(self, block):
        global pressed
        pressed = False
        GPIO.setwarnings(False) # Ignore warning for now
        GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        while True: # Run forever
          time.sleep(0.2)
          if GPIO.input(16) == GPIO.HIGH:
            try:
              if p.poll() is None: # Check if the p subprocess is running.
                pressed = True     # Button watchdog
                p.terminate()      # Terminate de p subprocess
                self.show_lcd("Creating", "GPT Table")
                os.system('parted /dev/'+ block +' mklabel gpt')
                time.sleep(1)
                self.show_lcd("Creating", "Partition")
                os.system('parted /dev/' + block + ' mkpart primary 2048s 100%')
                time.sleep(1)
                self.show_lcd("Formating", "vfat partition")
                os.system('mkfs.vfat /dev/' + block + '1')
                time.sleep(1)
                self.show_lcd("DONE!", "Remove USB")
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
                  self.show_lcd("Shredding USB...", ls[:-1] + "@" + sl[9] + sl[10])
                
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
            print(lcdstr)
            print(status)
            asdf.lcd_string(lcdstr, asdf.LCD_LINE_1)  ## DESCOMENTAR PARA USAR CON LCD
            asdf.lcd_string(status, asdf.LCD_LINE_2)  ## DESCOMENTAR PARA USAR CON LCD

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
                    self.show_lcd("USB Inserted", device.sys_path[-3:])
                    time.sleep(1)
                    t0 = threading.Thread(name='t0', target=self.button, args=(device.sys_path[-3:],))
                    t0.start()
                    self.shred(device.sys_path[-3:])          

                if device.action == 'remove':
                    self.show_lcd('clear')
                    self.show_lcd("USB Removed", device.sys_path[-3:])
                    
                    time.sleep(1)
                    self.show_lcd('clear')
                    self.show_lcd("READY")
a = Usbshredder()
