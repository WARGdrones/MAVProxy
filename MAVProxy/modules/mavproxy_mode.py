#!/usr/bin/env python
'''mode command handling'''

import time, os
from pymavlink import mavutil

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util

class ModeModule(mp_module.MPModule):
    def __init__(self, mpstate):
        super(ModeModule, self).__init__(mpstate, "mode", public=True)
        self.add_command('mode', self.cmd_mode, "mode change", self.available_modes())
        self.add_command('guided', self.cmd_guided, "fly to a clicked location on map")
        self.add_command('confirm', self.cmd_confirm, "confirm a command")

    def cmd_mode(self, args):
        '''set arbitrary mode'''
        mode_mapping = self.master.mode_mapping()
        if mode_mapping is None:
            print('No mode mapping available')
            return
        if len(args) != 1:
            print('Available modes: ', mode_mapping.keys())
            return
        if args[0].isdigit():
            modenum = int(args[0])
        else:
            mode = args[0].upper()
            if mode not in mode_mapping:
                print('Unknown mode %s: ' % mode)
                return
            modenum = mode_mapping[mode]
        self.master.set_mode(modenum)

    def cmd_confirm(self, args):
        '''confirm a command'''
        if len(args) < 2:
            print('Usage: confirm "Question to display" command <arguments>')
            return
        question = args[0].strip('"')
        command = ' '.join(args[1:])
        if not mp_util.has_wxpython:
            print("No UI available for confirm")
            return
        from MAVProxy.modules.lib import mp_menu
        mp_menu.MPMenuConfirmDialog(question, callback=self.mpstate.functions.process_stdin, args=command)

    def available_modes(self):
        if self.master is None:
            print('No mode mapping available')
            return []
        mode_mapping = self.master.mode_mapping()
        if mode_mapping is None:
            print('No mode mapping available')
            return []
        return mode_mapping.keys()

    def unknown_command(self, args):
        '''handle mode switch by mode name as command'''
        mode_mapping = self.master.mode_mapping()
        mode = args[0].upper()
        if mode in mode_mapping:
            self.master.set_mode(mode_mapping[mode])
            return True
        return False

    def cmd_guided(self, args):
        '''set GUIDED target'''
        if len(args) != 1 and len(args) != 3:
            print("Usage: guided ALTITUDE | guided LAT LON ALTITUDE")
            return

        if len(args) == 3:
            latitude = float(args[0])
            longitude = float(args[1])
            altitude = float(args[2])
            latlon = (latitude, longitude)
        else:
            latlon = self.mpstate.click_location
            if latlon is None:
                print("No map click position available")
                return
            altitude = float(args[0])

        print("Guided %s %s" % (str(latlon), str(altitude)))
        self.master.mav.mission_item_int_send (self.settings.target_system,
                                           self.settings.target_component,
                                           0,
                                           self.module('wp').get_default_frame(),
                                           mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                                           2, 0, 0, 0, 0, 0,
                                           int(latlon[0]*1.0e7),
                                           int(latlon[1]*1.0e7),
                                           altitude)
                                           
    def mavlink_packet(self, m):
            mtype = m.get_type()
            if mtype == 'HIGH_LATENCY2':
                mode_map = mavutil.mode_mapping_bynumber(m.type)
                if mode_map and m.custom_mode in mode_map:
                    self.master.flightmode = mode_map[m.custom_mode]
            
            
def init(mpstate):
    '''initialise module'''
    return ModeModule(mpstate)
