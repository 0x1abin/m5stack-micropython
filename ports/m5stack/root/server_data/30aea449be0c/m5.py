
# This file is part of MicroPython M5Stack package
# Copyright (c) 2017 Mika Tuupola
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/tuupola/micropython-m5stacj

from micropython import const
from machine import Pin, PWM
import idf9341 as lcd
import time

_BUTTON_A_PIN = const(39)
_BUTTON_B_PIN = const(38)
_BUTTON_C_PIN = const(37)
_SPEAKER_PIN = const(25)
# TFT_LED_PIN = const(32)
# TFT_DC_PIN = const(27)
# TFT_CS_PIN = const(14)
# TFT_MOSI_PIN = const(23)
# TFT_CLK_PIN = const(18)
# TFT_RST_PIN = const(33)
# TFT_MISO_PIN = const(19)


class M5Stack:
  def __init__(self):
    print("M5Stack Start.")
    lcd.init()

class Button:
  def __init__(self, pin, callback=None, trigger=Pin.IRQ_FALLING):
    if callback is None:
        callback = self._callback
    self.pin = Pin(pin)
    self.pin.init(self.pin.IN)
    self.pin.irq(trigger=trigger, handler=callback)

  def _callback(self, pin):
    pass

  def set_callback(self, callback, trigger=Pin.IRQ_FALLING):
    self.pin.irq(trigger=trigger, handler=callback)

  def press(self):
    return not self.pin.value()

class Beep:
  def __init__(self, pin=25):
    self.pin = PWM(Pin(pin))
    self.pin.duty(0)

  def tone(self, freq=1800, timeout=200):
    self.pin.freq(freq)
    self.pin.duty(512)
    time.sleep_ms(timeout)
    self.pin.duty(0)
    

M5Stack()

BtnA = Button(_BUTTON_A_PIN)
BtnB = Button(_BUTTON_B_PIN)
BtnC = Button(_BUTTON_C_PIN)

beep = Beep()