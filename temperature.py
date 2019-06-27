from __future__ import absolute_import, division, print_function

from builtins import *  # @UnusedWildImport
from mcculw import ul
from mcculw.enums import TempScale
from mcculw.ul import ULError

import util
from ai import AnalogInputProps



class TLogger():
    def __init__(self,use_device_detection = True):
        self.use_device_detection=use_device_detection
        self.board_num = 0
        # board initially uninitalized
        self.Init=False
        if use_device_detection:
            ul.ignore_instacal()
            if not util.config_first_detected_device(self.board_num):
                print("Could not find device.")
                return False
        self.channel = 0
        ai_props = AnalogInputProps(self.board_num)
        if ai_props.num_ti_chans < 1:
            util.print_unsupported_example(self.board_num)
            return False
        #if we made it this far, we gucci
        self.isInit = True
        return True
    def getTemp(self):
        if not self.isInit:
            print("Device Not Initialized")
            return 0
        try:
            # Get the value from the device (optional parameters omitted)
            value = ul.t_in(self.board_num, self.channel, TempScale.CELSIUS)

            # Display the value
            print("Channel " + str(self.channel) + " Value (deg C): " + str(value))
            return value
        except ULError as e:
            util.print_ul_error(e)
            return 0
    #destructor, gets called on deletion of instance of TLogger
    def __del__(self):
        #release resources
        if self.use_device_detection:
            ul.release_daq_device(self.board_num)
