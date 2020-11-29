# The MIT License (MIT)

# Copyright (c) 2015 Pat Pannuto

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.


from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import (bytes, dict, int, list, object, range, str, ascii, chr,
        hex, input, next, oct, open, pow, round, super, filter, map, zip)


import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

import bisect
import contextlib
import enum
import inspect
import ipaddress
import os
import platform
import psutil
import shutil
import socket
import sys
import time
import warnings


class Device():
    class SaleaeError(Exception):
        pass

    class CommandNAKedError(SaleaeError):
        pass

    class ImpossibleSettings(SaleaeError):
        pass


    @staticmethod
    def launch_logic(quiet=False, logic_path=None):
        '''Attempts to open Saleae Logic software

        Caller should just invoke this and then attempt to connect separately with
        their own timeout logic

        :param quiet: Silence terminal output from Logic (Linux only, otherwise ignored)
        :param logic_path:
            Full path to Logic executable. If not provided, attempt to find Logic
            at a standard location.
        '''
        if logic_path is not None:
            p = logic_path
        else:
            p = os.path.join("C:", os.sep, "Program Files", "Saleae Inc", "Logic.exe")
            if not os.path.exists(p):
                p = os.path.join("C:", os.sep, "Program Files", "Saleae LLC", "Logic.exe")
        try:
            os.startfile(p)
        except Exception as e:
            print(f'Unable to start {p}: {repr(e)}')

    @staticmethod
    def _list_logic_candidates():
        '''Convenience method to list Saleae Logic processes'''
        # This is a bit experimental as I'm not sure what the process name will
        # be on every platform. For now, I'm making the hopefully reasonable and
        # conservative assumption that if there's only one process running with
        # 'logic' in the name, that it's Saleae Logic.
        candidates = []
        for proc in psutil.process_iter():
            try:
                if 'logic' in proc.name().lower():
                    candidates.append(proc)
            except psutil.NoSuchProcess:
                pass
        return candidates

    @staticmethod
    def kill_logic(kill_all=False):
        '''Attempts to find and kill running Saleae Logic software

        :param kill_all: If there are multiple potential Logic processes, kill them all
        :raises OSError: rasied if there is no running Logic process found
        '''
        candidates = Saleae._list_logic_candidates()
        if len(candidates) == 0:
            raise OSError("No logic process found")
        if len(candidates) > 1 and not kill_all:
            raise NotImplementedError("Multiple candidates for logic software."
                    " Not sure which to kill: " + str(candidates))
        for candidate in candidates:
            candidate.terminate()

    @staticmethod
    def is_logic_running():
        '''Return whether or not a Logic instance is running.'''
        # Relies on _list_logic_candidates() to identify Logic software.
        return bool(Saleae._list_logic_candidates())

    def _set_triggers_for_all_channels(self, channels):
        self._build('SET_TRIGGER')
        for c in channels:
            # Try coercing b/c it will throw a nice exception if it fails
            c = self.Trigger(c)
            if c == self.Trigger.NoTrigger:
                self._build('')
            elif c == self.Trigger.High:
                self._build('high')
            elif c == self.Trigger.Low:
                self._build('low')
            elif c == self.Trigger.Posedge:
                self._build('posedge')
            elif c == self.Trigger.Negedge:
                self._build('negedge')
            else:
                raise NotImplementedError("Must pass trigger type")
        self._finish()

    def __init__(self, vid, pid, sn = None, ipaddr = 'localhost:10429', visabackend = None):
        quiet = False
        self.id = None
        self._to_send = []
        self.sample_rates = None
        self.connected_devices = None
        self._rxbuf = ''
        self._touched = False

        defaulthost = 'localhost'
        defaultport = 10429
        if isinstance(ipaddr,str):
            iplist = ipaddr.split(':')
            host = iplist[0]
            if 'localhost' not in host:
                try:
                    ipaddress.ip_address(host)
                except:
                    log.warning(f'{host} is invalid: using default host of {defaulthost}')
                    host  = defaulthost
            try:
                port = int(iplist[1])
            except:
                log.warning(f'{port} is invalid: Using default port of {defaultport}')
                port = defaultport
        else:
            host = 'localhost'
            port = defaultport
            log.warning(f'{ipaddr} is invalid: Using default host:port of {host}:{port}')

        connected = False
        exception = Exception
        try:
            self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._s.connect((host, port))
            connected = True
        except Exception as e:
            exception = e
            log.info("Could not connect to Logic software, attempting to launch it now...")
            Device.launch_logic(quiet=quiet)

        starttime = time.time()
        while (not connected) and (time.time() - starttime < 10.0):
            try:
                self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._s.connect((host, port))
                connected = True
            except Exception as e:
                exception = e

        if not connected:
            raise ConnectionError(f'Bad Saleae Backend: {host}:{port}: Did You "ENABLE SCRIPTING SOCKET SERVER"? {repr(exception)}')

        log.info("Connected.")

    def _build(self, s):
        '''Convenience method for building up a command to send'''
        if isinstance(s, list):
            self._to_send.extend(s)
        else:
            self._to_send.append(s)

    def _abort(self):
        self._to_send = []

    def _finish(self, s=None):
        if s:
            self._build(s)
        try:
            ret = self._cmd(', '.join(self._to_send))
        finally:
            self._to_send = []
        return ret

    def _round_up_or_max(self, value, candidates):
        i = bisect.bisect_left(candidates, value)
        if i == len(candidates):
            i -= 1
        return candidates[i]

    @property
    def touched(self):
        return self._touched

    def _send(self, s):
        self._touched = True
        log.debug("Send >{}<".format(s))
        self._s.send(bytes(s + '\0', 'UTF-8'))

    def _recv(self, expect_nak=False):
        self._touched = True
        while 'ACK' not in self._rxbuf:
            self._rxbuf += self._s.recv(1024).decode('UTF-8')
            log.debug("Recv >{}<".format(self._rxbuf))
            if 'NAK' == self._rxbuf[0:3]:
                self._rxbuf = self._rxbuf[3:]
                if expect_nak:
                    return None
                else:
                    raise self.CommandNAKedError
        ret, self._rxbuf = self._rxbuf.split('ACK', 1)
        return ret

    def _cmd(self, s, wait_for_ack=True, expect_nak=False):
        self._send(s)

        ret = None
        if wait_for_ack:
            ret = self._recv(expect_nak=expect_nak)
        return ret

    # NOTE: the [EACH_SAMPLE|ON_CHANGE] is the same as the CSV [ROW_PER_CHANGE|ROW_PER_SAMPLE], but I am using name convention from official C# API
    def _export_data2_digital_binary(self, each_sample=True, no_shift=True, word_size=16):
        '''Binary digital: [EACH_SAMPLE|ON_CHANGE], [NO_SHIFT|RIGHT_SHIFT], [8|16|32|64]'''
        # Do argument verification
        if word_size not in [8, 16, 32, 64]:
            raise self.ImpossibleSettings('Unsupported binary word size')

        # Build arguments
        self._build('EACH_SAMPLE' if each_sample else 'ON_CHANGE')
        self._build('NO_SHIFT' if no_shift else 'RIGHT_SHIFT')
        self._build(str(word_size))

    def _export_data2_analog_csv(self, column_headers=True, delimiter='comma', display_base='hex', analog_format='voltage'):
        '''CVS export analog/mixed: [HEADERS|NO_HEADERS], [COMMA|TAB], [BIN|DEC|HEX|ASCII], [VOLTAGE|ADC]'''

        # Do argument verification
        if delimiter.lower() not in ['comma', 'tab']:
            raise self.ImpossibleSettings('Unsupported CSV delimiter')
        if display_base.lower() not in ['bin', 'dec', 'hex', 'ascii']:
            raise self.ImpossibleSettings('Unsupported CSV display base')
        if analog_format.lower() not in ['voltage', 'adc']:
            raise self.ImpossibleSettings('Unsupported CSV analog format')

        # Build arguments
        self._build('HEADERS' if column_headers else 'NO_HEADERS')
        self._build(delimiter.upper())
        self._build(display_base.upper())
        self._build(analog_format.upper())

    def _export_data2_digital_csv(self, column_headers=True, delimiter='comma', timestamp='time_stamp', display_base='hex', rows_per_change=True):
        '''CVS export digital: [HEADERS|NO_HEADERS], [COMMA|TAB], [TIME_STAMP|SAMPLE_NUMBER], [COMBINED, [BIN|DEC|HEX|ASCII]|SEPARATE], [ROW_PER_CHANGE|ROW_PER_SAMPLE]'''

        # Do argument verification
        if delimiter.lower() not in ['comma', 'tab']:
            raise self.ImpossibleSettings('Unsupported CSV delimiter')
        if timestamp.lower() not in ['time_stamp', 'sample_number']:
            raise self.ImpossibleSettings('Unsupported timestamp setting')
        if display_base.lower() not in ['bin', 'dec', 'hex', 'ascii', 'separate']:
            raise self.ImpossibleSettings('Unsupported CSV display base')

        # Build arguments
        self._build('HEADERS' if column_headers else 'NO_HEADERS')
        self._build(delimiter.upper())
        self._build(timestamp.upper())
        self._build('SEPARATE' if display_base.upper() == 'SEPARATE' else ['COMBINED', display_base.upper()])
        self._build('ROW_PER_CHANGE' if rows_per_change else 'ROW_PER_SAMPLE')

    def _export_data2_digital_vcd(self):
        '''VCD digital: no arguments'''
        pass

    def _export_data2_analog_matlab(self, analog_format='voltage'):
        '''Matlab analog: [VOLTAGE|ADC]'''

        # Do argument verification
        if analog_format.lower() not in ['voltage', 'adc']:
            raise self.ImpossibleSettings('Unsupported Matlab analog format')

        # Build arguments
        self._build(analog_format.upper())

    def _export_data2_digital_matlab(self):
        '''Matlab digital: no arguments'''
        pass
