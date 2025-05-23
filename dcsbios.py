from __future__ import print_function
from __future__ import unicode_literals
import sys

# Исправленная функция byte2int для Python 3.x
if sys.version_info[0] == 2:  # Python 2.x
    def byte2int(b):
        return ord(b)
else:  # Python 3.x
    def byte2int(b):
        return b  # Просто возвращаем int напрямую

import struct

class ProtocolParser:
    def __init__(self):
        self.__state = "WAIT_FOR_SYNC"
        self.__sync_byte_count = 0
        self.__address = 0
        self.__count = 0
        self.__data = 0
        self.write_callbacks = set()
        self.frame_sync_callbacks = set()
        
    def processByte(self, c):
        c = byte2int(c)
        if self.__state == "ADDRESS_LOW":
            self.__address = c
            self.__state = "ADDRESS_HIGH"
        elif self.__state == "ADDRESS_HIGH":
            self.__address += c * 256
            if self.__address != 0x5555:
                self.__state = "COUNT_LOW"
            else:
                self.__state = "WAIT_FOR_SYNC"
        elif self.__state == "COUNT_LOW":
            self.__count = c
            self.__state = "COUNT_HIGH"
        elif self.__state == "COUNT_HIGH":
            self.__count += 256 * c
            self.__state = "DATA_LOW"
        elif self.__state == "DATA_LOW":
            self.__data = c
            self.__count -= 1
            self.__state = "DATA_HIGH"
        elif self.__state == "DATA_HIGH":
            self.__data += 256 * c
            self.__count -= 1
            for callback in self.write_callbacks:
                callback(self.__address, self.__data)
            self.__address += 2
            if self.__count == 0:
                self.__state = "ADDRESS_LOW"
            else:
                self.__state = "DATA_LOW"
                
        if c == 0x55:
            self.__sync_byte_count += 1
        else:
            self.__sync_byte_count = 0
            
        if self.__sync_byte_count == 4:
            self.__state = "ADDRESS_LOW"
            self.__sync_byte_count = 0
            for callback in self.frame_sync_callbacks:
                callback()

class StringBuffer:
    def __init__(self, parser, address, length, callback):
        self.__address = address
        self.__length = length
        self.__dirty = False
        self.buffer = bytearray(length)
        self.callbacks = set()
        if callback:
            self.callbacks.add(callback)
        parser.write_callbacks.add(lambda address, data: self.on_dcsbios_write(address, data))
        
    def set_char(self, i, c):
        if self.buffer[i] != c:
            self.buffer[i] = c
            self.__dirty = True
            
    def on_dcsbios_write(self, address, data):
        if address >= self.__address and self.__address + self.__length > address:
            data_bytes = struct.pack("<H", data)
            self.set_char(address - self.__address, data_bytes[0])
            if self.__address + self.__length > (address + 1):
                self.set_char(address - self.__address + 1, data_bytes[1])
                
        if address == 0xfffe and self.__dirty:
            self.__dirty = False
            s = self.buffer.split(b"\x00")[0].decode("latin-1")
            for callback in self.callbacks:
                callback(s)

class IntegerBuffer:
    def __init__(self, parser, address, mask, shift_by, callback):
        self.__address = address
        self.__mask = mask
        self.__shift_by = shift_by
        self.__value = None
        self.callbacks = set()
        if callback:
            self.callbacks.add(callback)
        parser.write_callbacks.add(lambda address, data: self.on_dcsbios_write(address, data))
        
    def on_dcsbios_write(self, address, data):
        if address == self.__address:
            value = (data & self.__mask) >> self.__shift_by
            if self.__value != value:
                self.__value = value
                for callback in self.callbacks:
                    callback(value)