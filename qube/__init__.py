# Python module for control of Qube bluetooth LED bulbs
#
# Copyright 2017 Matthew Garrett <mjg59@srcf.ucam.org>
#
# This code is released under the terms of the MIT license. See the LICENSE
# file for more details.

import base64
import time

from bluepy import btle
from Crypto.Cipher import AES

def FNV1a_128(data):
    prime = 0x01000000000000000000013B
    offset = 0x6C62272E07BB014262B821756295C58D

    for char in data:
        offset = ((offset^(ord(char))) * prime) % (2 ** 128)

    return offset.to_bytes(16, byteorder="big")


class Delegate(btle.DefaultDelegate):
    def __init__(self, bulb):
      self.bulb = bulb
      btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        self.bulb.response_buf += str(data, "ascii")
        if self.bulb.response_buf.find("\r\n") != -1:
            response = self.bulb.response_buf.split(" ")
            if response[1] == "GetLED":
                state = base64.b64decode(response[3])
                self.bulb.power = bool(state[0] & 0x1)
                self.bulb.red = state[1]
                self.bulb.green = state[2]
                self.bulb.blue = state[3]
                self.bulb.white = state[4]
            self.bulb.response_buf = ""
            self.bulb.in_response = False

class qube:
    def __init__(self, mac, key):
        self.mac = mac
        self.key = FNV1a_128(key)
        self.count = 1
        self.response_buf = ""
        self.power = False
        self.red = 0
        self.green = 0
        self.blue = 0
        self.white = 0
        self.in_response = False

    def connect(self):
        retries = 3
        while retries > 0:
            try:
                self.device = btle.Peripheral(self.mac,
                                              addrType=btle.ADDR_TYPE_PUBLIC)
                retries = 0
            except:
                retries -= 1

        self.device.setDelegate(Delegate(self))

        handles = self.device.getCharacteristics()
        for handle in handles:
            if handle.uuid == "fff2":
                self.password = handle
            if handle.uuid == "fff3":
                self.commandhandle = handle
        password = self.password.read()

        if len(password) == 16:
            k = AES.new(self.key, AES.MODE_ECB)
            data = k.decrypt(password)
            self.password.write(data)        

            password = self.password.read()
            if len(password) == 16:
                print("Unable to connect")

        self.update_state()

    def wait_for_response(self):
        self.in_response = True
        while self.in_response == True:
            self.device.waitForNotifications(10)

    def send_command(self, command):
        for i in range(0, len(command), 20):
            retries = 3
            while retries > 0:
                try:
                    self.commandhandle.write(bytes(command[i:min(len(command),
                                                                 i+20)],
                                                   "ascii"))
                    retries = 0
                except:
                    retries -= 1
        self.wait_for_response()
        self.count += 1

    def get_state(self):
        self.update_state()
        return (self.red, self.green, self.blue, self.white)

    def update_state(self):
        command = "1.0 GetLED %d 1\r\n" % self.count
        self.send_command(command)

    def on(self):
        packet = bytearray(2)
        packet[0] = 0x01
        packet[1] = 0x01

        encoded = str(base64.b64encode(packet), "ascii")
        command = "1.0 SetLED %d 1 %s\r\n" % (self.count, encoded)
        self.send_command(command)

    def off(self):
        packet = bytearray(2)
        packet[0] = 0x01
        packet[1] = 0x00
        encoded = str(base64.b64encode(packet), "ascii")
        command = "1.0 SetLED %d 1 %s\r\n" % (self.count, encoded)
        self.send_command(command)

    def get_on(self):
        self.update_state()
        return self.power

    def set_rgbw(self, red, green, blue, white):
        packet = bytearray(10)
        packet[0] = 0x13
        packet[1] = 0x01
        packet[2] = red
        packet[3] = green
        packet[4] = blue
        packet[5] = white
        encoded = str(base64.b64encode(packet), "ascii")
        command = "1.0 SetLED %d 1 %s\r\n" % (self.count, encoded)
        self.send_command(command)
