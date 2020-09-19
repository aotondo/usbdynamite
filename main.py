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

class Lcd_class():
  # Define some device parameters
  I2C_ADDR  = 0x27 # I2C device address
  LCD_WIDTH = 16   # Maximum characters per line

  # Define some device constants
  LCD_CHR = 1 # Mode - Sending data
  LCD_CMD = 0 # Mode - Sending command

  LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
  LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
  LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
  LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

  #LCD_BACKLIGHT  = 0x08  # On
  LCD_BACKLIGHT = 0x00  # Off

  ENABLE = 0b00000100 # Enable bit

  # Timing constants
  E_PULSE = 0.0005
  E_DELAY = 0.0005
  bus = smbus.SMBus(1)

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

    def shred(self, block):
        self.show_lcd('clear')
        p = subprocess.Popen(["dd", "if=/dev/urandom", "of=/dev/" + block, "bs=4M", "status=progress"], stderr=subprocess.PIPE)
        #self.show_lcd(p[0])
        line = ''
        while True:
          out = p.stderr.read(1)
          if out == '' and p.poll() != None:
            break
          if out != '':
            s = out.decode("utf-8")
            if s == '\r':
              if len(line) > 0:
                
                sl = line.split(" ")
                print(sl)
                #print len(line), line
                ls = sl[4] + sl[5]
                self.show_lcd("Shredding USB...", ls[:-1] + "@" + sl[9] + sl[10])
                line = ''
            else:
              line = line + s

    def show_lcd(self, lcdstr, status = " "):
        asdf = Lcd_class()
        if lcdstr == "clear":
            system('clear')
            asdf.lcd_clear()
        else: 
            print(lcdstr)
            print(status)
            asdf.lcd_string(lcdstr, asdf.LCD_LINE_1)
            asdf.lcd_string(status, asdf.LCD_LINE_2)

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
                    self.show_lcd("Inserted:", device.sys_path[-3:])
                    time.sleep(1)
                    self.shred(device.sys_path[-3:])          

                if device.action == 'remove':
                    self.show_lcd('clear')
                    self.show_lcd("Removed:", device.sys_path[-3:])
                    subprocess.Popen(["killall", "dd"], stdout=PIPE)
                    time.sleep(1)
                    self.show_lcd('clear')
                    self.show_lcd("READY")
a = Usbshredder()
