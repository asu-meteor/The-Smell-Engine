from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ctypes
import numpy
from datetime import datetime

from nidaqmx._lib import lib_importer, ctypes_byte_str
from nidaqmx.errors import check_for_error
from nidaqmx._task_modules.channels.do_channel import DOChannel
from nidaqmx._task_modules.channel_collection import ChannelCollection
from nidaqmx.utils import unflatten_channel_string
from nidaqmx.constants import (
    LineGrouping, ChannelType)


class DOChannelCollection(ChannelCollection):

    @property
    def debug_mode(self):
        return self.__debug_mode

    @debug_mode.setter
    def debug_mode(self, x):
        self.__debug_mode=x

    @property
    def channel_type(self):
        return self.__channel_type

    @channel_type.setter
    def channel_type(self, x):
        self.__channel_type = x

    @property
    def num_channels(self):
        return self.__num_channels

    @num_channels.setter
    def num_channels(self, x):
        self.__num_channels=x

    """
    Contains the collection of digital output channels for a DAQmx Task.
    """
    def __init__(self, task_handle, debug_mode=False, chann_type = False):
        self.debug_mode = debug_mode
        if not debug_mode:
            super(DOChannelCollection, self).__init__(task_handle)
        else:
            super(DOChannelCollection, self).__init__(0, self.debug_mode)
            self.channel_type = chann_type
            self.num_channels = 0
            # print("Digital Out Collection chann type:\t" + str(self.channel_type))


    def _create_chan(self, lines, line_grouping, name_to_assign_to_lines=''):
        """
        Creates and returns a DOChannel object.

        Args:
            lines (str): Specifies the names of the lines to use to 
                create virtual channels.
            line_grouping (Optional[nidaqmx.constants.LineGrouping]):
                Specifies how to group digital lines into one or more
                virtual channels.
            name_to_assign_to_lines (Optional[str]): Specifies a name to 
                assign to the virtual channel this method creates.
        Returns:
            nidaqmx._task_modules.channels.do_channel.DOChannel: 
            
            Specifies the newly created DOChannel object.
        """
        if not self.debug_mode:
            unflattened_lines = unflatten_channel_string(lines)
            num_lines = len(unflattened_lines)
            
            if line_grouping == LineGrouping.CHAN_FOR_ALL_LINES:
                if name_to_assign_to_lines or num_lines == 1:
                    name = lines
                else:
                    name = unflattened_lines[0] + '...'
            else:
                if name_to_assign_to_lines:
                    if num_lines > 1:
                        name = '{0}0:{1}'.format(
                            name_to_assign_to_lines, num_lines-1)
                    else:
                        name = name_to_assign_to_lines
                else:
                    name = lines

            return DOChannel(self._handle, name)
        else:
            # print("do_chann_coll - Assigned name to channel lines")
            name = name_to_assign_to_lines
            self.num_channels = self.num_channels + 1
            return DOChannel(self._handle, name, self.debug_mode, ChannelType.DIGITAL_OUTPUT)

    def add_do_chan(
            self, lines, name_to_assign_to_lines="",
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES):
        """
        Creates channel(s) to generate digital signals. You can group
        digital lines into one digital channel or separate them into
        multiple digital channels. If you specify one or more entire
        ports in **lines** input by using port physical channel names,
        you cannot separate the ports into multiple channels. To
        separate ports into multiple channels, use this function
        multiple times with a different port each time.

        Args:
            lines (str): Specifies the names of the digital lines or
                ports to use to create virtual channels. The DAQmx
                physical channel constant lists all lines and ports for
                devices installed in the system.
            name_to_assign_to_lines (Optional[str]): Specifies a name to
                assign to the virtual channel this function creates. If
                you do not specify a value for this input, NI-DAQmx uses
                the physical channel name as the virtual channel name.
            line_grouping (Optional[nidaqmx.constants.LineGrouping]): 
                Specifies how to group digital lines into one or more
                virtual channels. If you specify one or more entire
                ports with the **lines** input, you must set this input
                to **one channel for all lines**.
        Returns:
            nidaqmx._task_modules.channels.do_channel.DOChannel:
            
            Indicates the newly created channel object.
        """
        if not self.debug_mode:
            cfunc = lib_importer.windll.DAQmxCreateDOChan
            if cfunc.argtypes is None:
                with cfunc.arglock:
                    if cfunc.argtypes is None:
                        cfunc.argtypes = [
                            lib_importer.task_handle, ctypes_byte_str,
                            ctypes_byte_str, ctypes.c_int]

            error_code = cfunc(
                self._handle, lines, name_to_assign_to_lines, line_grouping.value)
            check_for_error(error_code)

            return self._create_chan(lines, line_grouping, name_to_assign_to_lines)
        else:
            if not lines or not name_to_assign_to_lines:
                # print('do_channel_collection.add_do_chan() - DaqWarning caught: User did not define communication lines' + "\n" + \
                #     str(datetime.now()))
                return -1
            else:
                # print("do_channel_collection - Successfully added DO channel.")
                return self._create_chan(lines, line_grouping, name_to_assign_to_lines)
                # return 0    # Success message

